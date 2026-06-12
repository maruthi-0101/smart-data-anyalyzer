"""modules.sql_engine

Lightweight SQLite engine to persist pandas DataFrames and run SQL
queries against them. Designed for backend use.
"""

from typing import List, Optional

import pandas as pd
import sqlite3


class DataFrameSQLEngine:
    """SQL Engine for DataFrame operations using SQLite.

    The engine can use an in-memory database or persist to a file via
    `db_path`. Tables are created from pandas DataFrames.
    """

    def __init__(self, df: pd.DataFrame = None, table_name: str = "data", db_path: str = ":memory:"):
        self.db_path = db_path
        self.table_name = table_name
        self.conn: Optional[sqlite3.Connection] = None
        self._create_connection()
        if df is not None:
            self.store_dataframe(df, table_name=self.table_name, if_exists="replace")

    def _create_connection(self) -> None:
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            raise RuntimeError(f"Unable to create sqlite connection: {e}")

    def store_dataframe(self, df: pd.DataFrame, table_name: Optional[str] = None, if_exists: str = "replace") -> None:
        """Store the provided DataFrame into the SQLite database."""
        if table_name is None:
            table_name = self.table_name
        if self.conn is None:
            self._create_connection()
        # Use pandas to_sql which will create/replace the table
        df.to_sql(table_name, self.conn, if_exists=if_exists, index=False)
        # keep latest dataframe schema
        self.table_name = table_name

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute arbitrary read-only SQL and return a pandas DataFrame.

        Raises RuntimeError on errors to surface failures to the caller.
        """
        if self.conn is None:
            raise RuntimeError("No database connection")
        try:
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            raise RuntimeError(f"Error executing query: {e}")

    def list_tables(self) -> List[str]:
        q = "SELECT name FROM sqlite_master WHERE type='table'"
        df = self.execute_query(q)
        return df['name'].tolist() if 'name' in df.columns else []

    def get_columns(self, table_name: Optional[str] = None) -> List[str]:
        if table_name is None:
            table_name = self.table_name
        q = f"PRAGMA table_info('{table_name}')"
        info = self.execute_query(q)
        return info['name'].tolist() if 'name' in info.columns else []

    def get_column_summary(self, column: str, table_name: Optional[str] = None) -> dict:
        """Return summary statistics for a single column using SQL when possible.

        The method will fall back to Python computations for aggregates not
        supported by SQLite (e.g., precision issues or advanced stats).
        """
        if table_name is None:
            table_name = self.table_name

        if column not in self.get_columns(table_name):
            raise ValueError(f"Column '{column}' not found in table '{table_name}'")

        # Basic counts: total rows, nulls, distinct
        q = f"SELECT COUNT(1) as row_count, SUM(CASE WHEN \"{column}\" IS NULL THEN 1 ELSE 0 END) as null_count, COUNT(DISTINCT \"{column}\") as distinct_count FROM \"{table_name}\""
        base = self.execute_query(q).to_dict(orient='records')[0]

        # Try numeric aggs (min/max/avg) via SQL; if fails, compute in Python
        try:
            q_num = f"SELECT MIN(\"{column}\") as min_val, MAX(\"{column}\") as max_val, AVG(\"{column}\") as avg_val FROM \"{table_name}\""
            num_aggs = self.execute_query(q_num).to_dict(orient='records')[0]
        except Exception:
            num_aggs = {"min_val": None, "max_val": None, "avg_val": None}

        return {
            "column": column,
            "row_count": int(base.get('row_count', 0)),
            "null_count": int(base.get('null_count', 0)),
            "distinct_count": int(base.get('distinct_count', 0)),
            "min": num_aggs.get('min_val'),
            "max": num_aggs.get('max_val'),
            "avg": num_aggs.get('avg_val'),
        }

    def generate_dataset_summary(self, table_name: Optional[str] = None) -> pd.DataFrame:
        """Generate a dataset summary DataFrame with per-column metrics.

        The returned DataFrame contains: column, row_count, null_count,
        distinct_count, min, max, avg (when applicable).
        """
        if table_name is None:
            table_name = self.table_name

        columns = self.get_columns(table_name)
        rows = []
        for col in columns:
            try:
                rows.append(self.get_column_summary(col, table_name=table_name))
            except Exception:
                # If a column summary failed, include a row with error markers
                rows.append({"column": col, "row_count": None, "null_count": None, "distinct_count": None, "min": None, "max": None, "avg": None})

        return pd.DataFrame(rows)

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None


def create_sql_engine(df: pd.DataFrame = None, table_name: str = "data", db_path: str = ":memory:") -> DataFrameSQLEngine:
    return DataFrameSQLEngine(df=df, table_name=table_name, db_path=db_path)
