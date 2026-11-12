"""
Export lead data to CSV and XLSX files.
"""

import os

import pandas as pd

from config import OUTPUT_DIR, CSV_FILENAME, XLSX_FILENAME
from utils.logger import get_logger

log = get_logger("exporter")

COLUMN_ORDER = [
    "company_name",
    "email",
    "phone",
    "address",
    "pincode",
    "domain",
    "website",
    "category",
    "social_links",
]


def export(records: list[dict]) -> tuple[str, str]:
    """Write *records* to both CSV and XLSX. Returns (csv_path, xlsx_path)."""
    if not records:
        log.warning("No records to export.")
        return "", ""

    df = pd.DataFrame(records)

    # Keep only known columns (in order), silently ignore missing ones
    cols = [c for c in COLUMN_ORDER if c in df.columns]
    df = df[cols]

    csv_path = os.path.join(OUTPUT_DIR, CSV_FILENAME)
    xlsx_path = os.path.join(OUTPUT_DIR, XLSX_FILENAME)

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    log.info("CSV  exported → %s  (%d rows)", csv_path, len(df))

    df.to_excel(xlsx_path, index=False, engine="openpyxl", sheet_name="Leads")
    log.info("XLSX exported → %s  (%d rows)", xlsx_path, len(df))

    return csv_path, xlsx_path
