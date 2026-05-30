# Architecture — Czech UGS Storage Sizing Package

## Module map

```
bsd/
  constants.py    Project-wide literals (CAPACITY_TWH, MONTH_ORDER, stress-period params)
  scenarios.py    Scenario dataclass; DEFAULT_SCENARIOS (S1–S5) with jvs colours
  data.py         ENTSOG / GIE CSV loaders (nailed-down; minor changes only)
  demand.py       load_demand_profile() → DemandProfile(peak, residual, total)
  imports.py      compute_monthly_imports() / compute_p99_imports()
  withdrawal.py   fit_withdrawal_curves() → WcCurves; .blend(eng_weight) factory
  obligations.py  Branch 1: simulate_month / min_start_fill_month / run_all_months
  target.py       Branch 2: build_day_series / simulate / min_start_fill /
                             run_all_scenarios / sensitivity_table
  jvs.py          Czech-authority chart styling; PALETTES["scenarios"] colour ramp
  plot.py         Shared plot helpers
  capacity.py     LEGACY flat model — superseded; retained for test coverage
  __init__.py     Public API re-export (all symbols importable from `bsd` directly)
```

## Data flow

```
data/
  cz_gas_imports_2020-2026.csv          ─┐
  StorageData_GIE_2011-01-01_…csv       ─┼─▶  bsd.data  ──▶  bsd.withdrawal
  cz_usg_withdrawal_curve_2025.csv      ─┘                        │
                                                                   │ WcCurves
  r_max_den_2025-2026.csv  ─┐                                     │
  r_30dnu_2025-2026.csv    ─┴─▶  bsd.demand  ─▶  DemandProfile   │
                                                       │           │
  cz_gas_imports_2020-2026.csv                         │           │
  StorageData_GIE_2011-01-01_…csv  ──▶  bsd.imports   │           │
                                             │          │           │
                                             ▼          ▼           ▼
                                         monthly_imports  +  wc_func
                                                    │
                              ┌─────────────────────┴──────────────────────┐
                              ▼                                             ▼
                    bsd.obligations (Branch 1)                  bsd.target (Branch 2)
                    simulate_month / bisect                      simulate / bisect
                              │                                             │
                              ▼                                             ▼
                      monthly TWh table                          1-Oct fill target
                      (obligations_table)                        (run_all_scenarios)
                              │                                             │
                         bsd.plot / jvs                              bsd.plot / jvs
                              │                                             │
                    ┌─────────┴──────────────────────────────────────────┐
                    ▼                                                     ▼
            app/app.py (Streamlit)                   presentation/ (.pptx build script)
            notebooks/storage_obligations.ipynb      notebooks/storage_target.ipynb
```

## Public API surface

All symbols below are importable directly from `bsd`:

### Constants
| Symbol | Description |
|---|---|
| `CAPACITY_TWH` | Czech UGS total working-gas capacity (45.3034 TWh) |
| `MONTH_ORDER` | `[10, 11, 12, 1, 2, 3]` (Oct → Mar) |
| `MONTH_NAMES` | `{10: "Oct", …}` |
| `DAYS_IN_MONTH` | Days per month for season simulation |
| `STRESS_PEAK_DAYS` | 7 (days at R.max.den in Branch 1) |
| `STRESS_RESIDUAL_DAYS` | 23 (residual days in Branch 1) |
| `WINTER_MONTHS` | `{10, 11, 12, 1, 2, 3}` |

### Scenarios
| Symbol | Description |
|---|---|
| `Scenario` | Frozen dataclass: `key, label, percentile, color` |
| `DEFAULT_SCENARIOS` | `list[Scenario]` for S1–S5 |
| `DEFAULT_SCENARIOS_DICT` | `dict[str, Scenario]` keyed by `"S1"` … `"S5"` |

### Demand
| Symbol | Signature | Returns |
|---|---|---|
| `load_demand_profile` | `(peak_path, r30_path)` | `DemandProfile(peak, residual, total)` |
| `demand_profile_table` | `(DemandProfile)` | display `pd.DataFrame` |

