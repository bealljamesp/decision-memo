# decision-memo

A portfolio project: a decision memo that frames a decision, weighs options with public data, and recommends one.

**Status:** Los Angeles County is modeled and drafted in `memo/memo.md`, using the Freddie Mac rate for the week of November 5, 2026 (7.18%). The memo is a draft. Washington DC, Chicago, and New York are not started.

## Decision question

Over a five-year horizon, should a household earning $120,000 a year in a given metro rent a comparable home or buy one?

- **Options:** (A) rent a comparable unit; (B) buy at the metro's median price with 20% down; (C) buy with 5% down, which adds mortgage insurance and a higher rate.
- **Criteria:** net cost over five years, cash needed up front, sensitivity to rates and price growth, and flexibility if the household has to move.
- **Recommendation:** choose one option per metro, state the break-even conditions, and show how the answer changes under plausible ranges.

## Result so far (Los Angeles County)

At 7.18%, renting comes out ahead by about $378,000 over five years with 20% down, and about $431,000 with 5% down. Buying would need about 8.4% a year price growth (20% down) to break even, against trailing growth of 0.02%. Details and limitations are in the memo.

## Assumptions

- Household: $120,000 gross income, with an affordability check on the monthly housing payment. The same household applies in every metro.
- Financing: 30-year fixed mortgage. Closing and selling costs, property tax, insurance, maintenance, and rent growth are labeled assumptions.
- Mortgage rates come from Freddie Mac's Primary Mortgage Market Survey, which is national. Every metro uses the same rate series.

## Data

- **ACS (Census):** median home value and median gross rent by county.
- **FHFA House Price Index:** purchase-only quarterly price trends by metropolitan division.
- **Freddie Mac PMMS:** weekly mortgage rates. `src/fetch_rates.py` reads the latest 30-year rate.

## Metros and geographies

Each metro uses one geography for both sources, so the price trend and the home value describe the same area.

| Metro | FHFA index (MSAD) | ACS geography |
|---|---|---|
| Los Angeles | 31084, Los Angeles-Long Beach-Glendale | County 06037 (LA County) |
| Washington, DC | TBD | TBD |
| Chicago | 16984, Chicago-Naperville-Evanston (MSAD) | TBD |
| New York | TBD | TBD |

FHFA publishes the large metros as metropolitan divisions, so its IDs don't match the CBSA codes. The Chicago division ID above is from FHFA's series list, not the CBSA code (16980). Confirm each ID and county list against the Census delineation file before use. `config/metros.yaml` holds the same table.

## Structure

```
decision-memo/
├── README.md
├── config/
│   ├── household.yaml      # income, down payments, loan terms, rate, labeled assumptions (documentation; not read by code yet)
│   └── metros.yaml         # metro geographies (documentation; not read by code yet)
├── data/
│   ├── raw/                # downloads, gitignored
│   └── processed/          # sensitivity grids
├── src/
│   ├── fetch_acs.py        # ACS median value and rent
│   ├── fetch_fhfa.py       # FHFA metro price index
│   ├── fetch_rates.py      # latest Freddie Mac 30-year rate
│   ├── model.py            # rent vs buy cost model
│   ├── sensitivity.py
│   └── figures.py
├── tests/
│   ├── test_fetch_acs.py
│   ├── test_fetch_fhfa.py
│   ├── test_fetch_rates.py
│   ├── test_model.py
│   └── test_sensitivity.py
└── memo/
    ├── memo.md
    └── figures/
```

The model and figure scripts take the mortgage rate and file paths as command-line arguments. `config/` is not read yet. Wiring it in is a follow-up.

## Known gaps

- `fetch_rates.py` parses a PMMS history CSV and is covered by tests on a fixture. It has not been run against the live Freddie Mac file.
- The memo's Los Angeles inputs (ACS values and the FHFA growth figure) are stated in the memo. Re-fetch them with the scripts above before the memo is published.
- The DC, Chicago, and New York metros are not modeled.

## Memo outline

1. Recommendation, with break-even conditions
2. Decision question, options, and criteria
3. Data and assumptions, with sources
4. Base-case results by metro
5. Sensitivity: what would change the answer
6. Limitations
7. Appendix: data details and the affordability calculation

Figures: (1) five-year net cost by option for each metro; (2) break-even heatmap of price growth against mortgage rate.

## Stack

Python, with requests for the Census, FHFA, and Freddie Mac downloads, and matplotlib for figures. Tests run with pytest.
