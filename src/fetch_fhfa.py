"""Fetch FHFA quarterly purchase-only house price index for one metro (CBSA).

Usage:
    python src/fetch_fhfa.py --cbsa 31080

Downloads FHFA's master HPI file, keeps the metro-level, purchase-only, quarterly
rows for the CBSA, and writes data/raw/fhfa_hpi_<cbsa>.json. The raw directory
is gitignored.

Purchase-only indexes leave out appraisal values, so they track actual sales.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

import requests

FHFA_MASTER_URL = "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv"

# Columns the script depends on. If FHFA renames any of them, fail with a clear error.
REQUIRED_COLUMNS = {
    "hpi_type",
    "hpi_flavor",
    "frequency",
    "level",
    "place_id",
    "yr",
    "period",
    "index_nsa",
    "index_sa",
}

# Row filters: metro-level, traditional repeat-sales index, purchase-only, quarterly.
FILTERS = {
    "hpi_type": "traditional",
    "hpi_flavor": "purchase_only",
    "frequency": "quarterly",
    "level": "MSA",
}

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def _float_or_none(raw: str) -> float | None:
    raw = raw.strip()
    return float(raw) if raw else None


def select_metro_rows(lines: Iterable[str], cbsa: str) -> list[dict]:
    """Return the quarterly purchase-only index rows for one CBSA, oldest first."""
    reader = csv.DictReader(lines)
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"FHFA file is missing expected columns: {sorted(missing)}")

    rows = []
    for row in reader:
        if row["place_id"].strip() != cbsa:
            continue
        if any(row[column] != value for column, value in FILTERS.items()):
            continue
        rows.append(
            {
                "year": int(row["yr"]),
                "quarter": int(row["period"]),
                "index_nsa": _float_or_none(row["index_nsa"]),
                "index_sa": _float_or_none(row["index_sa"]),
            }
        )
    rows.sort(key=lambda r: (r["year"], r["quarter"]))
    return rows


def fetch_metro_hpi(cbsa: str, timeout: int = 120) -> list[dict]:
    response = requests.get(FHFA_MASTER_URL, stream=True, timeout=timeout)
    response.raise_for_status()
    return select_metro_rows(response.iter_lines(decode_unicode=True), cbsa)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cbsa", required=True, help="5-digit CBSA code, e.g. 31080 for Los Angeles")
    args = parser.parse_args(argv)

    rows = fetch_metro_hpi(args.cbsa)
    if not rows:
        raise SystemExit(f"No purchase-only quarterly MSA rows found for CBSA {args.cbsa}.")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"fhfa_hpi_{args.cbsa}.json"
    out_path.write_text(json.dumps({"cbsa": args.cbsa, "source": FHFA_MASTER_URL, "rows": rows}, indent=2))
    print(f"Wrote {len(rows)} quarters to {out_path}")


if __name__ == "__main__":
    main()
