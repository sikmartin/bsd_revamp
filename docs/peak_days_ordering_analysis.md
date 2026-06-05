# Peak-Day Ordering in the 30-Day Stress Test — Sensitivity and Recommendation

**Scope** Branch 1 monthly storage obligations ([`bsd/obligations.py`](../bsd/obligations.py), `simulate_month`)
**Question** Where should the 7 peak days fall within the 30-day Art. 6 stress window, and how much does that choice change the obligation?
**Audience** Regulator / consultant reviewing the storage-sizing methodology
**Bottom line** The choice is **material — up to +3.6 TWh** on the most critical cells, and it bites only on the withdrawal-rate-binding deep-winter cells. The current model places the peak first, which **understates** those obligations. The recommendation splits by branch: **Branch 1 (deterministic, regulatory)** should adopt a single opinionated, conservative placement — **peak-last** — framed as a security-of-supply convention; **Branch 2 (season-long simulation)** should instead **randomise the peak placement** (and ultimately draw realistic ramped demand trajectories), which dissolves the placement question and is where realism belongs. The two branches then answer different questions and their numbers line up coherently (Branch 1 ≥ Branch 2 at comparable confidence).

---

## 1. The issue and why it matters

The monthly stress test models a 30-day 1-in-20 cold event as two demand tiers: **7 peak days** at the 1-in-20 peak-day rate (`R.max.den`) and **23 residual days** at the remaining average rate. Feasibility is checked day-by-day against two constraints:

- **Volume** — storage fill must stay non-negative across the 30 days.
- **Withdrawal rate** — on each day, the deliverability the storage can physically produce at its current fill, `wc(fill)`, must meet that day's demand gap (demand minus imports).

The withdrawal curve `wc(fill)` is **monotone increasing and strongly non-linear**: deliverability collapses as fill falls. On the blended curve (50/50, 10 % haircut) used as the Branch 1 default, deliverability is ~500 GWh/d above 50 % fill but falls steeply below ~30 %:

| Fill % | 10 | 20 | 25 | 30 | 35 | 40 | 50 |
|---|---|---|---|---|---|---|---|
| Deliverability (GWh/d) | 193 | 241 | 264 | 331 | 408 | 446 | 494 |

Because of this curvature, **when the peak falls within the window changes the result**:

- **Peak first (current):** the peak gap is tested while fill is at its highest → the withdrawal-rate constraint is easiest to meet. Storage then depletes fastest early.
- **Peak last:** the peak gap is tested after 23 residual days have already drawn the fill down → deliverability is at its lowest exactly when the largest gap must be served. This is the hardest case.
- **Peak floating (any position in between):** intermediate.

For the months where the **withdrawal rate is the binding constraint** — December and January (and February) at the stressed scenarios S1–S3 — the ordering is **not neutral**. The regulation (EU Reg. 2017/1938 Art. 6) defines a 7-day peak within a 30-day reference window but **does not specify where the peak falls**, so the modelling choice is ours to justify.

For the **volume-binding** months (October, November, the milder scenarios, and the March end-of-season floor) ordering is irrelevant: total gas withdrawn over 30 days is identical regardless of sequence, so a pure volume constraint gives the same answer either way. The sensitivity is entirely a withdrawal-rate phenomenon.

---

## 2. Quantitative results

Minimum required start-of-month fill (TWh), blended WC curve (`eng_weight = 0.50`), default scenario import percentiles. Only cells where ordering changes the result by **> 0.1 TWh** are shown; all other month × scenario cells are identical under both orderings.

| Month | Scenario | Peak-first (current) | Peak-last (worst) | Δ | Binding constraint |
|---|---|---:|---:|---:|---|
| Dec | S1 | 4.82 | **7.11** | +2.29 | WC both |
| Dec | S2 | 4.44 | **6.63** | +2.19 | WC both |
| Dec | S3 | 3.72 | **5.72** | +1.99 | WC both |
| Jan | S1 | 10.91 | **14.46** | +3.55 | WC both |
| Jan | S2 | 8.89 | **11.93** | +3.04 | WC both |
| Jan | S3 | 6.20 | **8.57** | +2.37 | WC both |
| Jan | S4 | 2.31 | **3.15** | +0.84 | **volume → WC** |
| Feb | S1 | 6.47 | **9.16** | +2.70 | WC both |
| Feb | S2 | 3.93 | **5.97** | +2.04 | WC both |

**Cells unaffected (Δ = 0.00):** all of October, November, March (floor-binding); December S4–S5; January S5; February S3–S5. These are volume- or floor-binding, where ordering cannot matter.

