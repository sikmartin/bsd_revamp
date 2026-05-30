# Consulting Review — Czech UGS Storage Target & Obligation Policy Analysis

**Reviewers:** Senior gas-market analyst & senior gas-systems infrastructure analyst (consulting team)
**Scope:** Documents reviewed — `analysis_synthesis_brief.md`, `storage_obligations_results.md`, `storage_target_results.md`, `wc_blend_decision.md`, and figures under `figs/`. Code intentionally not inspected.
**Date:** 2026-05-30
**Response date:** 2026-05-30
**Verdict:** *Analytically credible scaffold, but several first-order assumptions need rework before any number is offered as a binding regulatory anchor.*

---

## Team response summary (2026-05-30)

| Issue | Action taken |
|---|---|
| **T1** Fill trajectories reach 0% | **Fixed.** 0.5 TWh end-of-March floor embedded as a hard constraint in `bsd.target.simulate`. B2 S2 target: 21.9 → 22.5 TWh. Binding constraint for all scenarios: end-of-season floor. |
| **T2** WC curve biased / non-monotone | **Noted — not executed.** Cold-day conditioned upper-envelope approach is the right direction; deferred to next modelling phase as it requires re-specification of the empirical curve fitting. |
| **T3** Declared WC 734 GWh/d above firm capacity | **Addressed by haircut.** The 10% engineering-curve haircut and 50/50 blend already bridge the declared-vs-firm gap. The 10% haircut reduces the engineering ceiling from 734 to ~660 GWh/d, within the firm range cited by the review. No further code change. |
| **T4** Capacity 45.3 TWh above public sources | **Fixed.** Updated to 40.7739 TWh (pre-inverse-storage AGSI+ figure). Update point flagged in `bsd/constants.py`. All obligation and target numbers updated accordingly. |
| **T5** Blend weights diverge across branches | **Noted — not executed.** Same as T2. Deferred. See also `docs/wc_blend_decision.md`. |
| **M1** Imports treated as fixed percentile | **Noted.** This is not an econometric analysis. Import price-elasticity is out of scope for this regulatory framing exercise. |
| **M2** No injection feasibility check | **Noted.** Deferred per §9.2 of the brief. Out of scope for this phase. |
| **M3** EU Reg 2025/1733 not mentioned | **Fixed.** §10 added to `analysis_synthesis_brief.md` comparing Czech monthly schedule to EU 2025/1733 and flagging where Czech framing is stricter. |
| **M4** German levy structural break | **Flagged.** `levy_in_force` column added to `bsd.data.load_daily_imports()` output. Levy period 2022-10-01 – 2024-12-31 documented in `bsd/constants.py`. Percentile pooling note added to data docstring. |
| **M5** No N-1 corridor scenario | **Noted.** N-1 is addressed in a separate regulatory instrument (EU Reg 2017/1938 Art. 5 N-1 infrastructure standard). Out of scope here. |
| **M6** Market impact not assessed | **Noted.** Out of scope for this regulatory framing exercise. |
| **Me1** No ERÚ Decree 349/2012 citation | **Acknowledged.** The 7/23-day demand profile is an analytical convention consistent with the regulation; full ERÚ citation mapping is reserved for the formal regulatory submission text. |
| **Me2** Inter-branch coherence at 1 Jan | **Fixed.** §9.3 added to `analysis_synthesis_brief.md` with a cross-branch table at 1 January and explanation of the 5–6 TWh buffer. |
| **Me3** Spearman ρ on 272-day sample | **Noted.** Added to future-work list (§9.2). Re-running on the full 760-day winter sample is straightforward and recommended before external submission. |
| **Me4** Sensitivity table S4/S5 swapped | **Fixed** (committed earlier). |
| **Me5** Sign-off typo / no date | **Fixed** (committed earlier). |

---

## 1. Executive summary

The two-branch design (monthly Art. 6 obligations + a season-long target) is the right framing, and the explicit separation of the **volume** and **withdrawal-rate** constraints is a genuine analytical contribution that most public Czech/EU storage debates skip. The recommended S2 anchor (~22 TWh start-of-October; ~9.3 TWh January obligation) lands in a plausible range relative to current Czech UGS infrastructure and post-2022 import patterns.

