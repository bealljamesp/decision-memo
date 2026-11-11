import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fetch_acs import GEO_FIELD, VARIABLES, build_params, parse_acs_response  # noqa: E402

HEADER = ["NAME", "B25077_001E", "B25064_001E", GEO_FIELD]


def test_parse_returns_flat_record():
    rows = [HEADER, ["Test Metro Area", "100000", "1500", "99999"]]
    record = parse_acs_response(rows)
    assert record["name"] == "Test Metro Area"
    assert record["cbsa"] == "99999"
    assert record["median_home_value"] == 100000.0
    assert record["median_gross_rent"] == 1500.0


def test_negative_sentinel_becomes_none():
    # Census uses large negative values to flag estimates that are unavailable.
    rows = [HEADER, ["Test Metro Area", "-666666666", "1500", "99999"]]
    record = parse_acs_response(rows)
    assert record["median_home_value"] is None
    assert record["median_gross_rent"] == 1500.0


def test_missing_variable_becomes_none():
    rows = [["NAME", "B25077_001E", GEO_FIELD], ["Test Metro Area", "100000", "99999"]]
    record = parse_acs_response(rows)
    assert record["median_gross_rent"] is None


def test_wrong_row_count_raises():
    with pytest.raises(ValueError):
        parse_acs_response([HEADER])


def test_build_params_targets_cbsa_and_includes_key():
    params = build_params("31080", "abc123")
    assert params["key"] == "abc123"
    assert params["for"] == f"{GEO_FIELD}:31080"
    assert params["get"].split(",") == ["NAME", *VARIABLES]