**Effect on the binding constraint.** For the deep-WC-binding cells the constraint is withdrawal-rate under *both* orderings — peak-last simply makes it bite harder. The interesting case is **January S4**, which is **volume-binding under peak-first (2.31 TWh) but flips to withdrawal-rate-binding under peak-last (3.15 TWh)**: depleting 23 residual days before the peak pushes fill into the steep part of the curve, so deliverability — not volume — becomes the limiting factor. This shows the two constraints are not cleanly separable near the margin; ordering can change *which* one governs.

**The worst case is always peak-last.** Sweeping the peak across all 24 admissible insertion positions, the required start fill rises **monotonically and almost linearly** with the peak's position. The slope per day of delay equals the **residual daily gap** (the gas drawn on each pre-peak residual day) — e.g. ~0.10 TWh/day for Dec S1, ~0.13 TWh/day for Jan S2 — until the peak block reaches the end of the window. There is no interior maximum: the analytical worst case is provably **peak-last (position 23)** for every withdrawal-rate-binding cell. Consequently the **worst-case envelope and peak-last give identical numbers** — no separate envelope computation is needed.

**Import-ceiling benchmark.** The P99 cold-day January benchmark in the results document (the most-favourable-imports case, WC-driven) also rises under peak-last, from **2.20 → 2.77 TWh** (+0.57). The February P99 cold-day benchmark is volume-binding and unchanged.

---

## 3. Approaches compared

| Approach | What it assumes | Jan S2 result | Pros | Cons |
|---|---|---:|---|---|
| **Peak-first** (current default) | Cold snap strikes at month-start with tanks full | 8.89 TWh | Simple; matches current outputs | **Under-provisions**: a compliant supplier can still fail if the peak arrives late in the window |
| **Peak-last** (recommended) | Peak follows 23 days of sustained sub-peak cold | 11.93 TWh | Provably worst admissible ordering; physically realistic for deep winter; equals the envelope | More conservative (+34 % on the anchor) |
| **Worst-case envelope** (max over all positions) | Robust to any peak timing | 11.93 TWh | Defensible against "what if the peak fell elsewhere" | Identical to peak-last here, so adds computation for no extra protection |
| **Analytical worst-case** (bisect/iterate the peak position) | — | 11.93 TWh | Confirms peak-last is optimal without assuming it | Unnecessary in practice: monotonicity makes peak-last the closed-form answer |
| **Mid-window / fixed interior position** | Peak in the "middle" of the spell | ~10.4 TWh | Splits the difference | Arbitrary; no regulatory or physical basis for any specific interior day |
| **Empirically-calibrated position** | Peak placed where real cold spells put it | n/a | Most defensible *if* it could be substantiated | **Not feasible from current data** (see §4); needs a daily demand/temperature series we do not hold |
| **Stochastic / floating placement** (Branch 2) | Distribution over peak timing across many winters | distribution | Realistic; yields a risk-calibrated target, not a single adverse point | Belongs in the simulation branch, not the regulatory floor; the regulation asks Branch 1 for a guarantee, not an expectation |

Because required fill is monotone in peak position, **every fixed-placement approach is bracketed by peak-first (lower bound) and peak-last (upper bound)**. For the deterministic obligation the decision reduces to picking a point on that bracket; the realism that would justify an interior point lives more naturally in the stochastic branch.

---

## 4. Recommendation — split by branch

The placement question has a different right answer in each branch, because the two branches answer different questions. The deterministic regulatory branch needs a single defensible number; the simulation branch can carry a distribution.

### 4.1 Branch 1 (deterministic obligation): fixed, opinionated, conservative — peak-last

**Adopt peak-last as the Branch 1 default**, and report peak-first alongside it as an explicit lower bound ("best-case peak timing"). Frame it honestly as a **conservative regulatory convention, not a realism claim**, justified on four grounds:

- **Asymmetric cost.** Under-provisioning fails protected customers; over-provisioning costs carry. Art. 6 is a security-of-supply standard, so erring conservative is principled, not arbitrary.
- **Adequacy guarantee, not expectation.** The regulation requires supply through the 1-in-20 event **whatever day the peak falls on**, and does not pin the peak's position within the 30-day window. An obligation is only a genuine guarantee if it holds for the worst admissible timing. A supplier sized to 8.89 TWh for January S2 (peak-first) would be deliverability-short if the same peak arrived after three weeks of sustained cold.
- **Invariance.** Peak-last is the one placement whose obligation is robust to the unmodelled "when does the peak come" question — it removes a free parameter from a regulatory threshold rather than baking an assumption into it.
- **Reproducibility.** A legal obligation should not carry Monte Carlo noise. One placement, one number, one rule.