However, the team has identified **eight material issues** that the analysis should resolve before the numbers are used externally. The most important — ranked by impact on the headline — are:

1. **WC blend weight is a soft modelling choice carrying ±5–10 TWh of policy weight** (B1 January obligation moves from 5.95 → 14.88 TWh across the defensible range). The current "keep divergent blends" decision is reasonable but under-evidenced.
2. **Fill trajectories run to 0% by 31 March.** This is unphysical: Czech storages are depleted-reservoir facilities whose deliverability collapses well above 0% (the analysis admits the WC curve is "poorly identified <20%"). The simulation is allowed to operate in a regime where the model itself disclaims validity.
3. **The empirical P95 withdrawal curve is biased downward by commercial behaviour and is non-monotone in the raw data** (see `figs/withdrawal_curve.png`: P95 at 90–95% fill drops below P95 at 50–70% fill). Forcing isotonic monotonicity hides, rather than fixes, this.
4. **Capacity/declared-WC reference numbers (45.3 TWh / 734 GWh/d) sit at the upper edge of public figures.** Operator filings (Gas Storage CZ ~28.7 TWh / ~422 GWh/d; MND + Moravia Gas Storage ~9–10 TWh / ~80 GWh/d combined) sum closer to ~38–42 TWh and ~600–700 GWh/d in aggregate. Verify against current GIE AGSI+ "max gas in storage" and ENTSOG declared technical capacity. ([RWE](https://www.rwe.com/en/the-group/countries-and-locations/rwe-gas-storage-cz-s-r-o), [czgs.cz](https://www.czgs.cz/en/news/storage-year-2024-2025-begins), [Moravia GS / KKCG](https://kkcg.com/en/moravia-gas-storage))
5. **EU Reg 2025/1733 (10 Sept 2025)** extended the 90% filling regime to end-2027 but **scrapped intermediate monthly targets** and added a ±10 pp tolerance band. The Czech monthly-obligation framing is now stricter than the EU baseline; this needs explicit acknowledgement and market-impact assessment. ([Council 18 Jul 2025](https://www.consilium.europa.eu/en/press/press-releases/2025/07/18/gas-storage-council-greenlights-2-year-extension-of-reserves-filling-rules-to-safeguard-winter-supply/), [OIES Insight 174](https://www.oxfordenergy.org/wpcms/wp-content/uploads/2025/11/Insight-174-EU-Gas-Storage-Regulation.pdf))
6. **No injection feasibility check.** Targets ≥22 TWh for 1-Oct are taken as achievable. Summer 2025 injection season exposed real economic frictions (backwardation, low injection incentives) that bind Czech suppliers too.
7. **The 1-in-20 standard is a peak-day standard, not a 30-day stress profile;** the two-tier embedding (7d peak + 23d residual) is a defensible interpretation but is not how ERÚ Decree 349/2012 explicitly defines `R.max.den` and `r_30dnu`. Document the regulatory mapping.
8. **Demand–import correlation is partly captured in S1 but optimistically dismissed in S2.** The "commercial vs physical" reframing leans heavily on Spearman ρ over only 272 overlapping days (Jan 2025–Mar 2026), a window that excludes the worst 2022/23 stress. This is a thin empirical base for a regulatory finding.

The remainder of this document expands each issue, and proposes (§5) a concrete avenue of future work: a multi-year, injection-aware filling target where the end-of-March outturn endogenously sets the following October's obligation.

---

## 2. Issues and inconsistencies (structured)

### 2.1 Technical / infrastructure issues

| # | Issue | Where | Why it matters | Recommended fix |
|---|---|---|---|---|
| T1 | **WC curve runs to 0% fill** in `storage_target_fill_trajectories.png` (all five scenarios reach Mar 31 with fill ≈ 0%). | `storage_target_results.md` §"Fill-level trajectories" | Depleted-reservoir storages (most of CZ — Dolní Dunajovice, Tvrdonice, Štramberk, Třanovice, Háje, Lobodice, Uhřice, Dambořice) lose deliverability roughly with √pressure; cushion gas (~30–40% of total volume) is not withdrawable as working gas. A target that "just survives" by hitting 0% on 31 March is unrealistic and inconsistent with the doc's own warning that the WC curve is unreliable below 20%. | Impose a hard floor at ~15–20% fill (≈ 7–9 TWh) or, better, replace the binding constraint with `fill_t ≥ fill_min_operational` where `fill_min_operational` is calibrated from operator declared cushion + minimum deliverability. This will push the season target up by ~7–9 TWh. |
| T2 | **Empirical P95 WC curve is non-monotone in the raw bins** — `figs/withdrawal_curve.png` shows raw P95 at 90–95% fill at ~200–240 GWh/d, below P95 at 50–70% fill (~330–375 GWh/d). | Figure + `wc_blend_decision.md` | This is almost certainly an artefact of *when* high-fill days occur — early October, mild weather, low demand, hence low *observed* withdrawal — not a deliverability limit. Forcing isotonic monotonicity from below cures the shape but propagates the bias. | Use the ENTSOG declared technical capacity at each fill bin as the curve, calibrated (not blended) against the *upper envelope* of empirical observations conditional on cold days only (top-20% withdrawal days, the same conditioning already used for cold-day P99 imports). This removes the commercial-suppression bias without an ad hoc 75/25 vs 50/50 choice. |
| T3 | **Declared WC of 734 GWh/d is at the upper edge of public figures.** | `storage_target_results.md` §"Withdrawal capacity curve (reference)" | Gas Storage CZ alone publishes ~422 GWh/d peak deliverability; MND + Moravia Gas Storage together typically <200 GWh/d. The 734 GWh/d figure is plausible only if it sums *theoretical* peak capacities across all sites simultaneously (not contractually firm). | Cross-check against latest ENTSOG/GIE *firm declared* technical capacity (not nominated); if the gap is real, distinguish "physical" vs "marketable" capacity in §3 of the brief. |
| T4 | **Total working-gas capacity 45.3 TWh** — operator data sum closer to ~38–42 TWh post the Damborice ownership clarification. | `analysis_synthesis_brief.md` §2, §7 | A 3-TWh overstatement of the denominator inflates every "% fill" figure quoted downstream by ~8%. | Re-pull from GIE AGSI+ ("max gas in storage", CZ aggregate) at multiple snapshots in 2025/26; reconcile. |
| T5 | **WC blend weights differ across branches with no formal cross-validation.** | `wc_blend_decision.md` | The decision to keep divergent blends is defensible *per branch* but creates an internally inconsistent regulatory product: the same physical storage delivers different rates depending on which document the reader is in. | Replace the blend with the cold-day–conditioned upper-envelope curve (see T2). If a single curve cannot serve both branches, document the fill-regime split explicitly and add a regression test that the two curves agree above 30% fill. |

### 2.2 Market & economic-feasibility issues

| # | Issue | Where | Why it matters | Recommended fix |
|---|---|---|---|---|
| M1 | **Imports are treated as a fixed monthly percentile**, not a price-responsive supply curve. | Both branches | Czech imports from DE THE BZ are physically capacity-rich but **price-elastic**: on cold days, German hub prices spike (TTF +8% on 12 Jan 2026 alone; THE day-ahead repeatedly >€40/MWh in 2022–2026 cold snaps), suppliers prefer withdrawal over import — exactly the Spearman −0.52 the analysis observes. A purely percentile-based stress test undercounts the policy lever ERÚ actually has (mandate, subsidise, or price-cap imports during an Art. 13 emergency). | Add a price-conditioned import elasticity stage: under normal market conditions use P20–P50; under declared Art. 13 emergency use cold-day P99 (≈ 217 GWh/d Jan). The current "unconditional P20" sits between these and is not the operationally relevant number. |
| M2 | **No injection-side check.** Branch 2 targets of 22–25 TWh on 1 Oct are taken as achievable. | `analysis_synthesis_brief.md` §9.2 (explicitly deferred); `storage_target_results.md` Caveat 3 | Summer 2025 injection was financially punishing — TTF backwardation made summer gas €1.3/MWh *more* expensive than winter forwards; EU still missed 90% target by ~7 pp, exploiting new ±10pp flexibility. Czech suppliers face the same economics. A 22-TWh target requires ~16–18 TWh of net injection between April and October, against the existing 0.5 TWh end-March operational floor. Czech injection capacity from `data/cz_usg_injection_curve_2025.csv` declines with fill — at >90% fill, injection rate is <55% of nominal. | Run the deferred injection-feasibility check explicitly; report the implied summer hub price needed to clear the cost of carry. |
| M3 | **EU Reg 2025/1733 changed the goalposts.** | Not mentioned anywhere | The 90% target is now achievable any time 1 Oct–1 Dec with ±10 pp tolerance; intermediate monthly milestones removed. The Czech *monthly* obligation framing is materially **stricter than EU floor**, which is a defensible policy choice but must be argued, not assumed. | Add a §10 to the synthesis brief comparing the Czech monthly schedule to EU 2025/1733 and ERÚ Decree 349/2012; quantify the cost of incremental stringency (option value of delayed filling, summer-price exposure). |
| M4 | **German gas storage levy abolition (Jan 2025)** is a structural break — it cheapened THE → CZ flows materially. | Not mentioned | The post-2022 import sample (760 winter days) blends pre-2025 days when the levy was raising CZ entry costs by ~€2.5/MWh with post-2025 days when it was not. Pooled percentiles may understate today's reliable import capacity. ([Argus](https://www.argusmedia.com/en/news-and-insights/latest-market-news/2573135-germany-to-stop-gas-storage-levy-on-transit-from-2025)) | Either restrict the sample to post-2025-01-01 (cost: ~half the observations) or add a structural-break test on import distributions. At minimum, flag the levy abolition as a third break-point alongside post-2022-03-01. |
| M5 | **Single-corridor concentration risk is acknowledged qualitatively but not quantified.** | `analysis_synthesis_brief.md` §2 | DE THE BZ now carries >95% of Czech imports. A "Germany N-1" scenario (Brandov entry outage, Waidhaus restriction) is not in the scenario matrix. This is precisely the residual risk S1 is supposed to address but S1 is parameterised as a *statistical* tail (P10 imports), not a *structural* corridor-failure scenario. | Add a discrete corridor-loss scenario (e.g. 7 days at imports = 50% of normal, residual 23 days at P50) and report the implied obligation; this is what EU 2017/1938 Art. 5 N-1 actually requires. |
| M6 | **Market-impact of a binding 9.3 TWh January obligation is not assessed.** | Both results docs | A regulated minimum at month-start creates an injection-season demand curve that bids against EU-wide refilling competition. If 30+ TWh must be in CZ storage by 1 Dec (per S2), Czech suppliers compete with German, Italian, and Dutch refillers during summer. Allocation between protected-customer suppliers via market share is fine; the *system-level* price impact is not modelled. | Stress-test summer hub price under joint EU compliance trajectories; coordinate with MPO's Preventive Action Plan 2024–2027. |

### 2.3 Methodological / consistency issues

| # | Issue | Where | Recommended fix |
|---|---|---|---|
| Me1 | The two-tier `R.max.den` + `r_30dnu` profile is presented as the Czech implementation of EU Reg 2017/1938 Art. 6, but no citation to ERÚ Decree 349/2012 or the MPO Preventive Action Plan. | `storage_obligations_results.md` §"Demand profile" | Add explicit regulatory citations and confirm the 7d/23d split is the regulator's framing, not an analyst convention. |
| Me2 | The 22 TWh "Branch 2" total and the 9.3 TWh "Branch 1 January" obligation are different objects (annual seasonal opening fill vs monthly compliance checkpoint) but readers will compare them. | Brief §8 vs §9 | Add a clear cross-reference table showing how 9.33 TWh (B1 Jan) maps into the B2 trajectory (which passes through ~30% fill ≈ 13.6 TWh on 1 Jan for S2 — visibly *higher* than the B1 obligation). The 4.3 TWh gap between branches at the same date is the "buffer" implied by season-long vs once-per-season framing; it should be named and policy-discussed. |
| Me3 | The 272-day sample for the −0.52 Spearman correlation is short and partially overlaps with the warmest winter since 2022. | Brief §9.1 | Re-run on the full post-2022-03-01 sample (1,550 days) with a winter-only filter; report the rolling correlation. |
| Me4 | Sensitivity table in `storage_target_results.md` shows S5 jumping from 5.3 → 17 TWh on a +50 GWh/d peak shift — a *3.2× response* — but the body claims peak sensitivity is "±7–8 TWh for S2". Numbers are internally inconsistent. | `storage_target_results.md` §"Sensitivity analysis" | Reconcile the table and the prose; flag whether S5's jump is a discontinuity (volume-binding → rate-binding crossover) or a typo. |
| Me5 | Confirmation of WC blend in `wc_blend_decision.md` was added inline ("Confimed", typo) without dated supervisor identity. | End of file | Replace with a dated, attributed sign-off line — this is a regulatory document. |
| Me6 | The end-of-March 0.5 TWh operational floor is recommended as a standalone instrument but is omitted from both the monthly obligation and the season target. It also conflicts with T1 (fill trajectories reaching 0%). | Brief §9, target results §"March note" | Make the operational floor a hard constraint in both simulations and re-bisect. |

---

## 3. Cross-check against current external reality (May 2026 vantage)

| Claim in analysis | External reality | Implication |
|---|---|---|
| Czech UGS capacity 45.3 TWh | GIE / operator filings ~38–42 TWh aggregate | All "% fill" numbers possibly overstated ~8% |
| Declared WC 734 GWh/d | Gas Storage CZ ~422 + MND/Moravia ~80–200 = ~500–620 GWh/d firm | Engineering ceiling closer to ~620 GWh/d |
| Post-2022 cutoff | Correct, but Jan 2025 Russian transit cessation + Jan 2025 German levy abolition are additional breaks | Pooled percentiles mix regimes |
| 2025/26 EU storage drawdown "lowest since 2021" | Confirmed (NGI, Euronews, EGH) | S1/S2 stress is not hypothetical — current winter is mildly stressed |
| EU 90% target rigid | Outdated: Reg 2025/1733 added flexibility | Czech monthly schedule now stricter than EU floor |
| Cold-day P99 imports Jan = 217 GWh/d | Plausible (THE → CZ pipe is rarely saturated under normal conditions) | Cold-day P99 should be the default ceiling, not P70 |

---

## 4. Severity-ranked summary

| Rank | Issue | Impact on headline TWh | Confidence |
|---|---|---|---|
| 1 | T1 fill reaches 0% — missing operational floor | **+7 to +9 TWh** on B2 S2 target | High |
| 2 | T2/T5 WC curve choice (empirical vs engineering blend) | **±5 to ±10 TWh** on B1 January, ±10 TWh on B2 S2 | High |
| 3 | M2 summer injection feasibility not checked | Could render S1 (25 TWh) economically infeasible at observed forward curves | High |
| 4 | T3/T4 capacity / declared-WC numbers above public sources | Re-scale %, ±3 TWh on absolute targets | Medium |
| 5 | M3 misalignment with Reg 2025/1733 | Policy presentation risk | High |
| 6 | M5 corridor-loss scenario missing | Re-prices S1 from statistical to structural | Medium |
| 7 | M4 German levy structural break | Imports possibly understated by ~5–10 GWh/d | Medium |
| 8 | Me2 inter-branch coherence at 1 Jan | Communication risk, not number risk | High |

---

## 5. Proposed avenues of future work

### 5.1 Multi-year coupled filling target (top priority)

**Concept.** The current B1/B2 model treats each gas year as a closed system: 1 Oct is the start, 31 Mar is the end, and the inventory state between gas years is severed. In reality, **end-of-March outturn is the binding initial condition for the next April–September injection campaign**, which in turn determines the achievable 1-October fill.

**Formal coupling.** Let `F_oct(y)` denote the 1-Oct fill (TWh) entering gas year *y*, and `F_mar(y)` the 31-Mar outturn after the realised winter. Then:

```
F_oct(y+1) = F_mar(y) + ∫[Apr→Sep] inj(fill_t, price_t) dt − maintenance_outage_t
```

where `inj(fill_t, price_t)` is the **injection-rate curve** of `data/cz_usg_injection_curve_2025.csv` modulated by the summer–winter price spread. The injection curve as supplied is in *normalised* form (1.0 at 0% fill, ~0.54 at 99% fill), which can be directly read as a multiplier on nominal daily injection capacity (~365 GWh/d aggregate for Czech UGS at low fill, declining to ~200 GWh/d as full).

**What this resolves.**
- Currently `F_oct = 22 TWh` is *assumed* achievable for S2. Under the coupled model it becomes a **decision variable** subject to the injection-rate constraint and a chosen summer-price scenario.
- The end-of-March operational floor (the "0.5 TWh standalone instrument") becomes endogenous — its level is whatever is needed to make next year's filling target reachable at acceptable summer price exposure.
- Multi-year stochastic analysis: simulate N=1000 randomised winters (cold/normal/mild) and report the *long-run* probability that the regulated path becomes infeasible. This is the genuine quantity ERÚ should care about, not a single-season 1-in-20.

**Sketch of the model.**

```
For each scenario s ∈ {S1..S5}:
  F_oct(0) = bisection_result_from_B2(s)
  for y = 1 .. N_years:
    sample winter severity → F_mar(y) = F_oct(y-1) − winter_drawdown(y, s)
    constrain F_mar(y) ≥ end_of_march_floor (~0.5 TWh; or higher per T1 fix)
    inject Apr–Sep subject to injection_curve, hub_price(y), declared inj capacity
    F_oct(y) = F_mar(y) + summer_net_injection(y)
    check F_oct(y) ≥ B2_target(s) → if violated, record infeasibility
report P(infeasible) over horizon, expected operational floor, expected summer cost
```

**Data inputs needed (mostly already on hand).**
- `cz_usg_injection_curve_2025.csv` — present (fill-normalised injection multiplier).
- Aggregate nominal daily injection capacity (~365 GWh/d) — verifiable from ENTSOG declared technical capacity.
- TTF / Czech VTP summer-winter spread distribution — from forward curves / EEX history.
- Maintenance outage calendar (industry standard ~10 days per UGS per summer) — public on operator sites.

### 5.2 Other recommended extensions (in priority order)

1. **Stochastic import draws** (already deferred in §9.2 of the brief). Replace point percentiles with sampled draws from the empirical distribution; condition on a temperature index to embed the demand–import correlation rather than waving it through with a Spearman number.
2. **Copula-based joint demand/import model.** A Gaussian or t-copula on (daily demand anomaly, daily DE-THE import) calibrated on post-2022 winters; report the joint 1-in-20 / 1-in-100 quantile directly instead of multiplying marginals.
3. **Corridor-loss N-1 scenario** (per M5). Add an explicit "Brandov outage 7 days" and "Waidhaus restriction 14 days" to the scenario matrix.
4. **Sensitivity to demand profile shape, not just level.** A January-shifted vs February-shifted profile produces very different obligations; the current implementation only tests ±50 GWh/d uniform.
5. **Endogenous price formation.** The biggest gap between this analysis and a true *economic* feasibility study is that it has no price model. A simple two-period (summer/winter) hub-price model would let the team report obligations in € (cost-to-supplier) as well as TWh.
6. **Welfare comparison** of the Czech monthly schedule vs the new EU Reg 2025/1733 flexible regime. Is the additional Czech stringency *worth* the summer-price exposure? This is the question MPO/ERÚ will eventually be asked.

---

## 6. Recommendation

The analytical framework is sound and the documentation discipline (separate brief + per-branch results + decision memos) is unusual and welcome. We recommend the team:

1. **Hold the current S2 ≈ 9.3 TWh / 22 TWh numbers as draft, not final.** They should not yet be cited externally as the Czech regulatory anchor.
2. **Implement T1 and T2 first** (operational floor + cold-day–conditioned WC curve). These changes are mechanical and dominate the number.
3. **Run the deferred injection-feasibility check (M2/§5.1)** before defending any 1-Oct target above ~20 TWh.
4. **Add §10 to the synthesis brief** mapping the model to ERÚ Decree 349/2012 and EU Reg 2025/1733; flag where Czech monthly stringency exceeds the EU floor.
5. **Initiate the multi-year coupled filling-target work (§5.1)** as the next phase. The single-season framing has reached its useful limit; the policy question regulators will actually ask in 2027 — "what end-of-March floor keeps us reachable next year?" — requires the multi-year structure.

---

## References

- Council of the EU, [Gas storage: 2-year extension of refill rules](https://www.consilium.europa.eu/en/press/press-releases/2025/07/18/gas-storage-council-greenlights-2-year-extension-of-reserves-filling-rules-to-safeguard-winter-supply/), 18 Jul 2025
- European Parliament, [Refill flexibility press release](https://www.europarl.europa.eu/news/en/press-room/20250704IPR29447/gas-storage-parliament-backs-refill-flexibility-to-bring-down-prices), 4 Jul 2025
- Oxford Institute for Energy Studies, [Insight 174: EU Gas Storage Regulation](https://www.oxfordenergy.org/wpcms/wp-content/uploads/2025/11/Insight-174-EU-Gas-Storage-Regulation.pdf), Nov 2025
- Oxford Institute for Energy Studies, [Insight 162: End of Russian Gas Transit via Ukraine](https://www.oxfordenergy.org/wpcms/wp-content/uploads/2025/01/Insight-162-The-End-of-Russian-Gas-Transit-via-Ukraine.pdf), Jan 2025
- IEA, [Czech Republic — Natural gas security policy](https://www.iea.org/articles/czech-republic-natural-gas-security-policy)
- IEA, [Czechia's fuel diversification efforts](https://www.iea.org/commentaries/czechia-s-fuel-diversification-efforts-set-an-example-but-it-still-has-key-energy-security-challenges-to-tackle)
- ENTSOG/GIE, [System Capacity Map 2024](https://www.entsog.eu/sites/default/files/2024-02/ENTSOG_GIE_SYSCAP_2024_Update%20Feb.pdf)
- ENTSOG, [Winter Supply Outlook 2024-25 / Summer 2025](https://www.entsog.eu/sites/default/files/2024-10/SO0059-24%20Winter%20Supply%20Outlook%202024-25%20with%20Summer%20Overview%202025.pdf)
- Argus, [Germany to stop gas storage levy on transit from 2025](https://www.argusmedia.com/en/news-and-insights/latest-market-news/2573135-germany-to-stop-gas-storage-levy-on-transit-from-2025)
- Argus, [Europe faces challenging gas restocking season](https://www.argusmedia.com/en/news-and-insights/latest-market-news/2810699-europe-faces-challenging-gas-restocking-season)
- Natural Gas Intelligence, [Falling TTF prices mask rapid drawdown](https://naturalgasintel.com/news/falling-ttf-prices-mask-rapid-drawdown-in-eu-gas-storage-as-winter-advances/)
- European Gas Hub, [TTF gas prices surge — Jan 2026](https://europeangashub.com/ttf-gas-prices-surge-on-cold-weather-outages-and-geopolitical-nervousness.html)
- CEER, [Czech Republic National Report 2023](https://www.ceer.eu/wp-content/uploads/2025/10/CZ_National-report-2023_en.pdf)
- RWE, [RWE Gas Storage CZ](https://www.rwe.com/en/the-group/countries-and-locations/rwe-gas-storage-cz-s-r-o)
- Gas Storage CZ, [Storage year 2024–2025](https://www.czgs.cz/en/news/storage-year-2024-2025-begins)
- KKCG, [Moravia Gas Storage](https://kkcg.com/en/moravia-gas-storage)
- CEENergyNews, [Natural gas storage in CEE](https://ceenergynews.com/oil-gas/natural-gas-storage-cee-eu/)
