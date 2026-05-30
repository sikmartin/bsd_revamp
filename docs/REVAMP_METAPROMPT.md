# Revamp Metaprompt — Czech UGS Storage Sizing Package

**Audience:** the execution team (Claude Sonnet as lead engineer/analyst, Claude Haiku for
mechanical and verification tasks).
**Issued by:** project supervisor (Opus).
**Goal:** turn the analyst's groundwork into a presentable, maintainable package for the
authority's leadership: aligned models, a clean `bsd` library, updated docs, a working
Czech-language Streamlit explorer, and a finished Czech-language PowerPoint deck.

> Read this whole file before touching anything. Each phase has an **acceptance gate** —
> do not start the next phase until the current gate is green. Phases 0–4 are sequential.
> Phases 5 and 6 may run in parallel once Phase 4 is done.

---

## 0. Ground rules (apply to every phase)

- **Python execution:** always via `uv` (e.g. `uv run python`, `uv run pytest`,
  `uv run streamlit`). Never `pip install` or bare `python`. Add deps with `uv add`.
- **Never break the regression baseline.** `tests/test_regression.py`, `test_capacity.py`,
  `test_data.py` must pass before *and* after every phase. If a refactor legitimately
  changes a number, update the baseline **in the same commit** and say why in the message.
- **Single source of truth.** After extraction, no analytical constant or formula may exist
  in two places. Notebooks and the app import from `bsd`; they do not redefine logic.
- **Brand consistency.** All charts (notebooks, app, deck) use `bsd.jvs` styling and its
  palette (`scenarios` palette = S1→S5). The deck and app are in **Czech**; code, docstrings,
  and this repo's English docs stay in English.
- **Reproducibility.** Every figure in `figs/` must be regenerable by running its source
  notebook top-to-bottom with no manual steps.
- **Commit discipline.** Small, labelled commits per sub-task. End every commit message with
  the `Co-Authored-By` trailer the harness requires.

### Current-state map (what you are inheriting — verified by supervisor)

| Asset | State | Action |
|---|---|---|
| `bsd/data.py` | Nailed-down loaders. Good. | Keep; minor doc tidy only. |
| `bsd/capacity.py` | **OLD** flat "gap × 30" model (from `analysis.ipynb`). Superseded by the two simulation branches. | Mark legacy / retire — see Phase 2. |
| `bsd/jvs.py` | Czech chart styling + authority red/blue palette. Good. | Keep; reuse everywhere. |
| `bsd/plot.py` | Plot helpers. Good. | Keep; extend for new charts. |
| `notebooks/analysis.ipynb`, `storage_monthly.ipynb`, `withdrawal_curve.ipynb` | **Preparatory** — feed `analysis_synthesis_brief.md`. | Keep as provenance; do not promote their code. |
| `notebooks/storage_obligations.ipynb` (Branch 1) | **Final**, nailed-down. Defines `wc/wc_engineering/wc_blend`, `simulate_month`, `min_start_fill_month`. | Extract code to `bsd`. |
| `notebooks/storage_target.ipynb` (Branch 2) | **Final**, nailed-down. Defines `wc/wc_engineering/wc_blend`, `build_day_series`, `simulate`, `min_start_fill`, `wc_abs`, `solve`. | Extract code to `bsd`. |
| `docs/analysis_synthesis_brief.md` | Methodology bible, but **§8/§9 carry STALE numbers**. | Reconcile in Phase 1. |
| `docs/storage_obligations_results.md`, `storage_target_results.md` | **Current** headline results. **Authoritative** for the deck. | Cross-check, then treat as source of truth. |

### Known misalignments to resolve (do not ignore these)

1. **Stale brief numbers.** `analysis_synthesis_brief.md` §8 shows S2 season target **31.8 TWh**;
   `storage_target_results.md` shows **21.9 TWh**. §9 shows Jan S2 obligation **14.88 TWh**;
   `storage_obligations_results.md` shows **9.33 TWh** (and Dec/Feb similarly differ). The
   results docs are newer. The brief must be reconciled, with a dated note explaining the change
   (it is the withdrawal-curve blend that moved the numbers).
