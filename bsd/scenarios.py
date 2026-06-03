"""Scenario definitions (S1–S5) for import-risk sensitivity analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    percentile: int
    color: str = ""
    description: str = ""


def _build_defaults() -> list[Scenario]:
    try:
        from .jvs import PALETTES
        colors = PALETTES["scenarios"]
    except Exception:
        colors = [""] * 5

    return [
        Scenario("S1", "S1 — High stress",  10, colors[0],
            "Severe import shortfall (1-in-10 winter days worse than this). "
            "Represents a prolonged cold spell coinciding with low German hub "
            "supply or a single-corridor disruption."),
        Scenario("S2", "S2 — Stressed",     20, colors[1],
            "Significant import shortfall (1-in-5 winter days worse). "
            "Credible planning anchor: pairs a 1-in-20 demand event with a "
            "1-in-5 import shortfall for a joint severity of roughly 1-in-100."),
        Scenario("S3", "S3 — Base stressed", 30, colors[2],
            "Moderate import shortfall (1-in-3 winter days worse). Represents "
            "a cold week with tighter-than-normal German supply but no single "
            "corridor failure."),
        Scenario("S4", "S4 — Median",        50, colors[3],
            "Median import conditions. Half of observed winter days had lower "
            "imports than this. A reasonable central-case baseline."),
        Scenario("S5", "S5 — Favourable",    70, colors[4],
            "Above-average imports (only 30% of winter days higher). Optimistic "
            "supply conditions; useful as a lower bound on storage requirements."),
    ]


DEFAULT_SCENARIOS: list[Scenario] = _build_defaults()

DEFAULT_SCENARIOS_DICT: dict[str, Scenario] = {s.key: s for s in DEFAULT_SCENARIOS}
