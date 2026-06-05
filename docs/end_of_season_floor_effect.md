# Effect of the End-of-Season Floor on Monthly Obligations

**Scope** Sensitivity analysis of `END_OF_SEASON_FLOOR_TWH` (default 0.5 TWh) on the
results in [`docs/storage_obligations_results.md`](storage_obligations_results.md).
**Method** Re-ran `bsd.run_all_months` with `end_of_march_floor_TWh = 0.5` (default)
and `= 0.0` (disabled), all other assumptions held at Branch 1 defaults
(blend WC 50/50, 10% haircut; scenario import percentiles).

---

## Headline

The floor's effect is **confined entirely to March** and is **purely additive at
~0.5 TWh** across every scenario. It changes no other month and does not move the
season-defining January peak. This confirms the floor behaves exactly as designed:
a standalone operational-reserve instrument bolted onto the March result, not a
parameter that propagates through the stress model.

## March obligation, with vs. without the floor (TWh)

| Scenario | Floor ON (0.5) | Floor OFF (0.0) | Δ |
|---|---|---|---|
| S1 — High stress | 1.92 | 1.42 | +0.50 |
| **S2 — Stressed** | **0.90** | **0.40** | **+0.50** |
| S3 — Base stressed | 0.78 | 0.28 | +0.50 |
| S4 — Median | 0.52 | 0.01 | +0.51 |
| S5 — Favourable | 0.50 | 0.00 | +0.50 |

All other months (Oct, Nov, Dec, Jan, Feb) are **identical** under both settings.

## Why the effect is exactly +0.5 TWh

The floor is checked *after* the 30-day stress run completes, so it never interacts
with the within-month withdrawal-rate or volume constraints. Without the floor,
March is **volume-binding** in every scenario: storage is drawn down to ≈0 TWh by
Mar 31 (fill_end ≈ 0.00–0.002 TWh). Adding the requirement "end ≥ 0.5 TWh" therefore
just lifts the required *starting* fill by the floor volume one-for-one. With the floor
on, the binding constraint for all five March scenarios flips from `volume` to
`end-of-season floor`.

## Implications for the headline results

- **The recommended S2 anchor (8.89 TWh, January) is unaffected.** January is
  withdrawal-rate binding and far larger than any March figure; March never drives
  the season maximum, so the floor changes neither the anchor nor the 2–14 TWh
  sensitivity span.
- **The floor's real role is to put a non-trivial floor under March specifically.**
  Without it, the favourable scenarios (S4/S5) carry essentially **zero** March
  obligation (0.00–0.01 TWh), because March demand is mild and imports have
  recovered. The 0.5 TWh instrument is what keeps an operational reserve in the
  tank entering injection season regardless of scenario — which is the entire
  justification for treating it as a separate regulatory instrument rather than
  letting it fall out of the stress model.
- **Disabling it is a clean, transparent toggle.** Because the impact is a flat
  +0.5 TWh on one cell column, a reviewer can mentally add or remove it without
  re-running anything. Setting `END_OF_SEASON_FLOOR_TWH = 0.0` (or passing
  `end_of_march_floor_TWh=0.0`) reproduces the "pure Art. 6 stress" March numbers
  in the table above.

## Caveat

The floor does **not** provision for a second 1-in-20 event after March — it is a
post-stress reserve only (see Caveat §5 in the results doc). The 0.5 TWh figure is
calibrated as ~5 days of the S2 March peak gap (~49 GWh/d net of imports); changing
that calibration scales the March column linearly by the same amount.
