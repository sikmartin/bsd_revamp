# Phase 1 Results Cross-Check

**Produced by:** Phase 1 A2 — verification against freshly re-run notebooks  
**Date:** 2026-05-30  
**Notebooks re-executed via:** `uv run jupyter nbconvert --to notebook --execute`  
**Data vintage:** ENTSOG Physical Flows through 2026-05-28; GIE storage data through 2026-05-28

> **Gate purpose:** Confirm that `docs/storage_obligations_results.md` and
> `docs/storage_target_results.md` accurately reflect current notebook output before
> the deck (Phase 6) uses them as the sole source of truth.

---

## Branch 1 — `storage_obligations_results.md`

### Main obligations table (minimum fill at month start, TWh)

| Month | S1 | S2 | S3 | S4 | S5 | Status |
|---|---|---|---|---|---|---|
| Oct | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | ✅ |
| Nov | 1.36 | 1.00 | 0.10 | 0.00 | 0.00 | ✅ |
| Dec | 4.88 | 4.46 | 3.67 | 0.46 | 0.00 | ✅ |
| Jan | 11.57 | 9.33 | 6.36 | 2.31 | 0.67 | ✅ |
| Feb | 6.66 | 3.90 | 2.19 | 1.30 | 0.58 | ✅ |
| Mar | 1.19 | 0.34 | 0.20 | 0.00 | 0.00 | ✅ |

All cells within 0.01 TWh of notebook output. **Pass.**

### Demand profile table

| Month | Peak 7d (GWh/d) | Residual 23d (GWh/d) — doc | Residual 23d (GWh/d) — notebook | Total 30d (GWh) | Status |
|---|---|---|---|---|---|
| Oct | 163.2 | 81.2 | **118.7** | 3,873 | ❌ |
| Nov | 244.4 | 152.4 | **177.7** | 5,798 | ❌ |
| Dec | 325.4 | 198.0 | **236.6** | 7,720 | ❌ |
| Jan | 367.8 | 267.3 | 267.3 | 8,723 | ✅ |
| Feb | 326.7 | 202.5 | **237.5** | 7,750 | ❌ |
| Mar | 244.6 | 153.2 | **177.9** | 5,805 | ❌ |

**Root cause:** The "Residual 23d" column in the results doc is wrong for five of six months.
The correct formula is `(r_30dnu_total − 7 × R.max.den) / 23`; the erroneous values appear
to be from a different formula or an earlier version of the demand data.
The **Total 30d** column is correct, and the obligation numbers are unaffected
(the simulation uses peak and residual directly, not from this display table).

**Resolution:** Fix the five cells in `storage_obligations_results.md`. *(Done in Phase 1 A4 step.)*

### Import table (GWh/d)

| Month | S1 | S2 | S3 | S4 | S5 | P99 uncond | P99 cold | Status |
|---|---|---|---|---|---|---|---|---|
| Oct | 183 | 213 | 237 | 299 | 357 | 590 | 361 | ✅ |
| Nov | 148 | 160 | 231 | 284 | 342 | 635 | 352 | ✅ |
| Dec | 137 | 142 | 150 | 260 | 341 | 391 | 388 | ✅ |
| Jan | 113 | 135 | 164 | 214 | 272 | 366 | 217 | ✅ |
| Feb | 120 | 149 | 185 | 215 | 244 | 314 | 258 | ✅ |
| Mar | 154 | 196 | 216 | 254 | 350 | 820 | 743 | ✅ |

All within 1 GWh/d of notebook output (rounding). **Pass.**

### P99 cold-day ceiling obligations

| Month | P99 cold-day import (GWh/d) | Obligation (TWh) — doc | Notebook | Status |
|---|---|---|---|---|
| Oct | 360.9 | 0.00 | 0.00 | ✅ |
| Nov | 351.6 | 0.00 | 0.00 | ✅ |
| Dec | 387.5 | 0.00 | 0.00 | ✅ |
| Jan | 217.3 | 2.21 | 2.21 | ✅ |
| Feb | 258.3 | 0.48 | 0.48 | ✅ |
| Mar | 742.7 | 0.00 | 0.00 | ✅ |

**Pass.**

### Sensitivity table (S2 January)

