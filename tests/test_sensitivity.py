import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model import Assumptions, compare_rent_vs_buy  # noqa: E402
from sensitivity import advantage_grid, break_even_by_rate  # noqa: E402

RATES = [0.05, 0.07]
GROWTHS = [0.0, 0.05]


def test_grid_shape_matches_inputs():
    a = Assumptions(mortgage_rate=0.06)
    grid = advantage_grid(800_000, 2_000, a, RATES, GROWTHS)
    assert len(grid) == len(RATES)
    assert all(len(row) == len(GROWTHS) for row in grid)


def test_grid_cell_matches_direct_comparison():
    a = Assumptions(mortgage_rate=0.06)
    grid = advantage_grid(800_000, 2_000, a, RATES, GROWTHS, down_share=0.20)
    direct = compare_rent_vs_buy(800_000, 2_000, 0.05, replace(a, mortgage_rate=0.07), 0.20)
    assert grid[1][1] == direct["buy_advantage"]


def test_higher_rate_lowers_buy_advantage():
    a = Assumptions(mortgage_rate=0.06)
    grid = advantage_grid(800_000, 2_000, a, RATES, GROWTHS)
    assert grid[1][0] < grid[0][0]


def test_break_even_by_rate_has_one_entry_per_rate():
    a = Assumptions(mortgage_rate=0.06)
    result = break_even_by_rate(800_000, 2_000, a, RATES)
    assert set(result) == set(RATES)
