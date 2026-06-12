"""modules.insights

Generate automated insights from analysis results. The main class
`InsightEngine` orchestrates data cleaning, EDA and optional SQL summary
generation and returns programmatic insights for backend consumption.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .data_cleaner import DataCleaner
from .eda import EDAEngine
from .sql_engine import create_sql_engine


class InsightEngine:
    def __init__(self) -> None:
        self.cleaner = DataCleaner()
        self.eda = EDAEngine()

    def _detect_trends(self, df: pd.DataFrame) -> List[str]:
        """Detect simple trends using the first datetime column if present.

        Returns a list of human-readable trend descriptions.
        """
        trends: List[str] = []
        datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        # try to coerce object columns to datetime if none typed
        if not datetime_cols:
            for c in df.select_dtypes(include=[object, 'string']).columns:
                try:
                    coerced = pd.to_datetime(df[c], errors='coerce')
                    if coerced.notna().sum() > 0:
                        datetime_cols.append(c)
                        df[c] = coerced
                        break
                except Exception:
                    continue

        if not datetime_cols:
            return trends

        dt_col = datetime_cols[0]
        tmp = df.dropna(subset=[dt_col])
        if tmp.empty:
            return trends

        tmp = tmp.set_index(pd.to_datetime(tmp[dt_col]))
        numeric = tmp.select_dtypes(include=[np.number])
        for col in numeric.columns:
            series = numeric[col].resample('M').mean().dropna()
            if len(series) < 3:
                continue
            # simple slope via polyfit of values against time index
            x = np.arange(len(series))
            y = series.values
            slope = np.polyfit(x, y, 1)[0]
            if abs(slope) < 1e-8:
                continue
            direction = 'increasing' if slope > 0 else 'decreasing'
            trends.append(f"{col} has a {direction} trend over time (monthly slope={slope:.4f})")

        return trends

    def _correlation_findings(self, df: pd.DataFrame, threshold: float = 0.7) -> List[str]:
        findings: List[str] = []
        corr = self.eda.correlation_matrix(df)
        if corr.empty:
            return findings
        cols = corr.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if pd.isna(val):
                    continue
                if abs(val) >= threshold:
                    findings.append(f"Strong correlation: {cols[i]} <-> {cols[j]} = {val:.2f}")
        return findings

    def _data_quality_observations(self, df: pd.DataFrame) -> List[str]:
        obs: List[str] = []
        report = self.cleaner.generate_report(df)
        score = report.get('data_quality_score', None)
        if score is not None:
            if score < 50:
                obs.append(f"Low data quality score: {score} — requires cleaning and validation")
            elif score < 80:
                obs.append(f"Moderate data quality score: {score} — consider targeted cleaning")
            else:
                obs.append(f"Good data quality score: {score}")

        if report.get('duplicate_rows', 0) > 0:
            obs.append(f"{report['duplicate_rows']} duplicate rows detected")

        # high missing columns
        high_missing = [c for c in report['missing_by_column'] if c['missing_percentage'] > 20]
        for c in high_missing:
            obs.append(f"Column {c['column']} has high missing rate: {c['missing_percentage']}%")

        return obs

    def _business_recommendations(self, df: pd.DataFrame, findings: Dict) -> List[str]:
        recs: List[str] = []
        # Recommendations based on quality
        dq = findings.get('data_quality', {})
        score = dq.get('data_quality_score')
        if score is not None and score < 80:
            recs.append("Impute or remove missing values for critical columns; add validation at ingestion.")
        if dq.get('duplicate_rows', 0) > 0:
            recs.append("Deduplicate dataset and add unique constraints where applicable.")

        # Recommendations based on correlations
        correlations = findings.get('correlations', [])
        if correlations:
            recs.append("Investigate strongly correlated features for multicollinearity before modeling; consider feature selection or dimensionality reduction.")

        # Distribution / skew
        dist = findings.get('distribution', [])
        if dist:
            recs.append("Address highly skewed distributions with transformations or robust models.")

        # Trends
        trends = findings.get('trends', [])
        if trends:
            recs.append("Validate seasonality and trends; consider time-based features for forecasting or segmentation.")

        if not recs:
            recs.append("Data looks healthy; continue with modeling and monitoring.")

        return recs

    def run_full_analysis(self, df: pd.DataFrame, persist_sql: bool = False, db_path: str = ':memory:') -> Dict:
        """Run cleaning, EDA, optional SQL persistence, and produce insights.

        Returns a dictionary with keys: data_quality, eda_summary, correlations,
        trends, distribution, key_findings, recommendations, sql_summary (optional).
        """
        results: Dict = {}

        # Data quality
        data_quality = self.cleaner.generate_report(df)
        results['data_quality'] = data_quality

        # EDA summaries
        eda_summary = self.eda.generate_summary(df)
        results['eda_summary'] = eda_summary

        # Correlations
        correlations = self._correlation_findings(df)
        results['correlations'] = correlations

        # Distribution insights
        numeric = df.select_dtypes(include=[np.number])
        distribution = []
        for col in numeric.columns:
            skew = float(numeric[col].skew()) if numeric[col].count() > 2 else 0.0
            if abs(skew) > 1:
                distribution.append(f"{col}: highly skewed (skew={skew:.2f})")
            elif abs(skew) > 0.5:
                distribution.append(f"{col}: moderately skewed (skew={skew:.2f})")
        results['distribution'] = distribution

        # Trends
        trends = self._detect_trends(df)
        results['trends'] = trends

        # Key findings: combine top items
        key_findings: List[str] = []
        # Missing and duplicates
        if data_quality.get('overall_null_percentage', 0) > 0:
            key_findings.append(f"Dataset contains {data_quality['overall_null_percentage']}% missing values")
        if data_quality.get('duplicate_rows', 0) > 0:
            key_findings.append(f"{data_quality['duplicate_rows']} duplicate rows present")
        key_findings.extend(correlations[:5])
        key_findings.extend(distribution[:5])
        key_findings.extend(trends[:5])
        results['key_findings'] = key_findings

        # Business recommendations
        findings_bundle = {
            'data_quality': data_quality,
            'correlations': correlations,
            'distribution': distribution,
            'trends': trends,
        }
        results['recommendations'] = self._business_recommendations(df, findings_bundle)

        # Optional SQL persistence and summary
        if persist_sql:
            engine = create_sql_engine(df=df, table_name='data', db_path=db_path)
            try:
                sql_summary = engine.generate_dataset_summary()
                results['sql_summary'] = sql_summary.to_dict(orient='records')
            finally:
                engine.close()

        return results


def auto_inspect(df: pd.DataFrame, persist_sql: bool = False, db_path: str = ':memory:') -> Dict:
    """Convenience function: run analysis and return insights. Intended to be
    called automatically by a backend after a DataFrame is uploaded/loaded.
    """
    engine = InsightEngine()
    return engine.run_full_analysis(df, persist_sql=persist_sql, db_path=db_path)


# Backwards-compatible procedural helpers used by app.py
def generate_basic_insights(df: pd.DataFrame) -> Dict:
    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "memory_usage_mb": round(float(df.memory_usage(deep=True).sum() / 1024**2), 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing": int(df.isnull().sum().sum()),
    }


def get_column_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Column": df.columns,
            "Non-Null Count": df.count().values,
            "Null Count": df.isnull().sum().values,
            "Null %": (df.isnull().sum().values / max(len(df), 1) * 100).round(2),
            "Unique Values": df.nunique(dropna=True).values,
            "Data Type": df.dtypes.astype(str).values,
        }
    )


def get_top_insights(df: pd.DataFrame) -> List[str]:
    result = auto_inspect(df)
    top = []
    top.extend(result.get("key_findings", []))
    if not top:
        top.append("No major issues detected")
    return top


def get_correlation_insights(df: pd.DataFrame) -> List[str]:
    engine = InsightEngine()
    findings = engine._correlation_findings(df)
    return findings if findings else ["No strong correlations found (threshold: 0.7)"]


def get_distribution_insights(df: pd.DataFrame) -> List[str]:
    result = auto_inspect(df)
    distribution = result.get("distribution", [])
    return distribution if distribution else ["No significant skewness detected"]


def get_statistical_summary(df: pd.DataFrame) -> Dict:
    numeric_df = df.select_dtypes(include=[np.number])
    return {
        "numeric_columns": int(len(numeric_df.columns)),
        "rows": int(len(df)),
        "mean": numeric_df.mean().to_dict() if len(numeric_df.columns) > 0 else {},
        "std_dev": numeric_df.std().to_dict() if len(numeric_df.columns) > 0 else {},
    }
 