| WC assumption | Import assumption | Doc (TWh) | Notebook (TWh) | Status |
|---|---|---|---|---|
| Empirical P95 | S2 scenarios | 14.88 | 14.88 | ✅ |
| Blend 50/50 | S2 scenarios | 9.33 | 9.33 | ✅ |
| ENTSOG engineering | S2 scenarios | 4.68 | 4.67 | ✅ |
| Blend 50/50 | P99 cold days | 2.21 | 2.21 | ✅ |

**Pass.**

---

## Branch 2 — `storage_target_results.md`

### Minimum required 1-October fill

| Scenario | Start fill (%) — doc | Notebook | Start fill (TWh) — doc | Notebook | Binding — doc | Notebook | Status |
|---|---|---|---|---|---|---|---|
| S1 | 55.7 | 55.69 | 25.2 | 25.23 | Withdrawal rate | Withdrawal rate | ✅ |
| S2 | 48.4 | 48.44 | 21.9 | 21.94 | **Withdrawal rate** | **volume** | ❌ (binding only) |
| S3 | 37.6 | 37.58 | 17.0 | 17.02 | **Withdrawal rate** | **volume** | ❌ (binding only) |
| S4 | 21.9 | 21.94 | 9.9 | 9.94 | **Withdrawal rate** | **volume** | ❌ (binding only) |
| S5 | 11.7 | 11.67 | 5.3 | 5.29 | Volume | volume | ✅ |

All start-fill numbers match within rounding (0.1 TWh / 0.1%). **Numeric pass.**

**Binding constraint discrepancy (S2–S4):** The doc states all of S1–S4 are
withdrawal-rate binding. The current notebook output shows only S1 is
withdrawal-rate binding; S2–S4 are volume-limited at threshold. This is
consistent with the 75/25 blend used in Branch 2: at the low fill levels
reached by S2–S4, the engineeering-weighted curve (75%) keeps withdrawal
capacity above the daily gap, so volume runs out before the rate cap binds.
Under the old empirical P95 curve (which was binding at ~20% fill with ~127 GWh/d),
S2–S4 were indeed withdrawal-rate binding.

**Resolution:** Update the "Binding constraint" column for S2–S4 in the results doc
and revise the narrative "binding physical constraint remains withdrawal rate (S1–S4)"
to "(S1 only)". *(Done in Phase 1 A4 step.)*

### P99 cold-day ceiling (all scenarios converge)

| Metric | Doc | Notebook | Status |
|---|---|---|---|
| Start fill (TWh) | 6.58 | 6.58 | ✅ |
| Start fill (%) | 14.5 | 14.53 | ✅ |

**Pass.**

### Sensitivity table (S2 base, peak ±50 GWh/d)

| Assumption | Doc | Notebook | Status |
|---|---|---|---|
| Base (blend WC) | 21.9 | 21.94 | ✅ |
| Peak +50 GWh/d | ~30 | 30.48 | ✅ (approx) |
| Peak −50 GWh/d | ~15 | 14.43 | ✅ (approx) |

Doc uses "~" prefix; rounded values are consistent. **Pass.**

---

## Summary

| Document | Section | Result | Action required |
|---|---|---|---|
| `storage_obligations_results.md` | Main obligations table | ✅ all pass | None |
| `storage_obligations_results.md` | Demand profile — "Residual 23d" | ❌ 5 of 6 cells wrong | Fix values |
| `storage_obligations_results.md` | Import table | ✅ all pass | None |
| `storage_obligations_results.md` | P99 cold-day obligations | ✅ all pass | None |
| `storage_obligations_results.md` | Sensitivity table | ✅ all pass | None |
| `storage_target_results.md` | Start fill (%, TWh) | ✅ all pass | None |
| `storage_target_results.md` | Binding constraint S2–S4 | ❌ says "withdrawal rate", should be "volume" | Fix column + narrative |
| `storage_target_results.md` | P99 cold-day ceiling | ✅ pass | None |
| `storage_target_results.md` | Sensitivity table | ✅ pass | None |

**The headline numbers on which Phase 6 relies are correct.**
The two ❌ items are presentational (demand residual column, binding constraint label)
and do not affect any TWh obligation or fill target. Both are fixed in Phase 1 A4.
