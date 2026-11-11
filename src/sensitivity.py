"""Sensitivity grid: five-year buy advantage across mortgage rates and price growth.

Usage:
    python src/sensitivity.py --acs data/raw/acs_2024_06037.json --fhfa data/raw/fhfa_hpi_31084.json

Writes one CSV per down payment share to data/processed/. Positive values mean buying
comes out ahead of renting over the horizon; negative values mean renting does.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path

from model import Assumptions, break_even_growth, compare_rent_vs_buy, trailing_one_year_growth

DEFAULT_RATES = [0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08]
DEFAULT_GROWTHS = [-0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]
DEFAULT_DOWNS = [0.20, 0.05]

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


def advantage_grid(
    price0: float,
    rent0: float,
    a: Assumptions,
    rates: list[float],
    growths: list[float],
    down_share: float | None = None,
) -> list[list[float]]:
    """Rows are mortgage rates, columns are annual price growth rates."""
    grid = []
    for rate in rates:
        scenario = replace(a, mortgage_rate=rate)
        grid.append(
            [
                compare_rent_vs_buy(price0, rent0, g, scenario, down_share)["buy_advantage"]
                for g in growths
            ]
        )
    return grid


def break_even_by_rate(
    price0: float,
    rent0: float,
    a: Assumptions,
    rates: list[float],
    down_share: float | None = None,
) -> dict[float, float | None]:
    return {
        rate: break_even_growth(price0, rent0, replace(a, mortgage_rate=rate), down_share)
        for rate in rates
    }


def write_grid_csv(path: Path, rates: list[float], growths: list[float], grid: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["mortgage_rate"] + [f"growth_{g:+.3f}" for g in growths])
        for rate, row in zip(rates, grid):
            writer.writerow([f"{rate:.4f}"] + [f"{value:.2f}" for value in row])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--acs", type=Path, required=True, help="ACS JSON from fetch_acs.py")
    parser.add_argument("--fhfa", type=Path, required=True, help="FHFA JSON from fetch_fhfa.py")
    args = parser.parse_args(argv)

    acs = json.loads(args.acs.read_text())
    growth = trailing_one_year_growth(json.loads(args.fhfa.read_text())["rows"])
    a = Assumptions(mortgage_rate=DEFAULT_RATES[0])
    area = args.acs.stem.replace("acs_", "")

    for down in DEFAULT_DOWNS:
        grid = advantage_grid(
            acs["median_home_value"], acs["median_gross_rent"], a, DEFAULT_RATES, DEFAULT_GROWTHS, down
        )
        out = PROCESSED_DIR / f"sensitivity_{area}_down{round(down * 100)}.csv"
        write_grid_csv(out, DEFAULT_RATES, DEFAULT_GROWTHS, grid)
        print(f"Wrote {out}")

    print(f"Trailing FHFA growth: {growth:.2%}")
    for down in DEFAULT_DOWNS:
        be = break_even_by_rate(acs["median_home_value"], acs["median_gross_rent"], a, DEFAULT_RATES, down)
        print(f"\nBreak-even growth at {down:.0%} down:")
        for rate, g in be.items():
            text = f"{g:.2%}" if g is not None else "outside -10% to +20%"
            print(f"  rate {rate:.2%}: {text}")


if __name__ == "__main__":
    main()
