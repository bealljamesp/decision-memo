"""Fetch the latest 30-year fixed mortgage rate from Freddie Mac's Primary Mortgage Market Survey.

The survey is national and weekly. The rate is returned as an annual decimal (0.0718 for 7.18%),
which is the form model.py expects.

Usage:
    python src/fetch_rates.py                       # downloads the PMMS history file
    python src/fetch_rates.py --csv PMMS_history.csv  # reads a file you already saved

Writes data/raw/pmms_30yr_latest.json. The raw directory is gitignored.

Caveat: the parser assumes the history CSV has a date column and a 30-year rate column
(a header containing "30"). It is unit-tested on a fixture. It has not been checked
against the live file in this environment.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

PMMS_HISTORY_URL = "https://www.freddiemac.com/pmms/docs/PMMS_history.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "pmms_30yr_latest.json"


def _find_column(header: list[str], predicate) -> int:
    for i, name in enumerate(header):
        if predicate(name.strip().lower()):
            return i
    raise ValueError(f"no matching column in header: {header}")


def _parse_date(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognized date: {raw!r}")


def latest_30yr(lines: Iterable[str]) -> dict:
    """Return {'date': 'YYYY-MM-DD', 'rate': annual decimal} for the most recent 30-year reading."""
    reader = csv.reader(lines)
    header = next(reader)
    date_col = _find_column(header, lambda n: n.startswith("date") or n == "week")
    rate_col = _find_column(header, lambda n: "30" in n and ("rate" in n or "fixed" in n or "y" in n))

    best_date, best_rate = None, None
    for row in reader:
        if len(row) <= max(date_col, rate_col) or not row[rate_col].strip():
            continue
        try:
            rate = float(row[rate_col]) / 100.0
            date = _parse_date(row[date_col])
        except ValueError:
            continue
        if best_date is None or date > best_date:
            best_date, best_rate = date, rate

    if best_date is None:
        raise ValueError("no 30-year rate readings found")
    return {"date": best_date.strftime("%Y-%m-%d"), "rate": best_rate, "series": "30-year fixed, PMMS"}


def fetch_lines(url: str, timeout: int = 60) -> list[str]:
    import requests

    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text.splitlines()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, help="local PMMS history CSV (skips the download)")
    parser.add_argument("--url", default=PMMS_HISTORY_URL, help="PMMS history CSV URL")
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args(argv)

    if args.csv:
        lines = args.csv.read_text().splitlines()
    else:
        lines = fetch_lines(args.url)

    result = latest_30yr(lines)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(f"30-year fixed rate as of {result['date']}: {result['rate']:.2%}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
