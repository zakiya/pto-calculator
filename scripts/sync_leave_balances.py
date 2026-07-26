#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
#     "openpyxl>=3.1",
#     "xlrd>=2.0",
# ]
# ///
"""Sync a Tempo "Leave Balances" export into the Coda doc "PTO Calculator".

The Tempo export is one row per leave category and 148 columns wide (12 months
x 12 metrics). This flattens it to one row per category+month and upserts into
the `Leave Balances` table, keyed on `Key` so re-running is idempotent.

    uv run scripts/sync_leave_balances.py                 # newest file in input/tempo-downloads
    uv run scripts/sync_leave_balances.py path/to.xls     # a specific file
    uv run scripts/sync_leave_balances.py --dry-run       # parse and print, no API calls

Needs a Coda API token (https://coda.io/account) in CODA_API_TOKEN, either
exported or in a .env file at the project root.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input" / "tempo-downloads"

# Target: https://docs.superhuman.com/d/PTO-Calculator_dOxYiewNUHt
DEFAULT_DOC_ID = "OxYiewNUHt"
DEFAULT_TABLE_ID = "grid-qTEhXKpw1j"  # "Leave Balances"

API_BASE = "https://coda.io/apis/v1"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Tempo's per-month metric suffixes. These double as the Coda column names, so
# a rename on either side surfaces as a clear error rather than silent drift.
METRICS = [
    "Begin", "Used", "Accrued", "Misc", "FLSA CTO", "CTO", "End",
    "Waiting Period End", "SSMOS", "Proj. Accrual", "Proj. End", "Proj. SSM",
]

KEY_COLUMN = "Key"


class SyncError(Exception):
    """Anything that should stop the run with a readable message."""


# --------------------------------------------------------------------------- #
# Reading the spreadsheet
# --------------------------------------------------------------------------- #

def normalize(value: Any) -> Any:
    """Collapse the empty-cell representations of xlrd ('') and openpyxl (None)."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def read_grid(path: Path) -> list[list[Any]]:
    """Read the first sheet of an .xls or .xlsx file into a list of rows."""
    suffix = path.suffix.lower()
    if suffix == ".xls":
        import xlrd

        sheet = xlrd.open_workbook(path).sheet_by_index(0)
        return [
            [normalize(sheet.cell_value(r, c)) for c in range(sheet.ncols)]
            for r in range(sheet.nrows)
        ]
    if suffix in (".xlsx", ".xlsm"):
        import openpyxl

        sheet = openpyxl.load_workbook(path, data_only=True).worksheets[0]
        return [[normalize(cell) for cell in row] for row in sheet.iter_rows(values_only=True)]
    raise SyncError(f"Unsupported file type {suffix!r}: {path}")


def cell(row: list[Any], index: int) -> Any:
    return row[index] if index < len(row) else None


def find_header_row(grid: list[list[Any]]) -> int:
    """Locate the row that starts the data table (`Year | Category | ...`)."""
    for i, row in enumerate(grid):
        if cell(row, 0) == "Year" and cell(row, 1) == "Category":
            return i
    raise SyncError(
        "Could not find the header row (expected a row starting with 'Year', 'Category'). "
        "Did Tempo change its export format?"
    )


def read_preamble(grid: list[list[Any]], header_row: int) -> dict[str, Any]:
    """Pull `Employee Name:` / `Year:` out of the rows above the header."""
    meta: dict[str, Any] = {}
    for row in grid[:header_row]:
        label = cell(row, 0)
        if not isinstance(label, str):
            continue
        key = label.rstrip(": ").strip().lower()
        if key in ("employee name", "year"):
            meta[key] = cell(row, 1)
    if not meta.get("employee name"):
        raise SyncError("Could not find 'Employee Name:' above the header row.")
    return meta


def parse_month_columns(header: list[Any]) -> dict[tuple[str, str], int]:
    """Map (month, metric) -> column index, from headers like 'January Begin'."""
    columns: dict[tuple[str, str], int] = {}
    for index, name in enumerate(header):
        if not isinstance(name, str):
            continue
        for month in MONTHS:
            if name.startswith(month + " "):
                metric = name[len(month) + 1:].strip()
                if metric in METRICS:
                    columns[(month, metric)] = index
                break
    missing = [
        f"{month} {metric}"
        for month in MONTHS
        for metric in METRICS
        if (month, metric) not in columns
    ]
    if missing:
        raise SyncError(
            f"{len(missing)} expected month/metric columns are missing from the export, "
            f"starting with {missing[0]!r}. Did Tempo change its export format?"
        )
    return columns