It is also internally consistent with the model's own demand definition: the 23 elevated residual days are *already* part of the stress event; placing them before the peak simply orders them adversely. And because peak-last coincides exactly with the worst-case envelope and the analytical optimum (§2), no extra machinery is needed — a one-line change to the gap-sequence construction delivers the robust answer.

**Why not calibrate the placement to real cold spells?** It is the more appealing instinct, but it is not feasible from the current inputs and is partly illusory even in principle:

- *Data.* The demand inputs are two monthly scalars per month — `R.max.den` (one 1-in-20 peak-day value) and `r_30dnu` (one 30-day total) — not daily trajectories. The repository holds no daily protected-demand or temperature series. "Where did the peak fall within real spells" is therefore a **data-acquisition project** (a daily consumption or degree-day series plus a definition of "the spell"), not something derivable today.
- *Concept.* `R.max.den` and `r_30dnu` are two *independent* regulatory statistics. The model composites them into one trajectory — 7 flat peak days + 23 flat residual days — but that rectangular two-tier shape is a stylisation of what is really a smooth ramp (demand builds, peaks, recedes). Calibrating the position of a rectangular block would be calibrating a coarse proxy and would buy false precision. The honest home for trajectory realism is Branch 2 (§4.2).

**Residual caveat.** Peak-last assumes the full 23 residual days are drawn at the scenario import level *before* the peak — coherent with the existing deterministic-import assumption, and conservative for the same reason (Caveat 2 in the results document). A future stochastic-import extension that allows within-spell import recovery would shrink the peak-last premium; the deterministic framing should nonetheless use peak-last.

### 4.2 Branch 2 (season-long simulation): randomise placement, then ramp the trajectory

In the simulation branch the placement should be **stochastic, not fixed** — this is exactly where the realism that cannot be substantiated in Branch 1 can be expressed as a distribution rather than a single adverse point.

- **First step (cheap, high value):** insert the 7-day peak block at a *random position* within the 30-day window on each simulated winter, and report the required 1-Oct fill as a distribution — e.g. the fill that survives 95 % of simulated winters. This slots directly into the planned stochastic-imports and injection-feasibility extensions and turns the deterministic "which ordering" question into a percentile.
- **Fuller step:** replace the rectangular two-tier demand with a **realistic ramped daily trajectory** (build-up → peak → recession). This *dissolves* the placement question entirely instead of randomising a stylisation, and is the natural endpoint of the Branch 2 evolution.

**Consistency between the branches.** With this split, Branch 1 (conservative per-month floor, peak-last) will sit **at or above** Branch 2 (season-long, risk-calibrated target over a distribution of realistic winters), because peak-last is the adverse tail of what Branch 2 samples. That ordering is the right story to tell a regulator: *the monthly obligation is the conservative floor; the season simulation shows what a realistic risk-calibrated target looks like below it.* If proportionality pushback arises against the higher peak-last numbers, the answer is not to soften Branch 1's placement but to let Branch 2's distribution carry the case for a lower realistic target.

**Implementation note (Branch 1).** In `simulate_month`, change the gap sequence from `[gap_peak]*7 + [gap_resid]*23` to `[gap_resid]*23 + [gap_peak]*7`. Expose a `peak_position` argument (default 23 = peak-last; 0 = peak-first) so the lower bound and intermediate positions remain reproducible for sensitivity reporting, and so Branch 2 can reuse the same simulation core with a randomly drawn `peak_position`.

---

## 5. Impact on existing published results

[`docs/storage_obligations_results.md`](storage_obligations_results.md) **requires revision**, but only for the withdrawal-rate-binding cells. The main obligations table should be regenerated under peak-last:

| Month | S1 | S2 (anchor) | S3 | S4 | S5 |
|---|---:|---:|---:|---:|---:|
| Oct | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Nov | 1.36 | 1.01 | 0.10 | 0.00 | 0.00 |
| Dec | **7.11** | **6.63** | **5.72** | 0.46 | 0.00 |
| Jan | **14.46** | **11.93** | **8.57** | **3.15** | 0.67 |
| Feb | **9.16** | **5.97** | 2.19 | 1.30 | 0.58 |
| Mar | 1.92 | 0.90 | 0.78 | 0.51 | 0.50 |

(Bold = changed from the published peak-first table. Unchanged cells are volume- or floor-binding.)

Specific edits needed in the results document:

1. **Main results table** — update the bold cells above. The headline **S2 January anchor moves from 8.89 → 11.93 TWh**; S1 January from 10.91 → 14.46 TWh (still within the 40.8 TWh installed capacity).
2. **Import-capacity ceiling benchmark** — the WC-driven **January P99 cold-day obligation moves 2.20 → 2.77 TWh**; February (0.48) unchanged.
3. **Key-assumption sensitivity table** — the "Blend 50/50 × S2 January" anchor figure updates to 11.93 TWh; the 2–14 TWh defensible range becomes roughly **3–17 TWh** once the empirical-P95 and engineering bounds are also re-run under peak-last (those re-runs are recommended for completeness).
4. **Caveat 6 (Czech monthly framing)** — currently states "January always captures the worst peak." Add that, *within* each month, the peak is now placed last to guarantee the obligation against any peak timing — closing a gap the current wording leaves open.

