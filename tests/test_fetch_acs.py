import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fetch_acs import CBSA_FIELD, VARIABLES, build_params, parse_acs_response  # noqa: E402

HEADER = ["NAME", "B25077_001E", "B25064_001E", CBSA_FIELD]


def test_parse_returns_flat_record_with_geography():
    rows = [HEADER, ["Test Metro Area", "100000", "1500", "99999"]]
    record = parse_acs_response(rows)
    assert record["name"] == "Test Metro Area"
    assert record["geography"] == {CBSA_FIELD: "99999"}
    assert record["median_home_value"] == 100000.0
    assert record["median_gross_rent"] == 1500.0


def test_county_geography_fields_are_kept():
    header = ["NAME", "B25077_001E", "B25064_001E", "state", "county"]
    rows = [header, ["Test County", "100000", "1500", "06", "037"]]
    record = parse_acs_response(rows)
    assert record["geography"] == {"state": "06", "county": "037"}


def test_negative_sentinel_becomes_none():
    # Census uses large negative values to flag estimates that are unavailable.
    rows = [HEADER, ["Test Metro Area", "-666666666", "1500", "99999"]]
    record = parse_acs_response(rows)
    assert record["median_home_value"] is None
    assert record["median_gross_rent"] == 1500.0


def test_missing_variable_becomes_none():
    rows = [["NAME", "B25077_001E", CBSA_FIELD], ["Test Metro Area", "100000", "99999"]]
    record = parse_acs_response(rows)
    assert record["median_gross_rent"] is None


def test_wrong_row_count_raises():
    with pytest.raises(ValueError):
        parse_acs_response([HEADER])


def test_build_params_for_cbsa():
    params = build_params("abc123", cbsa="31080")
    assert params["key"] == "abc123"
    assert params["for"] == f"{CBSA_FIELD}:31080"
    assert "in" not in params
    assert params["get"].split(",") == ["NAME", *VARIABLES]


def test_build_params_for_county_splits_state_and_county():
    params = build_params("abc123", county_fips="06037")
    assert params["for"] == "county:037"
    assert params["in"] == "state:06"


def test_build_params_requires_exactly_one_geography():
    with pytest.raises(ValueError):
        build_params("abc123")
    with pytest.raises(ValueError):
        build_params("abc123", cbsa="31080", county_fips="06037")


def test_build_params_rejects_malformed_county_fips():
    with pytest.raises(ValueError):
        build_params("abc123", county_fips="6037")
