"""Fetch ACS 1-year median home value and median gross rent for one area.

The area is either a metro (CBSA) or a county (state FIPS + county FIPS).

Usage:
    CENSUS_API_KEY=... python src/fetch_acs.py --county-fips 06037 --year 2024
    CENSUS_API_KEY=... python src/fetch_acs.py --cbsa 31080 --year 2024

Writes data/raw/acs_<year>_<area>.json. The raw directory is gitignored.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

ACS_BASE = "https://api.census.gov/data/{year}/acs/acs1"
CBSA_FIELD = "metropolitan statistical area/micropolitan statistical area"

# ACS table variables: B25077 is median value (owner-occupied), B25064 is median gross rent.
VARIABLES = {
    "B25077_001E": "median_home_value",
    "B25064_001E": "median_gross_rent",
}

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def build_params(api_key: str, cbsa: str | None = None, county_fips: str | None = None) -> dict:
    """Build query parameters for a metro (cbsa) or a county (5-digit state+county FIPS)."""
    if bool(cbsa) == bool(county_fips):
        raise ValueError("pass exactly one of cbsa or county_fips")
    params = {"get": "NAME," + ",".join(VARIABLES), "key": api_key}
    if cbsa:
        params["for"] = f"{CBSA_FIELD}:{cbsa}"
    else:
        if len(county_fips) != 5 or not county_fips.isdigit():
            raise ValueError("county_fips must be 5 digits: 2-digit state + 3-digit county")
        params["for"] = f"county:{county_fips[2:]}"
        params["in"] = f"state:{county_fips[:2]}"
    return params


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
    geography = {
        column: record[column]
        for column in header
        if column != "NAME" and column not in VARIABLES
    }
    result = {"name": record["NAME"], "geography": geography}
    for code, label in VARIABLES.items():
        result[label] = _clean(record.get(code))
    return result


def fetch_housing(
    api_key: str,
    year: int,
    cbsa: str | None = None,
    county_fips: str | None = None,
    timeout: int = 30,
) -> dict:
    url = ACS_BASE.format(year=year)
    params = build_params(api_key, cbsa=cbsa, county_fips=county_fips)
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    record = parse_acs_response(response.json())
    record["year"] = year
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cbsa", help="5-digit CBSA code, e.g. 31080 for the LA metro")
    group.add_argument("--county-fips", help="5-digit state+county FIPS, e.g. 06037 for LA County")
    parser.add_argument("--year", type=int, required=True, help="ACS 1-year vintage, e.g. 2024")
    args = parser.parse_args(argv)

    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("Set CENSUS_API_KEY in the environment (get a free key from census.gov).")

    area = args.cbsa or args.county_fips
    record = fetch_housing(api_key, args.year, cbsa=args.cbsa, county_fips=args.county_fips)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"acs_{args.year}_{area}.json"
    out_path.write_text(json.dumps(record, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
