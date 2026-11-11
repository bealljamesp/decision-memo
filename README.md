# decision-memo

A portfolio project: a decision memo that frames a decision, weighs options with public data, and recommends one.

**Status:** scoping. No code yet.

## Decision question

Over a five-year horizon, should a household earning $120,000 a year in a given metro rent a comparable home or buy one?

- **Options:** (A) rent a comparable unit; (B) buy at the metro's median price with 20% down; (C) buy with 5% down, which adds mortgage insurance and a higher rate.
- **Criteria:** net cost over five years, cash needed up front, sensitivity to rates and price growth, and flexibility if the household has to move.
- **Recommendation:** choose one option per metro, state the break-even conditions, and show how the answer changes under plausible ranges.

## Assumptions

- Household: $120,000 gross income, with an affordability check on the monthly housing payment. The same household applies in every metro.
- Financing: 30-year fixed mortgage. Closing and selling costs, property tax, insurance, maintenance, and rent growth are labeled assumptions.
- Mortgage rates come from Freddie Mac's Primary Mortgage Market Survey, which is national. Every metro uses the same rate series.

## Data

- **ACS (Census):** median home value and median gross rent by metro.
- **FHFA House Price Index:** metro price trends for the appreciation assumption.
- **Freddie Mac PMMS:** weekly mortgage rates.

## Metros

| Metro | CBSA code |
|---|---|
| Los Angeles-Long Beach-Anaheim | 31080 |
| Washington-Arlington-Alexandria | 47900 |
| Chicago-Naperville-Elgin | 16980 |
| New York-Newark-Jersey City | 35620 |

Verify these codes against the Census delineation file before use.

## Planned structure

```
decision-memo/
├── README.md
├── config/
│   ├── household.yaml      # income, down payment, loan terms
│   └── metros.yaml         # CBSA codes and names
├── data/
│   ├── raw/                # downloads, gitignored
│   └── processed/
├── src/
│   ├── fetch_acs.py
│   ├── fetch_fhfa.py
│   ├── fetch_rates.py
│   ├── model.py            # rent vs buy cost model
│   ├── sensitivity.py
│   └── figures.py
├── tests/
│   └── test_model.py
└── memo/
    ├── memo.md
    └── figures/
```

## Memo outline

1. Recommendation, with break-even conditions
2. Decision question, options, and criteria
3. Data and assumptions, with sources
4. Base-case results by metro
5. Sensitivity: what would change the answer
6. Limitations
7. Appendix: data details and the affordability calculation

Figures: (1) five-year net cost by option for each metro; (2) break-even heatmap of price growth against mortgage rate.

## Plan (three weekends)

- **Weekend 1:** config, the LA data pipeline, and the core cost model with tests.
- **Weekend 2:** sensitivity analysis, the other three metros, and both figures.
- **Weekend 3:** memo writing, the recommendation, and README cleanup.

## Stack

Python, with pandas for data work, requests for the Census API, and matplotlib for figures.
