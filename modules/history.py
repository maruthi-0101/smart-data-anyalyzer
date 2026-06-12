"""modules.history
Simple SQLite-backed persistence for analysis history.

Provides helpers to initialize the database and perform CRUD on the
`analysis_history` table required by the app.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default DB location: project root / history.db
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "history.db"


def _get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    p = db_path or DB_PATH
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_history_db(db_path: Optional[str] = None) -> None:
    """Create the `analysis_history` table if it doesn't exist.

    Columns (per requirements):
      - id (INTEGER PRIMARY KEY AUTOINCREMENT)
      - filename (TEXT)
      - file_type (TEXT)
      - upload_time (TEXT)
      - rows_count (INTEGER)
      - columns_count (INTEGER)
      - data_quality_score (REAL)
    """
    conn = _get_conn(Path(db_path) if db_path else None)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_type TEXT,
            upload_time TEXT NOT NULL,
            rows_count INTEGER,
            columns_count INTEGER,
            data_quality_score REAL
        )
        """
    )
    conn.commit()
    conn.close()


def save_analysis_record(
    filename: str,
    file_type: str,
    rows_count: int,
    columns_count: int,
    data_quality_score: float,
    upload_time: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Insert a new analysis record and return the new id."""
    ts = upload_time or datetime.utcnow().isoformat()
    conn = _get_conn(Path(db_path) if db_path else None)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO analysis_history (filename, file_type, upload_time, rows_count, columns_count, data_quality_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (filename, file_type, ts, int(rows_count), int(columns_count), float(data_quality_score)),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return int(new_id)


def list_history(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all records ordered by newest first."""
    conn = _get_conn(Path(db_path) if db_path else None)
    cur = conn.cursor()
    cur.execute("SELECT * FROM analysis_history ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_history(record_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = _get_conn(Path(db_path) if db_path else None)
    cur = conn.cursor()
    cur.execute("SELECT * FROM analysis_history WHERE id = ?", (int(record_id),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_history(record_id: int, db_path: Optional[str] = None) -> bool:
    conn = _get_conn(Path(db_path) if db_path else None)
    cur = conn.cursor()
    cur.execute("DELETE FROM analysis_history WHERE id = ?", (int(record_id),))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return bool(changed)