2. **Divergent withdrawal-curve blend.** Branch 1 uses a **50/50** empirical/engineering blend;
   Branch 2 uses **75/25**. See Phase 1 task A3 — you will analyse and **recommend** unify-vs-parameterise.
3. **Duplicated code.** `wc/wc_engineering/wc_blend` and the month-specific import-percentile
   tables are defined independently in both branch notebooks. Extraction removes the duplication.

---

## Phase 0 — Baseline snapshot  *(Haiku)*

1. `git init` in the project root. Add a sensible `.gitignore` (`.venv/`, `.pytest_cache/`,
   `__pycache__/`, `.DS_Store`, `.ipynb_checkpoints/`). **Do not** ignore `data/` or `figs/` —
   they are part of the deliverable and the app needs the data.
2. Stage everything, commit: `chore: baseline snapshot of analyst groundwork`.
3. Tag it: `git tag v1-baseline`.
4. Create and switch to a working branch: `git checkout -b revamp`.

**Acceptance gate:** `git tag` lists `v1-baseline`; `git status` clean on branch `revamp`;
`uv run pytest` green.

---

## Phase 1 — Model alignment & doc reconciliation  *(Sonnet leads; Haiku verifies numbers)*

This phase produces *decisions and a clean methodology story*, before any code moves.

**A1 — Re-run both final notebooks** (`uv run` via nbconvert/jupyter execute) and capture the
headline tables they actually produce today. Haiku: build a side-by-side table comparing
notebook output vs. the numbers printed in `storage_obligations_results.md` and
`storage_target_results.md`. Flag every cell that disagrees by >0.05 TWh.

**A2 — Cross-check the results docs are a fair representation of the models.** This is a
gating check for the deck (Phase 6 relies *only* on these two docs). Produce
`docs/results_crosscheck.md`: for each headline number in the two results docs, ✅/❌ against
freshly-run notebook output. Resolve every ❌ (fix the doc, or fix the notebook and explain).

**A3 — Withdrawal-curve blend: analyse and recommend.** The supervisor has asked the team to
*recommend* whether to unify the blend (one weight for both branches) or keep it parameterised
(per-branch documented weights). Deliverable: a short memo `docs/wc_blend_decision.md` that:
   - quantifies the impact on each branch's S2 headline of switching Branch 1 to 75/25 and
     Branch 2 to 50/50 (run it both ways);
   - states the analytical justification for each branch's current choice (Branch 2's 75/25 is
     defended in `storage_target_results.md`: season-long sim reaches low fill where the
     empirical curve is poorly identified);
   - gives a clear recommendation. **Pause and report this recommendation to the supervisor
     before implementing it** — it may change published numbers.
   - Whichever way it lands, the extracted code (Phase 2) must expose blend weight as an
     explicit parameter so the choice is visible and overridable.

**A4 — Reconcile `analysis_synthesis_brief.md`.** Update §8 and §9 tables to the current
results-doc numbers. Add a dated reconciliation note: *"Numbers updated <date>: superseded
figures reflected the pre-blend withdrawal curve; current figures use the blended curve — see
results docs."* Keep §1–§7 (methodology and preparatory analyses) intact; they are the model's
narrative provenance.

**Acceptance gate:** `docs/results_crosscheck.md` shows all ✅; `wc_blend_decision.md` written
and supervisor sign-off received; brief §8/§9 match the results docs; `uv run pytest` green.

---

## Phase 2 — Promote nailed-down code into `bsd`  *(Sonnet)*

Move the analytical logic from the two final notebooks into the library so it is usable by the
Streamlit app and ready for possible future productionisation. **Behaviour must not change** —
this is extraction, not redesign. Re-running the notebooks after extraction must reproduce the
same figures and numbers (guarded by regression tests).