The model framing, scenario interpretation, demand profile, and import-assumption sections need no change. The revision is a level shift on the deep-winter stressed scenarios, not a structural change to the methodology.

---

## 6. Implementation prompt for the proposed approach

The following is a ready-to-hand task brief for implementing the §4 recommendation. It is written so it can be pasted to a developer or coding agent and executed without further context.

> **Task — implement peak-day placement as an explicit parameter, default to peak-last in Branch 1, and prepare the Branch 2 stochastic hook.**
>
> **Context.** `bsd/obligations.py::simulate_month` runs a 30-day Art. 6 stress test as 7 peak days + 23 residual days. It currently hard-codes the peak first: `gaps = [gap_peak] * STRESS_PEAK_DAYS + [gap_resid] * STRESS_RESIDUAL_DAYS`. Because the withdrawal-capacity curve is non-linear, placing the peak later raises the required start fill on the withdrawal-rate-binding deep-winter cells by up to ~3.6 TWh. Peak-last is the analytical worst case (required fill is monotone increasing in peak position). See `docs/peak_days_ordering_analysis.md` for the full rationale. Read that document and `bsd/obligations.py`, `bsd/constants.py`, `bsd/withdrawal.py` before editing.
>
> **Branch 1 changes (deterministic, regulatory):**
> 1. Add a keyword-only parameter `peak_position: int = STRESS_RESIDUAL_DAYS` to `simulate_month` (range 0–`STRESS_RESIDUAL_DAYS`; 0 = peak-first, `STRESS_RESIDUAL_DAYS` = peak-last). Build the gap sequence as `[gap_resid] * peak_position + [gap_peak] * STRESS_PEAK_DAYS + [gap_resid] * (STRESS_RESIDUAL_DAYS - peak_position)`. Validate the bound and raise `ValueError` otherwise.
> 2. Thread `peak_position` through `min_start_fill_month`, `run_all_months`, and any other caller, keeping the default at peak-last so the regulatory default is conservative. Do **not** silently change results elsewhere — every public entry point should expose the parameter with the same default.
> 3. Keep peak-first reproducible: a caller passing `peak_position=0` must reproduce the current published numbers exactly (use this as a regression check).
> 4. Add/adjust unit tests: (a) volume- and floor-binding cells are invariant to `peak_position`; (b) WC-binding cells (Dec/Jan/Feb S1–S3) are monotone non-decreasing in `peak_position`; (c) `peak_position=0` reproduces the legacy table; (d) the peak-last Jan S2 obligation is ≈ 11.93 TWh. Run with `uv run`.
>
> **Documentation changes:**
> 5. Regenerate `docs/storage_obligations_results.md` under the new default (peak-last). Update the main obligations table, the P99 cold-day January benchmark (2.20 → 2.77 TWh), the S2-January sensitivity row, and Caveat 6 per §5 of the ordering analysis. Re-run the empirical-P95 and engineering-curve bounds under peak-last so the stated defensible range is internally consistent.
> 6. Update `notebooks/storage_obligations.ipynb` so its narrative and any inline numbers reflect the peak-last default; mention `peak_position` and show the peak-first lower bound as a sensitivity. Edit the notebook deterministically with `nbformat` (one cell at a time) and verify the diff against `HEAD` — do not delegate cell edits to a subagent.
>
> **Branch 2 hook (season-long simulation — prepare, do not fully build):**
> 7. Ensure the simulation core can accept a per-event `peak_position` so Branch 2 (`bsd/target.py`) can draw it at random per simulated winter. Add a thin, documented seam (function argument or small helper) but leave the stochastic draw, the ramped-trajectory demand, and the percentile reporting as a clearly-marked TODO referencing §4.2. Do not change Branch 2 numerical outputs in this task.
>
> **Acceptance criteria:** all existing tests pass; new tests above pass; `peak_position=0` reproduces the legacy obligations table to within bisection tolerance; the default run produces the §5 peak-last table; docs and notebook are consistent with the new default; no Branch 2 output changes yet. Summarise the before/after obligations table in the PR description.

This prompt implements only the §4.1 default switch plus the §4.2 seam; the full Branch 2 stochastic placement and ramped-trajectory work is intentionally deferred to its own task, consistent with the planned Branch 2 evolution.
