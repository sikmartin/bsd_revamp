# Withdrawal-Curve Blend Decision

**Produced by:** Phase 1 A3  
**Date:** 2026-05-30  
**Status:** ⏸ AWAITING SUPERVISOR SIGN-OFF before implementation

---

## Background

Two branches currently use different blend weights for the withdrawal-capacity curve:

| Branch | Current blend | Rationale in results doc |
|---|---|---|
| Branch 1 — Monthly obligations | **50% engineering / 50% empirical** | Conservative regulatory anchor; month-level simulation rarely drops below 20% fill |
| Branch 2 — Season target | **75% engineering / 25% empirical** | Season-long simulation regularly reaches fill <20% where empirical curve is sparse and underestimates physical capacity |

Both branches apply a 10% haircut to the engineering curve before blending.

---

## Quantified impact of switching each branch

### Branch 1: switching from 50/50 → 75/25

S2 monthly obligations (TWh) under current 50/50 vs. alternative 75/25:

| Month | 50/50 (current) | 75/25 | Δ |
|---|---|---|---|
| Oct | 0.00 | 0.00 | 0.00 |
| Nov | 1.00 | 1.00 | 0.00 |
| Dec | 4.46 | 3.47 | −0.99 |
| Jan | 9.33 | 5.95 | −3.38 |
| Feb | 3.90 | 3.28 | −0.62 |
| Mar | 0.34 | 0.34 | 0.00 |

**Impact:** Switching B1 to 75/25 reduces the headline S2 January obligation by **3.4 TWh
(−36%)**, and Dec/Feb by ~1 TWh / 0.6 TWh. This is a material change to the published
regulatory anchor.

### Branch 2: switching from 75/25 → 50/50

S2 season target (TWh) under current 75/25 vs. alternative 50/50:

| Scenario | 75/25 (current) | 50/50 | Δ |
|---|---|---|---|
| S1 | 25.23 | 27.63 | +2.40 |
| S2 | 21.94 | 23.16 | +1.22 |
| S3 | 17.02 | 17.10 | +0.07 |
| S4 | 9.94 | 9.94 | 0.00 |
| S5 | 5.29 | 5.29 | 0.00 |

**Impact:** Switching B2 to 50/50 increases the headline S2 season target by **1.2 TWh
(+6%)** and S1 by 2.4 TWh. Smaller than the Branch 1 impact because at the low fill
levels the season simulation reaches (~20–30%), the engineering curve already dominates
the 75/25 blend; shifting to 50/50 only matters at higher fill levels in early October.

---

## Analytical justification for each branch's current choice

### Branch 1 — 50/50 rationale

The 30-day monthly stress test starts at month-start fill (Oct–Mar) and typically does
**not** drive fill below 20% — the simulation ends with positive storage remaining.
At fill levels of 30–60%, the empirical curve is reasonably well-identified (n ≥ 10
observations per 5% bin) and reflects actual commercial behaviour under peak demand.
Using a higher engineering weight would overstate deliverability at operationally
realistic fill levels. The 50/50 blend sits midway between the conservative floor
(empirical P95, depressed by commercial suppression) and the physical ceiling
(engineering curve), which is the appropriate posture for a regulatory obligation.

### Branch 2 — 75/25 rationale

The season-long simulation (Oct 1 – Mar 31) starts at the minimum feasible fill and
draws storage down to near-zero by season end under S1–S4. At these low fill levels
(<20%), empirical observations are **sparse** (fewer than 5 observations per bin in
the Czech post-2022 data) and subject to commercial suppression: operators rarely
let storage fall below 20% in practice, so observed withdrawal at low fill reflects
conservative commercial behaviour, not physical limits. The ENTSOG engineering curve
is better-identified at low fill; the 75/25 weight is a considered judgement that
physical deliverability is closer to the engineering ceiling when operators are
actually forced to withdraw deeply (a stress scenario).

An additional observation: at 75/25, the blend is nearly identical to the pure
engineering curve below 20% fill because the empirical curve contributes only 25%
of a very low value. Switching to 50/50 adds only 1.2 TWh at S2 — a small change
that reflects this insensitivity.

---

## Recommendation

**Keep the divergent blends. Do not unify.**

The branches answer different questions and face different fill-level regimes:

- **Branch 1** (regulatory compliance checkpoint) operates at realistic in-season
  fill levels where the empirical curve is data-rich. 50/50 is the appropriate
  midpoint between commercial floor and physical ceiling.
- **Branch 2** (season-opening fill target) drives storage to the physical limit.
  The empirical curve is poorly identified at <20% fill. 75/25 is analytically
  justified and defended in the results doc.

**Unifying to 75/25 everywhere** would reduce Branch 1 Jan S2 by 3.4 TWh to 5.95 TWh —
a 36% reduction in the regulatory anchor that is poorly supported by the data at
the fill levels where Branch 1 actually operates.

**Unifying to 50/50 everywhere** would increase Branch 2 S2 by only 1.2 TWh but
would understate physical deliverability at low fill, where the engineering curve
is the more reliable reference.

### What must be implemented regardless of sign-off decision

Whichever way this lands, Phase 2 code extraction must expose the blend weight
as an **explicit named parameter** (`eng_weight: float = 0.50` in `obligations.py`,
`eng_weight: float = 0.75` in `target.py`) so the choice is visible, overridable
from the Streamlit app, and testable. It must not be a module-level global.

---

## ⏸ Supervisor sign-off required

The recommendation above (**keep divergent blends**) is presented here for supervisor
review. If approved, Phase 2 will extract the code with the current blend weights as
defaults and expose them as explicit parameters. If the supervisor directs unification,
the affected results docs and regression baselines will be updated in the same Phase 2
commit with an explanation.

**Please confirm or redirect before Phase 2 begins.**