Proposed module layout (adjust names if you find a cleaner cut, but keep one concern per module):

```
bsd/
  __init__.py        # re-export the public API; update module docstring
  constants.py       # NEW — CAPACITY_TWH=45.3, DECLARED_WC_GWH_D=734, WINTER_MONTHS, scenario percentiles
  data.py            # keep
  demand.py          # NEW — load r_max_den / r_30dnu; build the two-tier 7+23 day profile
  imports.py         # NEW — month-specific import percentile tables; P99 cold-day (top-20% withdrawal-day) logic
  withdrawal.py      # NEW — empirical-P95 isotonic curve, engineering curve, wc_blend(weight=...), wc_abs
  obligations.py     # NEW — Branch 1: simulate_month(), min_start_fill_month() (bisection)
  target.py          # NEW — Branch 2: build_day_series(), simulate(), min_start_fill(), solve() (sensitivity)
  scenarios.py       # NEW or fold into constants — Scenario dataclass + DEFAULT_SCENARIOS (S1–S5)
  capacity.py        # LEGACY flat model — see below
  plot.py            # keep; add trajectory + headroom + heatmap helpers used by app & deck
  jvs.py             # keep
```

Tasks:
1. Lift `wc`, `wc_engineering`, `wc_blend`, `wc_abs` into `bsd/withdrawal.py`. Blend weight is a
   parameter (default per Phase 1 A3 decision). Fit logic (isotonic regression on P95 envelope)
   moves here too, reading the GIE data via `bsd.data`.
2. Lift Branch 1 `simulate_month` / `min_start_fill_month` into `bsd/obligations.py`; Branch 2
   `build_day_series` / `simulate` / `min_start_fill` / `solve` into `bsd/target.py`.
3. Move the `WC_ASSUMPTION` / `IMPORT_ASSUMPTION` switches into function arguments (enums or
   string literals with validation), not module globals.
4. `capacity.py`: it is the superseded flat model. Decide one of — (a) keep it under a clear
   `# LEGACY: superseded by obligations.py/target.py` banner and a deprecation note in its
   docstring, or (b) move it to `bsd/legacy/`. Do **not** silently delete; `test_capacity.py`
   covers it. State your choice in the commit.
5. **Rewrite both final notebooks to be thin clients:** import from `bsd`, call the functions,
   render tables and the existing figures. No analytical code defined in-notebook. They become
   the human-readable narrative + chart generators; the library is the engine.
6. **Tests:** extend `tests/` with unit tests for `withdrawal`, `obligations`, `target`
   (assert the published S1–S5 headlines within tolerance). Keep `test_regression.py` as the
   end-to-end guard.

**Acceptance gate:** notebooks run top-to-bottom via `uv run` and regenerate identical `figs/`;
`uv run pytest` green including new tests; `grep` confirms `wc_blend`/percentile tables are
defined exactly once (in `bsd`).

---

## Phase 3 — Polish project structure  *(Haiku, Sonnet reviews)*

1. Remove cruft from version control: ensure `.DS_Store`, `.pytest_cache/`, `.ipynb_checkpoints/`
   are gitignored and untracked.
2. Reconcile dependency manifests: `pyproject.toml` is authoritative. Add `streamlit`,
   `python-pptx`, `seaborn`, `isotonic`/`scikit-learn` (already present), `nbconvert` (dev).
   Keep `environment.yml` in sync or note it as secondary.
3. Add a top-level `README.md` (English): one-paragraph purpose, the two-branch framing diagram
   (copy from `CLAUDE.md`), how to run notebooks, how to run the app (`uv run streamlit run app/app.py`),
   how to run tests, and a directory guide.
4. Create the target directory layout:
   ```
   app/        # Streamlit application (Phase 5)
   bsd/        # library
   data/       # inputs (unchanged)
   docs/       # methodology + results + this metaprompt + crosscheck
   figs/       # generated charts
   notebooks/  # narrative + chart generators
   tests/
   presentation/  # NEW — the .pptx and its build script (Phase 6)
   ```