def parse_export(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """Flatten the export into one record per (category, month).

    Returns the employee name and the records. Cells that are blank in the
    export are left out of the record entirely rather than written as zero --
    Tempo emits an explicit 0.0 for a real zero, so blank means "not
    applicable" and should stay blank in Coda.
    """
    grid = read_grid(path)
    header_row = find_header_row(grid)
    header = grid[header_row]
    meta = read_preamble(grid, header_row)
    month_columns = parse_month_columns(header)

    employee = str(meta["employee name"])
    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    records: list[dict[str, Any]] = []
    for row in grid[header_row + 1:]:
        category = cell(row, 1)
        if not category:
            continue  # trailing blank / total rows
        year = int(cell(row, 0) or meta.get("year") or 0)
        last_updated = cell(row, 3)

        for month_number, month in enumerate(MONTHS, start=1):
            record: dict[str, Any] = {
                KEY_COLUMN: f"{employee}|{year}|{category}|{month_number:02d}",
                "Employee": employee,
                "Year": year,
                "Month #": month_number,
                "Month": month,
                "Category": category,
                "Synced At": synced_at,
            }
            if last_updated is not None:
                record["Last Updated"] = last_updated
            for metric in METRICS:
                value = cell(row, month_columns[(month, metric)])
                if value is not None:
                    record[metric] = value
            records.append(record)

    if not records:
        raise SyncError(f"No leave categories found in {path}")
    return employee, records


# --------------------------------------------------------------------------- #
# Writing to Coda
# --------------------------------------------------------------------------- #

def load_token() -> str:
    token = os.environ.get("CODA_API_TOKEN")
    if not token:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                if name.strip() == "CODA_API_TOKEN":
                    token = value.strip().strip("'\"")
                    break
    if not token:
        raise SyncError(
            "CODA_API_TOKEN is not set. Create a token at https://coda.io/account "
            "then either `export CODA_API_TOKEN=...` or add it to .env (see .env.example)."
        )
    return token


def upsert(
    client: httpx.Client,
    doc_id: str,
    table_id: str,
    records: list[dict[str, Any]],
    batch_size: int = 100,
) -> list[str]:
    """Upsert records keyed on `Key`, returning one mutation id per batch."""
    url = f"{API_BASE}/docs/{doc_id}/tables/{table_id}/rows"
    request_ids: list[str] = []
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        payload = {
            "rows": [
                {"cells": [{"column": name, "value": value} for name, value in record.items()]}
                for record in batch
            ],
            "keyColumns": [KEY_COLUMN],
        }
        response = client.post(url, json=payload)
        if response.status_code >= 400:
            raise SyncError(f"Coda rejected the upsert ({response.status_code}): {response.text}")
        request_ids.append(response.json()["requestId"])
        print(f"  sent rows {start + 1}-{start + len(batch)} of {len(records)}")
    return request_ids


def wait_for(client: httpx.Client, request_ids: list[str], timeout: float = 120.0) -> None:
    """Coda applies row writes asynchronously; block until they land."""
    deadline = time.monotonic() + timeout
    pending = list(request_ids)
    while pending:
        if time.monotonic() > deadline:
            raise SyncError(
                f"Timed out after {timeout:.0f}s waiting for Coda to apply "
                f"{len(pending)} of {len(request_ids)} batches. The rows may still land; "
                "re-run to confirm."
            )
        time.sleep(2)
        still_pending = []
        for request_id in pending:
            response = client.get(f"{API_BASE}/mutationStatus/{request_id}")
            if response.status_code >= 400 or not response.json().get("completed"):
                still_pending.append(request_id)
        pending = still_pending


# --------------------------------------------------------------------------- #

def newest_export() -> Path:
    if not INPUT_DIR.is_dir():
        raise SyncError(f"No input directory at {INPUT_DIR}")
    candidates = [
        p for p in INPUT_DIR.iterdir()
        if p.suffix.lower() in (".xls", ".xlsx", ".xlsm") and not p.name.startswith("~$")
    ]
    if not candidates:
        raise SyncError(
            f"No spreadsheet found in {INPUT_DIR}. Download one from "
            "Tempo > Home > View Leave Balances > Download to Excel."
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "file", nargs="?", type=Path,
        help=f"Tempo export to sync (default: newest file in {INPUT_DIR.relative_to(PROJECT_ROOT)})",
    )
    parser.add_argument("--doc", default=os.environ.get("CODA_DOC_ID", DEFAULT_DOC_ID))
    parser.add_argument("--table", default=os.environ.get("CODA_TABLE_ID", DEFAULT_TABLE_ID))
    parser.add_argument("--dry-run", action="store_true", help="Parse and summarize without writing to Coda")
    args = parser.parse_args()

    try:
        path = args.file or newest_export()
        if not path.exists():
            raise SyncError(f"No such file: {path}")

        print(f"Reading {path}")
        employee, records = parse_export(path)
        categories = sorted({r["Category"] for r in records})
        years = sorted({r["Year"] for r in records})
        print(
            f"Parsed {len(records)} rows for {employee} "
            f"({len(categories)} categories: {', '.join(categories)}; year {', '.join(map(str, years))})"
        )

        if args.dry_run:
            print("\n--dry-run, not writing. First 3 rows:")
            for record in records[:3]:
                print(f"  {record}")
            return 0

        token = load_token()
        print(f"Upserting into doc {args.doc}, table {args.table}")
        with httpx.Client(
            headers={"Authorization": f"Bearer {token}"}, timeout=60.0
        ) as client:
            request_ids = upsert(client, args.doc, args.table, records)
            print("Waiting for Coda to apply the writes...")
            wait_for(client, request_ids)

        print(f"Done. {len(records)} rows synced.")
        return 0
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
