"""modules.data_cleaner
Production-ready data cleaning utilities.

Provides a `DataCleaner` class with methods for missing value reports,
duplicate detection, null percentage, a simple data quality score and a
JSON-serializable `generate_report` used by the insights pipeline.
"""

from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd


class DataCleaner:
    """Helper for data quality and cleaning diagnostics."""

    def __init__(self) -> None:
        pass

    def missing_values_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return per-column missing counts, percentages, dtypes and uniques.

        The returned DataFrame is indexed by column name and is suitable for
        conversion to JSON via `reset_index().to_dict(orient='records')`.
        """
        total = len(df)
        if total == 0:
            # return empty frame with expected columns
            return pd.DataFrame(columns=["dtype", "missing_count", "missing_percentage", "unique_values"]).astype(object)

        missing = df.isnull().sum()
        pct = (missing / total * 100).round(4)
        uniques = df.nunique(dropna=True)
        dtypes = df.dtypes.astype(str)

        report = pd.DataFrame(
            {
                "dtype": dtypes.values,
                "missing_count": missing.values.astype(int),
                "missing_percentage": pct.values.astype(float),
                "unique_values": uniques.values.astype(int),
            },
            index=df.columns,
        )

        return report

    def duplicate_rows_count(self, df: pd.DataFrame) -> int:
        """Return number of exact duplicate rows as int."""
        if df is None or df.shape[0] == 0:
            return 0
        return int(df.duplicated().sum())

    def null_percentage(self, df: pd.DataFrame) -> float:
        """Return overall null percentage across all cells (0-100).

        Returns 0.0 for empty DataFrames.
        """
        if df is None:
            return 0.0
        rows, cols = df.shape
        if rows == 0 or cols == 0:
            return 0.0
        total_cells = rows * cols
        nulls = int(df.isnull().sum().sum())
        return round(nulls / total_cells * 100, 4)

    def data_quality_score(self, df: pd.DataFrame) -> float:
        """Compute a deterministic data quality score between 0 and 100.

        Formula:
            score = 100 * (1 - missing_fraction) * (1 - duplicate_fraction)

        Returns 0.0 for empty DataFrames.
        """
        if df is None:
            return 0.0
        rows, cols = df.shape
        if rows == 0 or cols == 0:
            return 0.0

        total_cells = rows * cols
        null_cells = int(df.isnull().sum().sum())
        missing_frac = null_cells / total_cells

        dup_rows = int(df.duplicated().sum())
        dup_frac = dup_rows / rows

        score = 100.0 * max(0.0, 1.0 - missing_frac) * max(0.0, 1.0 - dup_frac)
        return round(float(score), 2)

    def generate_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return a JSON-serializable report with data quality metrics.

        Keys:
            rows, columns, duplicate_rows, overall_null_percentage,
            data_quality_score, missing_by_column (list of dicts)
        """
        if df is None:
            return {
                "rows": 0,
                "columns": 0,
                "duplicate_rows": 0,
                "overall_null_percentage": 0.0,
                "data_quality_score": 0.0,
                "missing_by_column": [],
            }

        missing_df = self.missing_values_report(df)
        dup_count = self.duplicate_rows_count(df)
        overall_null_pct = self.null_percentage(df)
        quality_score = self.data_quality_score(df)

        report = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "duplicate_rows": int(dup_count),
            "overall_null_percentage": float(overall_null_pct),
            "data_quality_score": float(quality_score),
            "missing_by_column": missing_df.reset_index().rename(columns={"index": "column"}).to_dict(orient="records"),
        }

        return report

    def handle_missing_values(self, df: pd.DataFrame, strategy: str = "drop", fill_value: Optional[Any] = None) -> pd.DataFrame:
        """Handle missing values using a strategy.

        Strategies:
            - 'drop': drop rows with any nulls
            - 'fill': fill numeric columns with mean and categorical with mode
            - 'fill_with_value': fill all nulls with `fill_value`

        Returns a new DataFrame.
        """
        if df is None:
            return df
        df_copy = df.copy()

        if strategy == "drop":
            return df_copy.dropna()

        if strategy == "fill_with_value":
            return df_copy.fillna(fill_value)

        if strategy == "fill":
            # Fill numeric with mean, categorical with mode
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
            cat_cols = df_copy.select_dtypes(include=["object", "category"]).columns

            for c in numeric_cols:
                if df_copy[c].isnull().any():
                    mean_val = df_copy[c].mean()
                    df_copy[c] = df_copy[c].fillna(mean_val)

            for c in cat_cols:
                if df_copy[c].isnull().any():
                    modes = df_copy[c].mode()
                    fill = modes.iloc[0] if not modes.empty else None
                    df_copy[c] = df_copy[c].fillna(fill)

            return df_copy

        raise ValueError(f"Unknown strategy: {strategy}")

    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Return dataframe with duplicates removed; optional subset columns."""
        if df is None:
            return df
        return df.drop_duplicates(subset=subset)


# Backwards-compatible procedural helpers
def generate_report(df: pd.DataFrame) -> Dict[str, Any]:
    return DataCleaner().generate_report(df)

def handle_missing_values(df: pd.DataFrame, strategy: str = 'drop', fill_value: Optional[Any] = None) -> pd.DataFrame:
    return DataCleaner().handle_missing_values(df, strategy=strategy, fill_value=fill_value)

def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    return DataCleaner().remove_duplicates(df, subset=subset)

def duplicate_rows_count(df: pd.DataFrame) -> int:
    return DataCleaner().duplicate_rows_count(df)


def get_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Backwards-compatible helper returning column dtypes."""
    if df is None:
        return pd.DataFrame(columns=["Column", "Data Type"])
    return pd.DataFrame({"Column": df.columns, "Data Type": df.dtypes.values})


def get_basic_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Backwards-compatible helper returning numeric summary stats."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.describe(include=[np.number])


def get_missing_values_info(df: pd.DataFrame) -> pd.DataFrame:
    """Backwards-compatible missing-values report with legacy column names."""
    if df is None:
        return pd.DataFrame(columns=["Column", "Missing Count", "Missing Percentage"])

    cleaner = DataCleaner()
    report = cleaner.missing_values_report(df)
    if report.empty:
        return pd.DataFrame(columns=["Column", "Missing Count", "Missing Percentage"])

    legacy = report.reset_index().rename(
        columns={
            "index": "Column",
            "missing_count": "Missing Count",
            "missing_percentage": "Missing Percentage",
        }
    )
    # Match old behavior: only columns with at least one missing value.
    legacy = legacy[legacy["Missing Count"] > 0]
    return legacy[["Column", "Missing Count", "Missing Percentage"]]


def get_duplicate_rows_count(df: pd.DataFrame) -> int:
    """Backwards-compatible duplicate count function expected by app.py."""
    return duplicate_rows_count(df)

