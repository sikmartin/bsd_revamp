"""Scenario definitions (S1–S5) for import-risk sensitivity analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    percentile: int
    color: str = ""


def _build_defaults() -> list[Scenario]:
    try:
        from .jvs import PALETTES
        colors = PALETTES["scenarios"]
    except Exception:
        colors = [""] * 5

    return [
        Scenario("S1", "S1 — High stress",   10, colors[0]),
        Scenario("S2", "S2 — Stressed",       20, colors[1]),
        Scenario("S3", "S3 — Base stressed",  30, colors[2]),
        Scenario("S4", "S4 — Median",         50, colors[3]),
        Scenario("S5", "S5 — Favourable",     70, colors[4]),
    ]


DEFAULT_SCENARIOS: list[Scenario] = _build_defaults()

# Convenience dict keyed by scenario key
DEFAULT_SCENARIOS_DICT: dict[str, Scenario] = {s.key: s for s in DEFAULT_SCENARIOS}