### Imports
| Symbol | Signature | Returns |
|---|---|---|
| `compute_monthly_imports` | `(scenarios, *, imports_path, cutoff)` | `dict[key → pd.Series]` of GWh/d |
| `compute_p99_imports` | `(*, imports_path, gio_path, cutoff, cold_day_quantile)` | `(p99_cold, p99_uncond)` |
| `import_table` | `(monthly_imports, p99_cold, p99_uncond)` | display `pd.DataFrame` |

### Withdrawal curves
| Symbol | Signature | Returns |
|---|---|---|
| `fit_withdrawal_curves` | `(*, gio_path, eng_path, cutoff, haircut)` | `WcCurves` |
| `WcCurves.blend` | `(eng_weight: float)` | `Callable[[float], float]` |
| `WcCurves.empirical` | — | P95 relative isotonic curve |
| `WcCurves.empirical_abs` | — | P95 absolute isotonic curve (sensitivity use) |
| `WcCurves.engineering` | — | ENTSOG curve with haircut |

Branch defaults: `eng_weight=0.50` (Branch 1), `eng_weight=0.75` (Branch 2).
See `docs/wc_blend_decision.md` for justification.

### Branch 1 — Monthly obligations
| Symbol | Key parameters | Returns |
|---|---|---|
| `simulate_month` | `start_fill_pct, month, imp_GWh_d, wc_func, peak_demand, residual_demand` | `dict(feasible, binding, fill_trajectory, …)` |
| `min_start_fill_month` | same + `tol` | minimum fill % (or `None`) |
| `run_all_months` | `monthly_imports, wc_func, peak_demand, residual_demand, scenarios` | nested `results[key][month]` dict |
| `obligations_table` | `results, scenarios` | display `pd.DataFrame` |

### Branch 2 — Season fill target
| Symbol | Key parameters | Returns |
|---|---|---|
| `build_day_series` | `peak_demand, scenario_imports` | `(months, peaks, imports, gaps)` arrays |
| `simulate` | `start_fill_pct, scenario_key, monthly_imports, wc_func, peak_demand` | `dict(feasible, fill_trajectory, headroom_trajectory, …)` |
| `min_start_fill` | same + `tol` | minimum fill % (or `None`) |
| `run_all_scenarios` | `monthly_imports, wc_func, peak_demand, scenarios` | `results[key]` dict |
| `sensitivity_table` | `scenarios, monthly_imports, wc_func, peak_demand, peak_shifts, wc_abs_func` | `pd.DataFrame` |

## Tracing a number to code

**"S2 Jan obligation 9.33 TWh"**
1. `bsd.compute_monthly_imports(DEFAULT_SCENARIOS_DICT)["S2"][1]` → 135.0 GWh/d import
2. `bsd.fit_withdrawal_curves().blend(0.50)` → `wc_func`
3. `bsd.min_start_fill_month(1, 135.0, wc_func, peak, residual)` → ~20.6%
4. `20.6% × 45.3034 TWh / 100` → **9.33 TWh**

**"S2 season target 21.9 TWh"**
1. `bsd.compute_monthly_imports(DEFAULT_SCENARIOS_DICT)["S2"]` → monthly import Series
2. `bsd.fit_withdrawal_curves().blend(0.75)` → `wc_func`
3. `bsd.min_start_fill("S2", monthly_imports, wc_func, peak_demand)` → ~48.44%
4. `48.44% × 45.3034 TWh / 100` → **21.94 TWh**

## Intended productionisation path

The `bsd` library is designed to be imported from any host:
- **Notebooks** — already thin clients; re-run reproduces all `figs/`.
- **Streamlit app** (`app/app.py`) — calls `bsd` functions live on slider changes.
- **Scheduled batch** — `bsd.load_demand_profile()` and `bsd.compute_monthly_imports()`
  can be wired to auto-updated data files; results written to JSON for downstream use.

The only coupling between modules is through explicit function arguments — no module
globals carry analytical state after `fit_withdrawal_curves()` returns a `WcCurves`
object.