**Acceptance gate:** `README.md` instructions work from a clean checkout (`uv sync` →
`uv run pytest` → notebooks run); `git status` clean.

---

## Phase 4 — Documentation refresh  *(Sonnet)*

1. Update the three `docs/*.md` to reference the new `bsd` modules instead of "the notebook"
   wherever they say "controlled by `WC_ASSUMPTION` in the notebook" → now a function argument.
2. Add a short `docs/architecture.md`: the module map, the data-flow (data → withdrawal/imports/
   demand → obligations/target → plots → app/deck), and the public API surface intended for
   future productionisation.
3. Ensure every `docs/*.md` cross-link still resolves after any file moves.

**Acceptance gate:** no doc references a deleted/renamed symbol; supervisor can read
`architecture.md` and locate any number's code path in one hop.

---

## Phase 5 — Streamlit app (Czech, self-contained)  *(Sonnet)*

A single interactive explorer for the **regulatory options**, runnable with
`uv run streamlit run app/app.py`, reading bundled `data/` and importing `bsd`. **No analytical
code in the app** — it is a thin UI over the library. All copy in **Czech**; charts use `bsd.jvs`.

Structure:
- **Branch selector / two tabs:** *Měsíční povinnosti* (Branch 1) and *Sezónní cíl* (Branch 2).
- **Shared sidebar controls:**
  - Scénář importu: S1–S5 preset **or** vlastní percentil (slider 5–70).
  - Předpoklad těžební křivky (`withdrawal`): empirická P95 / blend (s posuvníkem váhy) / ENTSOG inženýrská.
  - Předpoklad importu: scénářové percentily / P99 ve studených dnech.
  - Posun špičky poptávky (±50 GWh/d) — sensitivity.
- **Branch 1 tab outputs:** monthly obligation table (TWh) for the chosen settings, the
  obligations heatmap and bar chart, the import/demand assumption tables, and the P99 cold-day
  ceiling benchmark. Highlight S2 as anchor.
- **Branch 2 tab outputs:** the minimum 1-October fill (% and TWh) with binding-constraint flag,
  the fill-trajectory chart, the headroom chart, and the sensitivity table — all recomputed live
  from the sidebar settings.
- **Context panel:** a collapsible "Metodika a předpoklady" section summarising data vintage,
  the post-2022 cutoff rationale, and the 45.3 TWh capacity reference.
- **Caveats footer:** the key caveats (deterministic imports, withdrawal-curve assumption,
  correlation) in Czech, lifted from the results docs.

Quality bar: every number on screen must trace to a `bsd` call (no hardcoded results). Verify
the app launches and the controls recompute using the `webapp-testing` / Playwright tooling
before declaring done; capture one screenshot per tab into `figs/app_*.png` for the record.

**Acceptance gate:** `uv run streamlit run app/app.py` launches clean; changing each control
visibly updates tables/charts; S2 defaults reproduce the published headline numbers; screenshots
captured.

---

## Phase 6 — PowerPoint deck (Czech)  *(Sonnet drafts narrative + builds; Haiku checks every number against the docs)*

Use the **`pptx` document skill**. Source content **only** from `docs/storage_obligations_results.md`
and `docs/storage_target_results.md` (this is also the fairness cross-check from Phase 1 A2 — if a
number you want isn't in those docs, it doesn't go on a slide). Output `presentation/uskladneni_plynu.pptx`
plus the build script that generates it. Czech throughout; brand palette from `bsd.jvs`.

Make a **compelling case for why this approach beats the status quo** — weave these arguments in:
- **Opřeno o skutečně pozorovaná data** (ENTSOG fyzické toky, post-2022), ne o smluvní alokace
  ani o historická ruská tranzitní čísla.
