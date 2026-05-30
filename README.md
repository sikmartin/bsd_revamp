# Czech Gas Import Capacity — Storage Sizing Analysis

Estimates the gas import capacity the Czech balancing zone can reliably count on
during winter, and derives how much working gas must be held in Czech underground
storage (UGS) facilities to survive a 1-in-20 cold-winter demand event when imports
fall short.

## Two-branch model structure

```
Peak demand (1-in-20, exogenous)
       │
       ├─── covered by reliable imports  ←── sized by import percentile scenarios
       │
       └─── covered by UGS withdrawal    ←── sized by the two branches below
```

| Branch | Notebook | What it answers |
|---|---|---|
| **Branch 1 — Monthly obligations** | `notebooks/storage_obligations.ipynb` | Minimum fill at the *start of each month* (Oct–Mar) per EU Reg. 2017/1938 Art. 6 |
| **Branch 2 — Season fill target** | `notebooks/storage_target.ipynb` | Minimum fill on *1 October* to survive the full Oct–Mar season |

## Quick start

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Execute both analysis notebooks (regenerates figs/)
uv run jupyter nbconvert --to notebook --execute notebooks/storage_obligations.ipynb
uv run jupyter nbconvert --to notebook --execute notebooks/storage_target.ipynb

# Launch the interactive Streamlit app
uv run streamlit run app/app.py
```

## Directory guide

```
app/           Streamlit interactive explorer (Czech-language UI)
bsd/           Python library — all analytical logic lives here
  constants.py   Project-wide constants (CAPACITY_TWH, MONTH_ORDER, …)
  scenarios.py   Scenario dataclass + DEFAULT_SCENARIOS (S1–S5)
  demand.py      Demand profile loader (peak + residual from r_max_den / r_30dnu)
  imports.py     Monthly import percentiles + P99 cold-day benchmark
  withdrawal.py  WC curve fitting (empirical P95, ENTSOG engineering, blends)
  obligations.py Branch 1 simulation engine
  target.py      Branch 2 simulation engine
  data.py        ENTSOG / GIE data loaders (nailed-down)
  jvs.py         Czech-authority chart styling and colour palettes
  plot.py        Plot helpers
  capacity.py    LEGACY flat model — superseded; kept for historical reference
data/          Input files (ENTSOG Physical Flows, GIE storage, demand profiles)
docs/          Methodology, results, architecture, and decision records
figs/          Generated charts (reproducible by running the notebooks)
notebooks/     Analysis notebooks (thin clients that import from bsd/)
  storage_obligations.ipynb   Branch 1 narrative + charts
  storage_target.ipynb        Branch 2 narrative + charts
  analysis.ipynb              Preparatory analysis (provenance only)
  storage_monthly.ipynb       Preparatory analysis (provenance only)
  withdrawal_curve.ipynb      Preparatory analysis (provenance only)
presentation/  Czech-language PowerPoint deck + build script
tests/         Pytest suite (unit + regression)
```

## Key results (S2 planning anchor)

| Metric | Value |
|---|---|
| Jan obligation (Branch 1, S2) | **9.33 TWh** |
| 1-Oct fill target (Branch 2, S2) | **21.9 TWh** (~48% of capacity) |
| Czech UGS working-gas capacity | **45.3 TWh** |
| Binding constraint (B2 S1) | Withdrawal rate |
| Binding constraint (B2 S2–S5) | Volume |

See `docs/storage_obligations_results.md` and `docs/storage_target_results.md`
for full scenario tables, sensitivity analyses, and caveats.

## Data source

ENTSOG Transparency Platform — Aggregated Data export for the Czech balancing
zone (operator NET4GAS), Physical Flows, all entry directions, daily granularity,
post-March 2022 only (pre-2022 data includes Russian transit volumes and the 2021
storage-filling frenzy — structurally different from today's market).

## Running tests

```bash
uv run pytest                 # all 98 tests
uv run pytest tests/test_obligations.py -v   # Branch 1 unit tests
uv run pytest tests/test_target.py -v        # Branch 2 unit tests
```
