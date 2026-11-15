import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fetch_rates import latest_30yr  # noqa: E402

FIXTURE = [
    "Date,30Y Rate,15Y Rate",
    "2026-10-22,7.32,6.82",
    "2026-10-29,7.24,6.60",
    "2026-11-05,7.18,6.57",
    "2026-10-15,,6.50",
]


def test_returns_latest_30yr_rate_as_decimal():
    result = latest_30yr(FIXTURE)
    assert result["date"] == "2026-11-05"
    assert result["rate"] == pytest.approx(0.0718)


def test_ignores_blank_rate_rows_and_unsorted_input():
    shuffled = [FIXTURE[0], FIXTURE[3], FIXTURE[2], FIXTURE[1]]
    assert latest_30yr(shuffled)["date"] == "2026-11-05"


def test_accepts_slash_dates():
    lines = ["Week,30-Year Fixed Rate", "11/05/2026,7.18", "10/29/2026,7.24"]
    assert latest_30yr(lines)["date"] == "2026-11-05"


def test_raises_when_no_30yr_column():
    with pytest.raises(ValueError):
        latest_30yr(["Date,15Y Rate", "2026-11-05,6.57"])


def test_raises_when_no_readings():
    with pytest.raises(ValueError):
        latest_30yr(["Date,30Y Rate", "2026-11-05,"])
