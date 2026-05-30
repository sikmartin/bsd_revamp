# Czech UGS Storage Obligations — Monthly Results

**Produced by** [`notebooks/storage_obligations.ipynb`](../notebooks/storage_obligations.ipynb)  
**Methodology** [`docs/analysis_synthesis_brief.md`](analysis_synthesis_brief.md) — Sections 9, 9.1  
**Data vintage** ENTSOG Physical Flows through 2026-05-28; GIE storage data through 2026-05-28

---

## What this document answers

> **What working-gas volume must regulated suppliers hold at the start of each
> heating-season month (Oct–Mar) to ensure that protected customers can be
> supplied through a 30-day 1-in-20 demand event, at each import-risk scenario?**

The obligation applies per month independently.  The 1-in-20 event is a once-per-season
occurrence; each month's requirement is a standalone stress test, not a sequential chain.

---

## Method in brief

For each calendar month m and import scenario s, a 30-day stress simulation is run
starting at fill level F:

1. **Two-tier demand profile** — Days 1–7 at `R.max.den[m]` (1-in-20 peak day, GWh/d);
   days 8–30 at the residual average `(r_30dnu[m] − 7 × R.max.den[m]) / 23`.
2. **Import level** — month-specific percentile of post-2022 daily Physical Flow imports.
3. **Withdrawal-rate constraint** — at each day, `wc(fill_t)` must meet the daily gap.
   Default curve: 50/50 blend of empirical P95 and ENTSOG engineering curve (10% haircut).
   Controlled by `WC_ASSUMPTION` in the notebook.
4. **Volume constraint** — fill must remain non-negative.
5. **Minimum obligation** — bisection finds the lowest F at which the simulation is feasible.

Compliance is checked at **month-start checkpoints only** (Oct 1, Nov 1, …, Mar 1).
Intra-month draw-down paths are unconstrained, preserving market flexibility.

---

## Main results

### Minimum required fill at start of month (TWh)

**Default assumptions: blend WC curve (50/50, 10% haircut) × scenario import percentiles**

| Month | S1 — High stress | **S2 — Stressed** | S3 — Base stressed | S4 — Median | S5 — Favourable |
|---|---|---|---|---|---|
| Oct | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 |
| Nov | 1.36 | **1.00** | 0.10 | 0.00 | 0.00 |
| Dec | 4.88 | **4.46** | 3.67 | 0.46 | 0.00 |
| Jan | 11.57 | **9.33** | 6.36 | 2.31 | 0.67 |
| Feb | 6.66 | **3.90** | 2.19 | 1.30 | 0.58 |
| Mar | 1.19 | **0.34** | 0.20 | 0.00 | 0.00 |

Czech UGS working-gas capacity: **45.3 TWh**.  All obligations fit within installed capacity.

**Recommended end-of-season operational floor (separate instrument): ~0.5 TWh at Mar 31.**
See Caveats §5.

### Import capacity ceiling benchmark (P99, cold days)

The table below shows obligations if imports are assumed to reach their **P99 on cold days**
(top-20% storage-withdrawal days per month) — the import-side counterpart to the ENTSOG
engineering withdrawal curve.  This is the most favourable defensible import assumption;
it answers "what if the interconnectors deliver near-maximum during the stress period?"

| Month | P99 cold-day imports (GWh/d) | Obligation (TWh) |
|---|---|---|
| Oct | 360.9 | 0.00 |
| Nov | 351.6 | 0.00 |
| Dec | 387.5 | 0.00 |
| Jan | 217.3 | **2.21** |
| Feb | 258.3 | 0.48 |
| Mar | 742.7 | 0.00 |

Under this ceiling assumption only January retains a material obligation (2.21 TWh),
driven purely by the withdrawal-rate constraint — storage cannot deliver the peak-day
gap fast enough even with generous imports.

### Key assumption sensitivities (S2 January obligation)

| WC assumption | Import assumption | Jan obligation |
|---|---|---|
| Empirical P95 | S2 scenarios | 14.88 TWh |
| **Blend 50/50** | **S2 scenarios** | **9.33 TWh (default)** |
| ENTSOG engineering | S2 scenarios | 4.68 TWh |
| Blend 50/50 | P99 cold days | 2.21 TWh |
| ENTSOG engineering | P99 cold days | 1.09 TWh |

The range 2–15 TWh represents the full span of defensible regulatory choices.
**S2 / blend (9.33 TWh) is the recommended anchor**: it pairs a conservative but
not extreme import assumption with a withdrawal curve that acknowledges both physical
capacity and observed commercial behaviour.

---

## Scenario interpretation

**S2 is the recommended planning anchor** for regulatory discussion.

| Scenario | Import basis | Interpretation |
|---|---|---|
| S1 — High stress | P10 | Physical-infrastructure stress — pan-European cold event with German pipeline capacity constrained; commercial override not available |
| **S2 — Stressed** | **P20** | **Regulatory anchor** — commercial-conditions stress; ~1-in-40 joint event under observed demand/import correlation, ~1-in-100 under independence assumption |
| S3 — Base stressed | P30 | Moderate stress, tighter-than-normal German supply, no corridor failure |
| S4 — Median | P50 | Central case; useful lower bound for market-impact assessment |
| S5 — Favourable | P70 | Optimistic; near-zero obligation in all months except Jan/Feb |

