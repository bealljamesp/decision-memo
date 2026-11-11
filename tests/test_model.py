import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model import (  # noqa: E402
    Assumptions,
    balance_after,
    break_even_growth,
    compare_rent_vs_buy,
    monthly_payment,
    trailing_one_year_growth,
)


def test_monthly_payment_matches_standard_table():
    # $100,000 at 6% for 30 years is about $599.55 a month.
    assert monthly_payment(100_000, 0.06, 30) == pytest.approx(599.55, abs=0.01)


def test_balance_reaches_zero_at_term():
    assert balance_after(100_000, 0.06, 30, 360) == pytest.approx(0.0, abs=1e-6)


def test_higher_growth_favors_buying():
    a = Assumptions(mortgage_rate=0.065)
    low = compare_rent_vs_buy(800_000, 2_000, 0.00, a)["buy_advantage"]
    high = compare_rent_vs_buy(800_000, 2_000, 0.06, a)["buy_advantage"]
    assert high > low


def test_break_even_growth_zeroes_the_advantage():
    a = Assumptions(mortgage_rate=0.065)
    g = break_even_growth(800_000, 2_000, a)
    assert g is not None
    assert compare_rent_vs_buy(800_000, 2_000, g, a)["buy_advantage"] == pytest.approx(0.0, abs=1.0)


def test_break_even_returns_none_when_no_sign_change():
    # Renting is so cheap relative to the price that buying loses across the whole range.
    a = Assumptions(mortgage_rate=0.30)
    assert break_even_growth(800_000, 500, a) is None


def test_affordability_flag_uses_income_ratio():
    a = Assumptions(mortgage_rate=0.065, income=120_000)
    result = compare_rent_vs_buy(200_000, 2_000, 0.03, a)
    assert result["affordable"] is True
    result = compare_rent_vs_buy(3_000_000, 2_000, 0.03, a)
    assert result["affordable"] is False


def test_small_down_payment_costs_more_monthly_pmi():
    a = Assumptions(mortgage_rate=0.065)
    twenty = compare_rent_vs_buy(800_000, 2_000, 0.03, a, down_share=0.20)
    five = compare_rent_vs_buy(800_000, 2_000, 0.03, a, down_share=0.05)
    assert five["owner_cost_ratio"] > twenty["owner_cost_ratio"]


def test_trailing_growth_uses_four_quarters_back():
    rows = [
        {"year": 2025, "quarter": q, "index_sa": 100.0, "index_nsa": None} for q in (1, 2, 3, 4)
    ] + [{"year": 2026, "quarter": 1, "index_sa": 110.0, "index_nsa": None}]
    assert trailing_one_year_growth(rows) == pytest.approx(0.10)


def test_trailing_growth_needs_five_quarters():
    with pytest.raises(ValueError):
        trailing_one_year_growth([{"year": 2026, "quarter": 1, "index_sa": 100.0, "index_nsa": None}])
