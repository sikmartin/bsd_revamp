# Development ideas

## Path handling

- **Anchor data paths to `__file__`** — current `Path("data/...")` constants in `data.py` resolve against the caller's working directory, which works from notebooks launched at the project root but breaks elsewhere. Replacing them with `Path(__file__).parent.parent / "data" / "..."` would make the package location-independent.
- **Move data paths to `constants.py`** — currently in `data.py`, but they are project-wide configuration, not I/O logic. Consolidating into `constants.py` (or a dedicated `config.py`) keeps `data.py` focused.
- **Default path arguments on load functions** — once paths are anchored to `__file__`, it becomes safe to add `path=DATA_PATH_IMPORTS` defaults to `load_daily_imports` etc., reducing boilerplate at call sites.
- **Production config** — for any deployment context, paths should come from env vars or a config file rather than being hardcoded.

## Naming

- **Rename `bsd/demand.py`** — the module specifically handles peak demand profiles (R.max.den + r_30dnu), not demand in general. A name like `peak_demand.py` or `demand_profile.py` would better reflect its scope. Requires updating all imports across the codebase.
- **Rename data files** — `cz_gas_exports_2020-2026.csv` and `cz_gas_imports_2020-2026.csv` use commercial/accounting terminology; `cz_gas_exit_*` and `cz_gas_entry_*` better reflect that these cover all entry/exit points in the ENTSOG balancing zone model (not just border crossings). Requires updating `DATA_PATH_IMPORTS` / `DATA_PATH_EXPORTS` in `data.py` and any references elsewhere.

## Data

- **Short demand proxy history** — domestic exit points (`Distribution` + `Final Consumers`) in the ENTSOG export file are only populated from January 2025, giving roughly one heating season of demand/import overlap. Investigate whether historical domestic demand data is available from another source (e.g. ERU, NET4GAS transparency reports) to extend the correlation analysis window.

## Distribution / sharing

- **Streamlit Cloud (current default)** — live at https://bsdrevamp-5oqwwmcjjsz8b2avrwrbww.streamlit.app; share URL on need-to-know basis. If the GitHub repo must become private before the BSD revamp is publicly communicated, Streamlit Cloud can deploy from private repos with no other changes.
- **Self-contained HTML/JS snapshot** — single `.html` file, works offline and from `file://`, no Python needed. For formal report archival or consumers behind firewalls. Build only at report milestone checkpoints — the JS port of the simulation math creates a maintenance obligation if done continuously. Build prompt: `docs/html_snapshot_build_prompt.md`.
- **ShinyLive with bundled files** — Shiny for Python app with `bsd/` and `data/` bundled via `shinylive export`; full Python model runs in Pyodide. Avoids the two-codebase problem but still requires a local HTTP server (`python -m http.server`) — cannot open from `file://` due to browser WASM security restrictions.

## Model extensions (Branch 2 — season fill target)

- **Stochastic import draws** — replace fixed monthly import percentiles with Monte Carlo draws to produce a distribution of outcomes rather than a single deterministic trajectory.
- **Summer injection feasibility check** — verify that the minimum 1-October fill level derived by `min_start_fill` is actually reachable given injection-rate constraints over the Apr–Sep period.
