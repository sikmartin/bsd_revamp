"""
bsd — Czech UGS storage sizing analysis toolkit.

Public API (import from `bsd` directly)
-----------------------------------------
Constants
    CAPACITY_TWH, MONTH_ORDER, MONTH_NAMES, DAYS_IN_MONTH,
    STRESS_PEAK_DAYS, STRESS_RESIDUAL_DAYS

Scenarios
    Scenario, DEFAULT_SCENARIOS, DEFAULT_SCENARIOS_DICT

Data loaders
    load_storage_gie

Demand
    DemandProfile, load_demand_profile, demand_profile_table

Imports
    compute_monthly_imports, compute_import_benchmarks, import_table

Withdrawal curves
    WcCurves, fit_withdrawal_curves

Branch 1 — Monthly obligations
    simulate_month, min_start_fill_month, run_all_months, obligations_table

Branch 2 — Season fill target
    build_day_series, simulate, min_start_fill, run_all_scenarios, sensitivity_table

Modules (accessible as bsd.data, bsd.jvs, etc.)
-------------------------------------------------
data       Load and clean ENTSOG / GIE data files.
jvs        Czech-authority chart styling and colour palettes.
plot       Plot helpers (extended in Phase 2+).
"""

# -- constants ----------------------------------------------------------------
from .constants import (
    CAPACITY_TWH,
    CAPACITY_GWH,
    MONTH_ORDER,
    MONTH_NAMES,
    DAYS_IN_MONTH,
    STRESS_PEAK_DAYS,
    STRESS_RESIDUAL_DAYS,
    WINTER_MONTHS,
    GAS_STORAGE_LEVY_START,
    GAS_STORAGE_LEVY_END,
    END_OF_SEASON_FLOOR_TWH,
)

# -- scenarios ----------------------------------------------------------------
from .scenarios import Scenario, DEFAULT_SCENARIOS, DEFAULT_SCENARIOS_DICT

# -- demand -------------------------------------------------------------------
from .demand import DemandProfile, load_demand_profile, demand_profile_table

# -- imports ------------------------------------------------------------------
from .imports import compute_monthly_imports, compute_import_benchmarks, import_table

# -- data loaders -------------------------------------------------------------
from .data import load_storage_gie

# -- withdrawal curves --------------------------------------------------------
from .withdrawal import WcCurves, fit_withdrawal_curves

# -- branch 1: monthly obligations -------------------------------------------
from .obligations import (
    simulate_month,
    min_start_fill_month,
    run_all_months,
    obligations_table,
)

# -- branch 2: season fill target --------------------------------------------
from .target import (
    build_day_series,
    simulate,
    min_start_fill,
    run_all_scenarios,
    sensitivity_table,
)

# -- sub-modules (kept accessible) -------------------------------------------
from . import jvs, data, plot

__all__ = [
    # constants
    "CAPACITY_TWH", "CAPACITY_GWH", "MONTH_ORDER", "MONTH_NAMES",
    "DAYS_IN_MONTH", "STRESS_PEAK_DAYS", "STRESS_RESIDUAL_DAYS", "WINTER_MONTHS",
    "END_OF_SEASON_FLOOR_TWH",
    # scenarios
    "Scenario", "DEFAULT_SCENARIOS", "DEFAULT_SCENARIOS_DICT",
    # demand
    "DemandProfile", "load_demand_profile", "demand_profile_table",
    # data loaders
    "load_storage_gie",
    # imports
    "compute_monthly_imports", "compute_import_benchmarks", "import_table",
    # withdrawal
    "WcCurves", "fit_withdrawal_curves",
    # branch 1
    "simulate_month", "min_start_fill_month", "run_all_months", "obligations_table",
    # branch 2
    "build_day_series", "simulate", "min_start_fill", "run_all_scenarios", "sensitivity_table",
    # modules
    "jvs", "data", "plot",
]
