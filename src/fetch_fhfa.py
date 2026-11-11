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
from collections import Counter
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
    "hpi_flavor": "purchase-only",
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


def summarize_cbsa(lines: Iterable[str], cbsa: str, name_hint: str = "Los Angeles") -> str:
    """Describe what the file holds for a CBSA, to diagnose an empty selection."""
    reader = csv.DictReader(lines)
    combos: Counter = Counter()
    name_matches: dict[str, str] = {}
    for row in reader:
        if row.get("place_id", "").strip() == cbsa:
            combos[(row.get("hpi_type"), row.get("hpi_flavor"), row.get("frequency"), row.get("level"))] += 1
        elif name_hint.lower() in row.get("place_name", "").lower():
            name_matches.setdefault(row["place_id"].strip(), row["place_name"])
    lines_out = [f"Rows for CBSA {cbsa} by (hpi_type, hpi_flavor, frequency, level):"]
    lines_out += [f"  {combo}: {count}" for combo, count in combos.most_common()] or ["  none: place_id not in file"]
    if name_matches:
        lines_out.append(f"Places whose name contains '{name_hint}':")
        lines_out += [f"  {pid}: {name}" for pid, name in name_matches.items()]
    return "\n".join(lines_out)


def fetch_lines(url: str, timeout: int = 120) -> list[str]:
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()
    return list(response.iter_lines(decode_unicode=True))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cbsa", required=True, help="5-digit CBSA code, e.g. 31080 for Los Angeles")
    parser.add_argument("--url", default=FHFA_MASTER_URL, help="FHFA master CSV to read")
    args = parser.parse_args(argv)

    lines = fetch_lines(args.url)
    rows = select_metro_rows(lines, args.cbsa)
    if not rows:
        raise SystemExit(
            f"No purchase-only quarterly MSA rows found for CBSA {args.cbsa} in {args.url}.\n"
            + summarize_cbsa(lines, args.cbsa)
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"fhfa_hpi_{args.cbsa}.json"
    out_path.write_text(json.dumps({"cbsa": args.cbsa, "source": FHFA_MASTER_URL, "rows": rows}, indent=2))
    print(f"Wrote {len(rows)} quarters to {out_path}")


if __name__ == "__main__":
    main()
