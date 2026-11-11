"""Fetch ACS 1-year median home value and median gross rent for one metro (CBSA).

Usage:
    CENSUS_API_KEY=... python src/fetch_acs.py --cbsa 31080 --year 2024

Writes data/raw/acs_<year>_<cbsa>.json. The raw directory is gitignored.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

ACS_BASE = "https://api.census.gov/data/{year}/acs/acs1"
GEO_FIELD = "metropolitan statistical area/micropolitan statistical area"

# ACS table variables: B25077 is median value (owner-occupied), B25064 is median gross rent.
VARIABLES = {
    "B25077_001E": "median_home_value",
    "B25064_001E": "median_gross_rent",
}

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def build_params(cbsa: str, api_key: str) -> dict:
    return {
        "get": "NAME," + ",".join(VARIABLES),
        "for": f"{GEO_FIELD}:{cbsa}",
        "key": api_key,
    }


def _clean(raw: str | None) -> float | None:
    """Return a float, or None for missing values and Census negative sentinels."""
    if raw is None:
        return None
    value = float(raw)
    return None if value < 0 else value


def parse_acs_response(rows: list[list[str | None]]) -> dict:
    """Turn the Census API's header-plus-one-row response into a flat record."""
    if len(rows) != 2:
        raise ValueError(f"expected a header row and one data row, got {len(rows)} rows")
    header, values = rows
    record = dict(zip(header, values))
    result = {
        "name": record["NAME"],
        "cbsa": record[GEO_FIELD],
    }
    for code, label in VARIABLES.items():
        result[label] = _clean(record.get(code))
    return result


def fetch_metro_housing(cbsa: str, year: int, api_key: str, timeout: int = 30) -> dict:
    url = ACS_BASE.format(year=year)
    response = requests.get(url, params=build_params(cbsa, api_key), timeout=timeout)
    response.raise_for_status()
    record = parse_acs_response(response.json())
    record["year"] = year
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cbsa", required=True, help="5-digit CBSA code, e.g. 31080 for Los Angeles")
    parser.add_argument("--year", type=int, required=True, help="ACS 1-year vintage, e.g. 2024")
    args = parser.parse_args(argv)

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set CENSUS_API_KEY in the environment (get a free key from census.gov).")

    record = fetch_metro_housing(args.cbsa, args.year, api_key)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"acs_{args.year}_{args.cbsa}.json"
    out_path.write_text(json.dumps(record, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