- **Sofistikované, ale srozumitelné metody:** denní simulace zásobníku s vazbou na fyzickou
  těžební křivku — a vědomé zjednodušení (deterministické měsíční percentily, měsíční rámec)
  zvolené proto, že **srozumitelnost a auditovatelnost jsou hodnota sama o sobě** pro regulační debatu.
- **Soulad s EU nařízením 2017/1938 čl. 6** a se skutečným komerčním chováním trhu
  (záporná korelace poptávky a importu → konzervativní percentily).
- **Vázající omezení je rychlost těžby, ne objem** — klíčové zjištění, které pouhý TWh-cíl míjí.

Suggested slide flow (~12–14 slides), all in Czech:
1. Titul + jedna věta o účelu.
2. Otázka pro vedení: kolik plynu musí být v zásobnících na začátku zimy / měsíce?
3. Proč nový přístup (status quo vs. tento přístup — výše uvedené argumenty).
4. Data a rozsah (zdroj, post-2022 cutoff, 4 zimy, 45,3 TWh kapacita).
5. Předpoklady a vstupy (vysoká úroveň: poptávka 1-z-20, importní percentily, těžební křivka).
6. Dvě větve modelu — jeden snímek s rámcovým diagramem.
7. Větev 1 — měsíční povinnosti: tabulka + heatmapa; S2 jako kotva.
8. Větev 2 — sezónní cíl: 1-Oct fill tabulka + trajektorie naplnění.
9. Klíčové zjištění: rychlost těžby je vázající omezení (headroom graf).
10. Interpretace scénářů S1–S5 (S2 kotva, S1 fyzický stres).
11. Citlivost (těžební křivka a importní strop jako hlavní hybatele).
12. Výhrady a další kroky (stochastické importy, letní injektáž, kopule pro korelaci).
13. Doporučení + výzva k diskusi.

Haiku task: build a number-trace table — every figure on every slide ↔ the exact line in the
results docs it came from. Any slide number without a doc source is a defect.

**Acceptance gate:** `presentation/uskladneni_plynu.pptx` opens and renders; Haiku's number-trace
table shows 100% sourced-from-results-docs; supervisor review.

---

## Roles summary

| Phase | Lead | Support |
|---|---|---|
| 0 Baseline | Haiku | — |
| 1 Alignment | Sonnet | Haiku (number diff, crosscheck) |
| 2 Extraction | Sonnet | — |
| 3 Structure | Haiku | Sonnet (review) |
| 4 Docs | Sonnet | — |
| 5 Streamlit | Sonnet | Haiku (Czech copy proofing) |
| 6 Deck | Sonnet (build) | Haiku (number-trace audit) |

## Definition of done (whole package)

- `git tag v1-baseline` exists; revamp work on `revamp` branch with clean history.
- All analytical logic lives in `bsd`; defined exactly once; covered by passing tests.
- Two final notebooks run end-to-end as thin clients and regenerate all `figs/`.
- Brief reconciled; results docs cross-checked ✅; `architecture.md` written.
- Streamlit app launches, is fully Czech, recomputes live, defaults reproduce headlines.
- Czech `.pptx` built, every number sourced from the two results docs, makes the case for the approach.
- `uv run pytest` green throughout.

---

## Token intensity

> ⚠️ TOKEN INTENSITY WARNING
> Estimated execution cost: **~120–160 K output tokens** (well above the ~10 K Pro-session
> threshold; ~1.2–1.6× a conservative 100 K session quota).
> Drivers: Phase 2 code extraction + test authoring (~30–40 K), Phase 5 Streamlit build with
> Playwright verification (~30–45 K, incl. ~2.5 K per screenshot), Phase 6 deck build via pptx
> skill (~25–35 K), Phase 1 notebook re-runs and cross-check (~15–20 K).
> **Recommendation: split across at least 3 sessions** — (1) Phases 0–2, (2) Phases 3–4 + Phase 5
> app, (3) Phase 6 deck + final review. Commit at every acceptance gate so a session can resume
> cleanly from `git log`.
