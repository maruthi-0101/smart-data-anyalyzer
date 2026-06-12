"""modules.report_generator

Functions to export data (CSV, Excel, JSON) and to generate a PDF report
using reportlab. The PDF includes Dataset Overview, Data Quality, Missing
Values Summary, EDA Results, SQL Summary, and Recommendations.
"""

from typing import Any, Dict, List, Optional
import io
import json
import logging

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


def export_csv(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def export_json(df: pd.DataFrame) -> bytes:
    records = df.to_dict(orient="records")
    return json.dumps(records, indent=2, default=str).encode("utf-8")


def export_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    buf.seek(0)
    return buf.read()


def build_export_payloads(df: pd.DataFrame) -> Dict[str, bytes]:
    """Build all export payloads up front so callers can pass ready-to-download data."""
    return {
        "csv": export_csv(df),
        "excel": export_excel(df),
        "json": export_json(df),
    }


def _small_table(data: List[List[Any]]) -> Table:
    tbl = Table(data, hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    )
    return tbl


def generate_pdf_report(
    analysis_results: Dict[str, Any],
    ai_results: Optional[Dict[str, Any]] = None,
    df: Optional[pd.DataFrame] = None,
    title: str = "Smart Data Analyzer Report",
) -> bytes:
    """Generate a PDF report and return its bytes.

    `analysis_results` is expected to come from `auto_inspect` and
    contain 'data_quality', 'eda_summary', 'sql_summary', etc.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = []

    # Title
    flow.append(Paragraph(title, styles["Title"]))
    flow.append(Spacer(1, 12))

    # Dataset Overview
    flow.append(Paragraph("Dataset Overview", styles["Heading2"]))
    dq = analysis_results.get("data_quality", {})
    rows = dq.get("rows", "N/A")
    cols = dq.get("columns", "N/A")
    quality = dq.get("data_quality_score", "N/A")
    flow.append(Paragraph(f"Rows: {rows}", styles["Normal"]))
    flow.append(Paragraph(f"Columns: {cols}", styles["Normal"]))
    flow.append(Paragraph(f"Data Quality Score: {quality}", styles["Normal"]))
    flow.append(Spacer(1, 12))

    # Missing Values Summary
    flow.append(Paragraph("Missing Values Summary", styles["Heading2"]))
    missing = dq.get("missing_by_column", [])
    if missing:
        table_data = [["Column", "Missing Count", "Missing %", "Unique Values"]]
        for r in missing:
            table_data.append([r.get("column"), r.get("missing_count"), r.get("missing_percentage"), r.get("unique_values")])
        flow.append(_small_table(table_data))
    else:
        flow.append(Paragraph("No missing values detected.", styles["Normal"]))
    flow.append(Spacer(1, 12))

    # EDA Results (numerical summary sample)
    flow.append(Paragraph("EDA Summary (Numerical)", styles["Heading2"]))
    eda = analysis_results.get("eda_summary", {})
    numeric = eda.get("numerical_summary", [])
    if numeric:
        # show up to first 10 columns summary
        table_data = [["Column", "Mean", "Median", "Std Dev", "Min", "Max"]]
        for row in numeric[:10]:
            table_data.append([
                row.get("column"),
                round(row.get("mean", 0), 4) if row.get("mean") is not None else "",
                round(row.get("median", 0), 4) if row.get("median") is not None else "",
                round(row.get("std", 0), 4) if row.get("std") is not None else "",
                row.get("min", ""),
                row.get("max", ""),
            ])
        flow.append(_small_table(table_data))
    else:
        flow.append(Paragraph("No numerical summary available.", styles["Normal"]))
    flow.append(Spacer(1, 12))

    # SQL Summary
    flow.append(Paragraph("SQL Analysis Summary", styles["Heading2"]))
    sql_summary = analysis_results.get("sql_summary")
    if sql_summary:
        # show first few rows of sql summary
        keys = list(sql_summary[0].keys()) if sql_summary else []
        table_data = [keys]
        for r in sql_summary[:10]:
            table_data.append([r.get(k, "") for k in keys])
        flow.append(_small_table(table_data))
    else:
        flow.append(Paragraph("No SQL summary available.", styles["Normal"]))
    flow.append(Spacer(1, 12))

    # AI Recommendations / Insights
    flow.append(Paragraph("Recommendations", styles["Heading2"]))
    if ai_results is None:
        # fallback to analysis key findings
        findings = analysis_results.get("key_findings", [])
    else:
        findings = ai_results.get("recommendations") or ai_results.get("key_insights") or []

    if findings:
        for f in findings:
            flow.append(Paragraph(f"- {f}", styles["Normal"]))
    else:
        flow.append(Paragraph("No recommendations generated.", styles["Normal"]))

    # Build PDF
    try:
        doc.build(flow)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        logger.error("Failed to generate PDF report: %s", e)
        raise
