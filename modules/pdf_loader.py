"""modules.pdf_loader

Utilities to extract tables from PDF files and convert to pandas DataFrame.
Supports both PDF table extraction (via pdfplumber) and a text-based
parsing fallback for PDFs that contain tabular text but no explicit table
structures. Handles multi-page PDFs.
"""

from typing import List, Optional
import io
import logging
from collections import Counter
import re

import pandas as pd
import pdfplumber

logger = logging.getLogger(__name__)


def _read_bytes(file_obj) -> bytes:
    if hasattr(file_obj, "read"):
        file_obj.seek(0)
        return file_obj.read()
    if isinstance(file_obj, (bytes, bytearray)):
        return bytes(file_obj)
    raise ValueError("Unsupported file object: must be file-like or bytes")


def extract_tables_from_pdf(file_obj) -> List[pd.DataFrame]:
    """Extract explicit tables from PDF pages using pdfplumber.

    Returns a list of DataFrames (may be empty).
    """
    data = _read_bytes(file_obj)
    dfs: List[pd.DataFrame] = []

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.extract_tables()
                except Exception as e:
                    logger.warning("Failed to extract tables on page %s: %s", page_number, e)
                    continue

                for table in tables:
                    if not table:
                        continue
                    df = pd.DataFrame(table)
                    # If first row looks like header (contains alphabetic characters), set as header
                    first_row = df.iloc[0].astype(str).tolist()
                    if any(any(c.isalpha() for c in str(cell)) for cell in first_row):
                        df.columns = first_row
                        df = df.drop(df.index[0]).reset_index(drop=True)
                    df = df.replace({"": None})
                    dfs.append(df)
    except Exception as e:
        logger.error("Error reading PDF: %s", e)
        raise

    return dfs


def _split_line_tokens(line: str) -> List[str]:
    """Split a line into tokens using multiple-space/tab separators; fallback to whitespace."""
    parts = re.split(r"\s{2,}|\t", line.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        parts = re.split(r"\s+", line.strip())
        parts = [p.strip() for p in parts if p.strip()]
    return parts


def _parse_text_table(text: str) -> Optional[pd.DataFrame]:
    """Attempt to parse a text block into a DataFrame.

    Strategy:
    - Split text into non-empty lines
    - Try to find a header line within first 10 lines containing alphabetic tokens
    - Use tokenization based on multiple spaces/tabs
    - Collect subsequent lines as rows; handle wrapped lines heuristically
    - If no clear header, detect most common token count and use generic column names
    """
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return None

    max_header_search = min(10, len(lines))
    for idx in range(max_header_search):
        header_tokens = _split_line_tokens(lines[idx])
        if len(header_tokens) >= 2 and any(re.search(r"[A-Za-z]", t) for t in header_tokens):
            rows: List[List[str]] = []
            for l in lines[idx + 1:]:
                toks = _split_line_tokens(l)
                if not toks:
                    continue
                if len(toks) == len(header_tokens):
                    rows.append(toks)
                elif len(toks) > len(header_tokens):
                    merged = toks[: len(header_tokens) - 1] + [" ".join(toks[len(header_tokens) - 1 :])]
                    rows.append(merged)
                else:
                    if rows:
                        rows[-1][-1] = rows[-1][-1] + " " + " ".join(toks)
                    else:
                        continue

            if rows:
                try:
                    df = pd.DataFrame(rows, columns=header_tokens)
                    return df
                except Exception:
                    break

    # Fallback: detect most common token count and build generic header
    token_counts = [len(_split_line_tokens(l)) for l in lines]
    filtered = [c for c in token_counts if c > 1]
    if not filtered:
        return None
    most_common_count, _ = Counter(filtered).most_common(1)[0]
    if most_common_count < 2:
        return None

    rows = []
    for l in lines:
        toks = _split_line_tokens(l)
        if len(toks) == most_common_count:
            rows.append(toks)

    if not rows:
        return None

    headers = [f"col_{i+1}" for i in range(most_common_count)]
    df = pd.DataFrame(rows, columns=headers)
    return df


def load_pdf_to_df(file_obj, concat: bool = True) -> Optional[pd.DataFrame]:
    """Load first (or concatenated) table(s) from PDF into a DataFrame.

    If `concat` is True and multiple tables have identical columns, they
    will be concatenated. Otherwise the first table is returned. If no
    explicit tables are found, attempt text-based parsing to extract rows.
    """
    tables = extract_tables_from_pdf(file_obj)
    if tables:
        if len(tables) == 1:
            return tables[0]
        if concat:
            try:
                same_cols = [tuple(df.columns) for df in tables]
                if len(set(same_cols)) == 1:
                    return pd.concat(tables, ignore_index=True)
            except Exception:
                pass
        return tables[0]

    # No explicit tables — extract text and attempt to parse
    try:
        data = _read_bytes(file_obj)
        all_text = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                try:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                except Exception:
                    continue
        full_text = "\n".join(all_text)
        if not full_text.strip():
            return None

        df = _parse_text_table(full_text)
        return df
    except Exception as e:
        logger.error("Failed to parse PDF text: %s", e)
        raise