The five scenarios are best presented as **S2 as anchor with a calibrated sensitivity range**
(S1 shows what physical scarcity looks like; S3–S5 show the tapering under better supply conditions)
rather than five equally weighted options.

---

## Demand profile used

| Month | R.max.den — Peak 7d (GWh/d) | Residual 23d (GWh/d) | Total 30d (GWh) |
|---|---|---|---|
| Oct | 163.2 | 118.7 | 3,872.8 |
| Nov | 244.4 | 177.7 | 5,798.1 |
| Dec | 325.4 | 236.6 | 7,719.9 |
| Jan | **367.8** | **267.3** | **8,722.7** |
| Feb | 326.7 | 237.5 | 7,749.9 |
| Mar | 244.6 | 177.9 | 5,804.9 |

---

## Import assumptions (month-specific percentiles, GWh/d)

| Month | S1 (P10) | S2 (P20) | S3 (P30) | S4 (P50) | S5 (P70) | P99 unconditional | **P99 cold days** |
|---|---|---|---|---|---|---|---|
| Oct | 183 | 213 | 237 | 299 | 357 | 590 | **361** |
| Nov | 148 | 160 | 231 | 284 | 342 | 635 | **352** |
| Dec | 137 | 142 | 150 | 260 | 341 | 391 | **388** |
| Jan | 113 | 135 | 164 | 214 | 272 | 366 | **217** |
| Feb | 120 | 149 | 185 | 215 | 244 | 314 | **258** |
| Mar | 154 | 196 | 216 | 254 | 350 | 820 | **743** |

December and January show the widest spread — German hub supply is most variable
during deep-winter cold snaps.

**P99 conditional vs unconditional:** The unconditional P99 is dominated by mild-weather
days with high import utilisation; it overstates available import capacity during a cold
emergency.  The cold-day P99 (imports on days in the top 20% of storage withdrawal) is the
operationally relevant ceiling — it measures what the pipe has actually delivered when
storage was also being heavily drawn.  The gap is largest in Oct–Nov (−229 / −284 GWh/d)
and smallest in December (−3 GWh/d).  Spearman ρ between withdrawal and imports: Jan −0.67,
Feb −0.76 — the correlation is strongest in the most critical months.

---

## Regulatory application

Individual supplier obligations are derived by allocating the monthly system-level
TWh requirement in proportion to each supplier's **share of protected customers**
(Art. 6, Regulation 2017/1938).

The checkpoints (Oct 1, Nov 1, …, Mar 1) are the enforceable dates.  Between checkpoints
suppliers are free to optimise draw-down and refill within market constraints — this
preserves the commercial incentive to withdraw during high-price events, which aligns
market behaviour with the regulatory objective rather than working against it.

---

## Caveats

**1. Monthly independence assumption.**  Each obligation is sized for a standalone
30-day stress event starting that month.  Physical fill entering a month depends on
earlier-season draw-down; injection-season feasibility (Apr–Sep) is not checked here.
Targets above ~32 TWh in January (S1) warrant an explicit injection-side review.

**2. Deterministic imports.**  Month-specific percentiles are applied as constants
within each 30-day period.  Within-month variability would allow partial day-to-day
buffering, so results are conservative upper-bounds at each scenario.

**3. Withdrawal curve assumption.**  Two boundary curves bracket physical deliverability:
the empirical P95 (conservative floor — deflated by commercial suppression on cold days)
and the ENTSOG engineering curve (physical ceiling — declared technical capacity).  The
default blend (50/50, 10% haircut on engineering) sits between them.  `WC_ASSUMPTION` in
the notebook controls the active curve; the sensitivity table above shows the full range.

**4. Import assumption — conditional vs unconditional P99.**  Post-2022 data shows a strong
negative correlation between Czech storage withdrawal and imports (Spearman ρ = −0.52 to
−0.76 in winter months).  The unconditional P99 overstates import availability during a
genuine cold emergency — it is driven by mild days with high commercial flow.  The cold-day
P99 is the appropriate ceiling: it conditions on days when the interconnectors were actually
being tested under demand stress.  `IMPORT_ASSUMPTION` in the notebook controls which
benchmark is shown in the ceiling table.  The residual risk of a pan-European physical
capacity constraint (German pipe saturated) is captured by S1.

**5. End-of-season operational floor.**  No endpoint constraint is embedded in the March
stress test (doing so would provision for a second 1-in-20 event).  A separate minimum
reserve of **~0.5 TWh at March 31** is recommended — covering roughly 5 days of the
S2 March peak gap (49 GWh/d net of imports) before injection season begins.  This is
a standalone regulatory instrument, additional to the monthly obligations above.

**6. Czech monthly framing vs. EU floating window.**  The EU regulation's 7/30-day stress
events are not calendar-pinned.  The Czech monthly approach is administratively tractable
and conservative (January always captures the worst peak).  Cross-month stress events
(e.g. starting January 15) are not modelled; the exposure at boundary months is small
relative to model uncertainty.
