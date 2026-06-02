# Development ideas

## Path handling

- **Production config** — for any deployment context, paths should come from env vars or a config file rather than being hardcoded.

## Data

- **Short demand proxy history** — domestic exit points (`Distribution` + `Final Consumers`) in the ENTSOG export file are only populated from January 2025, giving roughly one heating season of demand/import overlap. Investigate whether historical domestic demand data is available from another source (e.g. ERU, NET4GAS transparency reports) to extend the correlation analysis window.

## Distribution / sharing

- **Streamlit Cloud (current default)** — live at https://bsdrevamp-5oqwwmcjjsz8b2avrwrbww.streamlit.app; share URL on need-to-know basis. If the GitHub repo must become private before the BSD revamp is publicly communicated, Streamlit Cloud can deploy from private repos with no other changes.
- **Self-contained HTML/JS snapshot** — single `.html` file, works offline and from `file://`, no Python needed. For formal report archival or consumers behind firewalls. Build only at report milestone checkpoints — the JS port of the simulation math creates a maintenance obligation if done continuously. Build prompt: `docs/html_snapshot_build_prompt.md`.
- **ShinyLive with bundled files** — Shiny for Python app with `bsd/` and `data/` bundled via `shinylive export`; full Python model runs in Pyodide. Avoids the two-codebase problem but still requires a local HTTP server (`python -m http.server`) — cannot open from `file://` due to browser WASM security restrictions.

## Model extensions (Branch 2 — season fill target)

- **Stochastic import draws** — replace fixed monthly import percentiles with Monte Carlo draws to produce a distribution of outcomes rather than a single deterministic trajectory.
- **Summer injection feasibility check** — verify that the minimum 1-October fill level derived by `min_start_fill` is actually reachable given injection-rate constraints over the Apr–Sep period.
