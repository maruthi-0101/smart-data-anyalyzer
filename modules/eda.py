"""modules.eda

Exploratory Data Analysis utilities. Exposes an `EDAEngine` class that
produces numerical and categorical summaries, correlation matrices and
per-column statistics.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class EDAEngine:
    """Perform EDA operations on a DataFrame.

    The methods return plain Python structures and pandas objects that are
    easy to serialize for a backend API.
    """

    def __init__(self) -> None:
        pass

    def numerical_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame with mean, median, mode, std, min, max, q1, q3
        and missing/counts for each numeric column.
        """
        num = df.select_dtypes(include=[np.number])
        if num.shape[1] == 0:
            return pd.DataFrame()

        summary = pd.DataFrame(index=num.columns)
        summary["count"] = num.count()
        summary["missing"] = num.isnull().sum()
        summary["mean"] = num.mean()
        summary["median"] = num.median()
        # mode may return multiple values; convert to string representation
        summary["mode"] = num.mode().apply(lambda row: ", ".join(map(str, row.dropna().unique()[:3])), axis=0)
        summary["std"] = num.std()
        summary["min"] = num.min()
        summary["max"] = num.max()
        summary["q1"] = num.quantile(0.25)
        summary["q3"] = num.quantile(0.75)
        summary = summary.fillna(0)
        return summary.reset_index().rename(columns={"index": "column"})

    def categorical_summary(self, df: pd.DataFrame, top_n: int = 10) -> Dict[str, pd.DataFrame]:
        """Return a mapping of categorical column -> value counts (top N).

        Also provide unique counts and missing counts per categorical column.
        """
        cat = df.select_dtypes(include=["object", "category"]).columns.tolist()
        result: Dict[str, pd.DataFrame] = {}
        for col in cat:
            vc = df[col].value_counts(dropna=False).head(top_n)
            meta = {
                "column": col,
                "unique": int(df[col].nunique(dropna=True)),
                "missing": int(df[col].isnull().sum()),
                "top_values": vc.to_dict(),
            }
            result[col] = pd.DataFrame([meta])
        return result

    def correlation_matrix(self, df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
        """Return correlation matrix for numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] == 0:
            return pd.DataFrame()
        return numeric_df.corr(method=method)

    def column_statistics(self, df: pd.DataFrame, column: str) -> Optional[Dict]:
        """Return detailed statistics for a single column (numeric or categorical)."""
        if column not in df.columns:
            return None

        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            modes = series.mode()
            mode_val = modes.tolist() if not modes.empty else []
            return {
                "column": column,
                "dtype": str(series.dtype),
                "count": int(series.count()),
                "missing": int(series.isnull().sum()),
                "mean": float(series.mean()) if series.count() > 0 else None,
                "median": float(series.median()) if series.count() > 0 else None,
                "mode": mode_val,
                "std": float(series.std()) if series.count() > 0 else None,
                "min": float(series.min()) if series.count() > 0 else None,
                "max": float(series.max()) if series.count() > 0 else None,
                "q1": float(series.quantile(0.25)) if series.count() > 0 else None,
                "q3": float(series.quantile(0.75)) if series.count() > 0 else None,
            }
        else:
            top = series.value_counts(dropna=False).head(10).to_dict()
            return {
                "column": column,
                "dtype": str(series.dtype),
                "count": int(series.count()),
                "missing": int(series.isnull().sum()),
                "unique": int(series.nunique(dropna=True)),
                "top_values": top,
            }

    def generate_summary(self, df: pd.DataFrame) -> Dict:
        """Return a combined summary with numerical and categorical summaries."""
        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "numerical_summary": self.numerical_summary(df).to_dict(orient="records"),
            "categorical_summary": {k: v.to_dict(orient="records") for k, v in self.categorical_summary(df).items()},
            "correlation_matrix": self.correlation_matrix(df).to_dict(),
        }


# Backwards-compatible procedural helpers used by app.py
def get_data_info(df: pd.DataFrame) -> Dict:
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "memory_usage": float(df.memory_usage(deep=True).sum() / 1024**2),
    }


def get_numerical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def get_column_statistics(df: pd.DataFrame, column: str) -> Dict:
    stats = EDAEngine().column_statistics(df, column)
    return stats if stats is not None else {}


def get_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return EDAEngine().correlation_matrix(df)


def get_value_counts(df: pd.DataFrame, column: str, top: int = 10) -> pd.Series:
    if column in df.columns:
        return df[column].value_counts(dropna=False).head(top)
    return pd.Series(dtype="object")
