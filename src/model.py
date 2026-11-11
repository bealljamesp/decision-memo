"""Five-year rent-vs-buy comparison for one metro.

Both paths start with the same cash: the down payment and closing costs the buyer would
pay are invested by the renter. Each month the renter invests (or withdraws) the
difference between the owner's cash cost and the rent. At the horizon:

    renter wealth = invested starting cash and monthly differences, compounded
    owner wealth  = net sale proceeds minus the remaining loan balance

buy_advantage = owner wealth - renter wealth. Positive means buying comes out ahead.

Usage:
    python src/model.py --mortgage-rate 0.065 \
        --acs data/raw/acs_2024_06037.json --fhfa data/raw/fhfa_hpi_31084.json

Every cost rate in Assumptions is a labeled assumption, not a sourced figure.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Assumptions:
    mortgage_rate: float  # annual, required: take it from Freddie Mac PMMS
    income: float = 120_000.0
    down_share: float = 0.20
    term_years: int = 30
    property_tax_rate: float = 0.011  # share of home value per year (assumption)
    insurance_rate: float = 0.0035  # share of home value per year (assumption)
    maintenance_rate: float = 0.01  # share of home value per year (assumption)
    closing_rate: float = 0.03  # buyer closing costs, share of price (assumption)
    selling_rate: float = 0.06  # seller costs at sale, share of price (assumption)
    pmi_rate: float = 0.0075  # annual, applied while down payment is under 20% (assumption)
    rent_growth: float = 0.03  # annual (assumption)
    invest_return: float = 0.045  # annual return on invested cash (assumption)
    horizon_years: int = 5
    affordability_ratio: float = 0.28  # housing cost as share of gross monthly income (rule of thumb)


def monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    n = years * 12
    r = annual_rate / 12
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def balance_after(principal: float, annual_rate: float, years: int, months_paid: int) -> float:
    r = annual_rate / 12
    pay = monthly_payment(principal, annual_rate, years)
    balance = principal
    for _ in range(months_paid):
        balance = balance * (1 + r) - pay
    return balance


def compare_rent_vs_buy(
    price0: float,
    rent0: float,
    growth: float,
    a: Assumptions,
    down_share: float | None = None,
) -> dict:
    """Compare renting with buying at a given down payment share.

    price0: current median home value. rent0: current median gross rent.
    growth: annual home price growth, for example from the FHFA index.
    """
    down = a.down_share if down_share is None else down_share
    months = a.horizon_years * 12
    loan0 = price0 * (1 - down)
    pay = monthly_payment(loan0, a.mortgage_rate, a.term_years)
    pmi_m = loan0 * a.pmi_rate / 12 if down < 0.20 else 0.0
    starting_cash = price0 * down + price0 * a.closing_rate
    r_m = a.invest_return / 12

    renter = starting_cash
    balance = loan0
    first_owner_cash = None
    first_rent = rent0
    for t in range(1, months + 1):
        price_t = price0 * (1 + growth) ** (t / 12)
        rent_t = rent0 * (1 + a.rent_growth) ** ((t - 1) / 12)
        interest = balance * a.mortgage_rate / 12
        balance -= pay - interest
        owner_cash = pay + pmi_m + price_t * (a.property_tax_rate + a.insurance_rate + a.maintenance_rate) / 12
        if t == 1:
            first_owner_cash = owner_cash
        renter = renter * (1 + r_m) + (owner_cash - rent_t)

    price_n = price0 * (1 + growth) ** (months / 12)
    owner_wealth = price_n * (1 - a.selling_rate) - balance
    monthly_income = a.income / 12
    return {
        "down_share": down,
        "owner_wealth": owner_wealth,
        "renter_wealth": renter,
        "buy_advantage": owner_wealth - renter,
        "owner_first_month_cost": first_owner_cash,
        "owner_cost_ratio": first_owner_cash / monthly_income,
        "renter_first_month_cost": first_rent,
        "affordable": first_owner_cash / monthly_income <= a.affordability_ratio,
    }


def break_even_growth(price0: float, rent0: float, a: Assumptions, down_share: float | None = None) -> float | None:
    """Annual price growth at which buying and renting leave the household equally well off.

    Returns None if the advantage doesn't change sign between -10% and +20% growth.
    """
    def advantage(g: float) -> float:
        return compare_rent_vs_buy(price0, rent0, g, a, down_share)["buy_advantage"]

    lo, hi = -0.10, 0.20
    f_lo, f_hi = advantage(lo), advantage(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        f_mid = advantage(mid)
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def trailing_one_year_growth(rows: list[dict]) -> float:
    """Growth over the last four quarters, from FHFA rows with year, quarter, and index values."""
    if len(rows) < 5:
        raise ValueError("need at least five quarters to compute one-year growth")
    latest, year_ago = rows[-1], rows[-5]
    key = "index_sa" if latest.get("index_sa") is not None else "index_nsa"
    return latest[key] / year_ago[key] - 1


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mortgage-rate", type=float, required=True, help="annual rate, e.g. 0.065")
    parser.add_argument("--acs", type=Path, required=True, help="ACS JSON from fetch_acs.py")
    parser.add_argument("--fhfa", type=Path, required=True, help="FHFA JSON from fetch_fhfa.py")
    args = parser.parse_args(argv)

    acs = _load(args.acs)
    growth = trailing_one_year_growth(_load(args.fhfa)["rows"])
    a = Assumptions(mortgage_rate=args.mortgage_rate)

    print(f"Area: {acs['name']}")
    print(f"Starting median value ${acs['median_home_value']:,.0f}, median rent ${acs['median_gross_rent']:,.0f}")
    print(f"Trailing one-year price growth (FHFA): {growth:.2%}")
    for down in (0.20, 0.05):
        result = compare_rent_vs_buy(acs["median_home_value"], acs["median_gross_rent"], growth, a, down)
        be = break_even_growth(acs["median_home_value"], acs["median_gross_rent"], a, down)
        be_text = f"{be:.2%}" if be is not None else "outside -10% to +20%"
        print(
            f"\n{down:.0%} down: buy advantage ${result['buy_advantage']:,.0f} over five years; "
            f"break-even growth {be_text}; "
            f"first-month owner cost ${result['owner_first_month_cost']:,.0f} "
            f"({result['owner_cost_ratio']:.0%} of gross income), affordable: {result['affordable']}"
        )


if __name__ == "__main__":
    main()
