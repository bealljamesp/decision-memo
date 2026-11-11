import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fetch_fhfa import select_metro_rows  # noqa: E402

HEADER = "hpi_type,hpi_flavor,frequency,level,place_name,place_id,yr,period,index_nsa,index_sa"

# Fixture rows only: they follow the documented column layout but are not real FHFA values.
FIXTURE = "\n".join(
    [
        HEADER,
        "traditional,purchase_only,quarterly,MSA,Test Metro A,31080,2024,2,100.0,99.5",
        "traditional,purchase_only,quarterly,MSA,Test Metro A,31080,2024,1,99.0,98.5",
        "traditional,purchase_only,quarterly,MSA,Test Metro B,47900,2024,1,50.0,50.0",
        "traditional,all_transactions,quarterly,MSA,Test Metro A,31080,2024,1,77.0,77.0",
        "traditional,purchase_only,annual,MSA,Test Metro A,31080,2024,4,101.0,101.0",
        "traditional,purchase_only,quarterly,Divisions,Test Division,31080,2024,3,88.0,88.0",
        "traditional,purchase_only,quarterly,MSA,Test Metro A,31080,2023,4,,",
    ]
)


def test_keeps_only_matching_metro_rows_sorted_oldest_first():
    rows = select_metro_rows(FIXTURE.splitlines(), "31080")
    assert [(r["year"], r["quarter"]) for r in rows] == [(2023, 4), (2024, 1), (2024, 2)]


def test_values_parse_and_blanks_become_none():
    rows = select_metro_rows(FIXTURE.splitlines(), "31080")
    assert rows[0]["index_nsa"] is None and rows[0]["index_sa"] is None
    assert rows[2] == {"year": 2024, "quarter": 2, "index_nsa": 100.0, "index_sa": 99.5}


def test_other_cbsa_returns_empty_list():
    assert select_metro_rows(FIXTURE.splitlines(), "99999") == []


def test_missing_required_column_raises():
    bad = "hpi_type,hpi_flavor,frequency,level,place_id,yr,period,index_nsa\n"
    with pytest.raises(ValueError, match="index_sa"):
        select_metro_rows(bad.splitlines(), "31080")
