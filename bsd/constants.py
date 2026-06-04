"""Project-wide constants for the Czech UGS storage sizing models."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Data file paths — anchored to the package root so they work regardless of
# the process working directory.
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

#: Path to ENTSOG aggregated import data for the Czech balancing zone.
DATA_PATH_IMPORTS = _DATA_DIR / "cz_gas_entry_2020-2026.csv"

#: Path to ENTSOG aggregated export data for the Czech balancing zone.
DATA_PATH_EXPORTS = _DATA_DIR / "cz_gas_exit_2020-2026.csv"

#: Path to month-specific 1-in-20 peak demand data (MWh/d).
DATA_PATH_DEMAND_PEAK = _DATA_DIR / "r_max_den_2025-2026.csv"

#: Path to month-specific 30-day total demand data (MWh).
DATA_PATH_DEMAND_30DAY = _DATA_DIR / "r_30dnu_2025-2026.csv"

#: Path to GIE storage fill-level time series (2011–present).
DATA_PATH_STORAGE_GIE = _DATA_DIR / "StorageData_GIE_2011-01-01_2026-05-28.csv"

#: Path to the ENTSOG winter outlooks and reviews withdrawal and injection curves.
# https://www.entsog.eu/outlooks-reviews#winter-outlooks-and-reviews
DATA_PATH_WTHDRW_CURVE = _DATA_DIR / "cz_usg_withdrawal_curve_2025.csv"
DATA_PATH_INJCTN_CURVE = _DATA_DIR / "cz_usg_injection_curve_2025.csv"

#: Directory for notebook figure output, anchored to the project root so it
#: resolves regardless of the kernel's working directory (no `%cd ..` needed).
FIGS_DIR = _DATA_DIR.parent / "figs"

#: Adjacent-system label used for domestic storage withdrawal flows.
STORAGE_LABEL = "Storage"

# ---------------------------------------------------------------------------
# Structural-break cutoff
# ---------------------------------------------------------------------------

#: Default structural-break cutoff as an ISO date string.  Pre-2022 data
#: reflects Russian transit volumes and commercial behaviours that are no
#: longer representative.  Stored as a string (consistent with levy-date
#: constants below) and converted to pd.Timestamp at the use site.
DEFAULT_CUTOFF: str = "2022-04-01"

# ---------------------------------------------------------------------------
# Working-gas capacity
# ---------------------------------------------------------------------------

# Working-gas capacity: GIE AGSI+ aggregate for Czech UGS, pre-inverse-storage era.
# Source: AGSI+ snapshot from before inverse storage was permitted (~2021/22 data).
# UPDATE: re-verify against current GIE AGSI+ "max gas in storage" CZ aggregate
# after confirming whether any currently active inverse-storage contracts inflate
# the reported total.  Replace this value and re-run notebooks / tests.
CAPACITY_TWH: float = 40.7739
CAPACITY_GWH: float = CAPACITY_TWH * 1000

MONTH_ORDER: list[int] = [10, 11, 12, 1, 2, 3]
WINTER_MONTHS: set[int] = set(MONTH_ORDER)
MONTH_NAMES: dict[int, str] = {
    10: "Oct",
    11: "Nov",
    12: "Dec",
    1: "Jan",
    2: "Feb",
    3: "Mar",
}
MONTH_NUM: dict[str, int] = {
    "october": 10,
    "november": 11,
    "december": 12,
    "january": 1,
    "february": 2,
    "march": 3,
}
DAYS_IN_MONTH: dict[int, int] = {10: 31, 11: 30, 12: 31, 1: 31, 2: 28, 3: 31}

# EU Regulation 2017/1938 Art. 6 stress-period structure
STRESS_PEAK_DAYS: int = 7
STRESS_TOTAL_DAYS: int = 30
STRESS_RESIDUAL_DAYS: int = STRESS_TOTAL_DAYS - STRESS_PEAK_DAYS  # 23

# Withdrawal-curve fitting parameters
WC_BIN_EDGES = list(range(0, 105, 5))
WC_BIN_QUANTILE: float = 0.95
WC_MIN_OBS: int = 5
WC_DEFAULT_HAIRCUT: float = 0.10

# Cold-day import conditioning
COLD_DAY_THRESHOLD_QUANTILE: float = 0.80

# End-of-March operational reserve floor (Branch 1 and Branch 2).
# Recommended as a standalone regulatory instrument: ~0.5 TWh covers roughly
# 5 days of the S2 March peak gap before injection season begins.
# Set to 0.0 in individual function calls to disable.
END_OF_SEASON_FLOOR_TWH: float = 0.5

# German gas storage levy (Gasspeicherumlage) — raised Czech import costs ~€2.5/MWh
# while in force, suppressing observed import utilisation.  Import percentiles computed
# from data spanning this period are conservative (understated capacity).
# Start: 2022-10-01 (EnSiG first application, gas year 2022/23)
# End:   2024-12-31 (abolished from 2025-01-01 per BNetzA announcement Nov 2024)
# Reference: Argus Media, "Germany to stop gas storage levy on transit from 2025"
GAS_STORAGE_LEVY_START: str = "2022-10-01"
GAS_STORAGE_LEVY_END: str = "2024-12-31"
