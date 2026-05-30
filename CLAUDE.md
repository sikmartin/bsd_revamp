
# Project conventions

## Commands
- Run: `uv run python -c`

## Rules
- Always use uv to execute Python (including ipython, jupyter) code

# Project scope

**Name**
Czech Gas Import Capacity — Storage Sizing Analysis

**Purpose**  
This project estimates the level of gas imports into the Czech balancing zone
that can reliably be counted on during winter, at several risk-level scenarios.
The results are an input into a discussion about how much working gas needs to be
held in Czech underground storage (UGS) facilities so that a 1-in-20 cold-winter
demand event can be met even when imports fall short.

**Modeling structure**

Two branches, each implemented in its own notebook:

1. **Branch 1 — Monthly obligations** (`notebooks/storage_obligations.ipynb`)  
   Deterministic model for regulatory use. Sets the minimum gas-in-storage volume that regulated suppliers must hold at the start of each heating-season month (Oct–Mar), per EU Regulation 2017/1938 Art. 6. Uses a two-tier demand profile (7-day peak `R.max.den` + 23-day residual from `r_30dnu`) and month-specific import percentiles. Monthly stress tests are independent (once-per-season event framing). A separate ~0.5 TWh end-of-March operational floor is recommended as a standalone instrument.

2. **Branch 2 — Season-long fill target** (`notebooks/storage_target.ipynb`)  
   Deterministic simulation finding the minimum 1-October fill level such that a 1-in-20 winter can be survived across the full Oct–Mar season. Currently uses fixed monthly import percentiles. Planned extensions (deferred): stochastic import draws and summer injection feasibility check.

**Model framing**

```
Peak demand (1-in-20, exogenous)
       │
       ├─── covered by reliable imports  ←── this notebook sizes this
       │
       └─── covered by UGS withdrawal    ←── subsequent exercise
```

**Data source**  
ENTSOG Transparency Platform — Aggregated Data export for the Czech balancing
zone (operator NET4GAS), all entry directions, daily granularity.

**Key analytical decision: Physical Flows, post-March 2022 only**  
See Section 2 for the detailed rationale.  In brief:
- Physical Flows record what physically crossed the border; Allocations record
  commercial settlements.  For capacity reliability the physical record is more
  direct.
- Pre-2022 data reflects Russian transit volumes and the 2021 storage-filling
  frenzy — structurally different from today's market.  Using it would
  overstate available import capacity.