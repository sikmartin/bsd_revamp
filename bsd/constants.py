"""Project-wide constants for the Czech UGS storage sizing models."""

from .data import WINTER_MONTHS  # re-export; defined once in data.py

CAPACITY_TWH: float = 45.3034
CAPACITY_GWH: float = CAPACITY_TWH * 1000

MONTH_ORDER: list[int] = [10, 11, 12, 1, 2, 3]
MONTH_NAMES: dict[int, str] = {10: "Oct", 11: "Nov", 12: "Dec",
                                1: "Jan", 2: "Feb", 3: "Mar"}
MONTH_NUM: dict[str, int] = {
    "october": 10, "november": 11, "december": 12,
    "january": 1,  "february": 2,  "march": 3,
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
COLD_DAY_QUANTILE: float = 0.80
