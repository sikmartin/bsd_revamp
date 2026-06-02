# Build prompt: self-contained HTML/JS snapshot

**When to use:** for formal report archival or consumers behind firewalls that
block the Streamlit Cloud URL. **Not** the primary distribution method —
the live app at https://bsdrevamp-5oqwwmcjjsz8b2avrwrbww.streamlit.app covers
routine sharing. Only build this at report milestone checkpoints; the JS port
creates a maintenance obligation if done continuously.

---

## Context for the executing agent

This project (`/Users/martinsik/Coding/bsd_revamp`) is a Czech UGS gas storage
sizing analysis toolkit. The primary interactive app is
`app/app.py` (Streamlit). The goal here is a **single self-contained `.html`
file** that replicates the app's two-tab UI, works offline, and opens from
`file://` with no server and no Python.

Always run Python with `uv run`.

---

## Step 1 — Pre-compute data

Create and run `scripts/precompute_html_data.py`. It imports the `bsd` package
(editable install), runs the full data pipeline, and writes a JSON file
`app_html/data.json`. The JSON schema:

```python
import bsd, json, numpy as np
from pathlib import Path

prof   = bsd.load_demand_profile()
curves = bsd.fit_withdrawal_curves()
imp    = bsd.compute_monthly_imports(bsd.DEFAULT_SCENARIOS_DICT)
p99c, p99u = bsd.compute_import_benchmarks()

fill_knots = list(range(0, 101, 5))          # 21 points: 0, 5, …, 100

data = {
    "CAPACITY_TWH": bsd.CAPACITY_TWH,
    "MONTH_ORDER": bsd.MONTH_ORDER,
    "DAYS_IN_MONTH": {str(k): v for k, v in bsd.DAYS_IN_MONTH.items()},
    "STRESS_PEAK_DAYS": bsd.STRESS_PEAK_DAYS,
    "STRESS_RESIDUAL_DAYS": bsd.STRESS_RESIDUAL_DAYS,
    "WC_FILL_KNOTS": fill_knots,
    "WC_EMPIRICAL_KNOTS":    [round(curves.empirical(fp), 4)    for fp in fill_knots],
    "WC_ENGINEERING_KNOTS":  [round(curves.engineering(fp), 4)  for fp in fill_knots],
    "MONTHLY_IMPORTS": {
        key: {str(m): round(float(imp[key][m]), 4) for m in bsd.MONTH_ORDER}
        for key in imp
    },
    "P99_COLD":   {str(m): round(float(p99c[m]), 4) for m in bsd.MONTH_ORDER},
    "P99_UNCOND": {str(m): round(float(p99u[m]), 4) for m in bsd.MONTH_ORDER},
    "PEAK_GWH_D":     {str(m): round(float(prof.peak[m]), 4)     for m in bsd.MONTH_ORDER},
    "RESIDUAL_GWH_D": {str(m): round(float(prof.residual[m]), 4) for m in bsd.MONTH_ORDER},
}

Path("app_html").mkdir(exist_ok=True)
Path("app_html/data.json").write_text(json.dumps(data, indent=2))
```

Run: `uv run python scripts/precompute_html_data.py`

---

## Step 2 — Build `app_html/index.html`

A single HTML file. All external resources (Chart.js) must be inlined or
loaded from CDN with a local fallback so the file works offline. Prefer
inlining Chart.js (download and paste the minified bundle into a `<script>`).

### Overall structure

```
<html>
  <head>  styles  </head>
  <body>
    sidebar (fixed left, ~260px)
    main area
      tabs: "Měsíční povinnosti" | "Sezónní cíl"
    footer disclaimer
  </body>
  <script>
    const DATA = { /* paste data.json contents here */ };
    /* simulation functions */
    /* UI logic */
    /* chart rendering */
  </script>
</html>
```

### Sidebar controls (map from `app/app.py`)

| Control | Type | Default |
|---|---|---|
| Scénář | `<select>` | S2 |
| Vlastní percentil (shown when custom selected) | range slider 5–70 | 20 |
| Těžební křivka | radio (3 options) | Blend |
| Větev 1 — váha inženýrské (shown for Blend) | range slider 0–100 step 5 | 50 |
| Větev 2 — váha inženýrské (shown for Blend) | range slider 0–100 step 5 | 75 |
| Importní strop P99 | radio (2 options) | Cold days |
| Posun špičky (GWh/d) | range slider −50 to +50 step 10 | 0 |

### JavaScript simulation functions

Port these directly from `bsd/obligations.py` and `bsd/target.py`:

```javascript
// Linear interpolation on WC knots (step 5, 0..100)
function wcInterp(fp, knots) {
  fp = Math.max(0, Math.min(100, fp));
  const i = Math.min(Math.floor(fp / 5), 19);
  const t = (fp - i * 5) / 5;
  return knots[i] * (1 - t) + knots[i + 1] * t;
}

function wcBlend(fp, engWeight) {
  const e = wcInterp(fp, DATA.WC_EMPIRICAL_KNOTS);
  const g = wcInterp(fp, DATA.WC_ENGINEERING_KNOTS);
  return (1 - engWeight) * e + engWeight * g;
}

// Branch 1: 30-day stress test for one month
// Returns {feasible, fillTrajectory}
function simulateMonth(startFill, month, impGWhD, engWeight, peakShift) {
  const peak    = DATA.PEAK_GWH_D[month] + peakShift;
  const resid   = DATA.RESIDUAL_GWH_D[month] + peakShift;
  const gapPeak  = Math.max(0, peak - impGWhD);
  const gapResid = Math.max(0, resid - impGWhD);
  const gaps = [...Array(DATA.STRESS_PEAK_DAYS).fill(gapPeak),
                ...Array(DATA.STRESS_RESIDUAL_DAYS).fill(gapResid)];
  const delta = 100.0 / (DATA.CAPACITY_TWH * 1000);  // % per GWh
  let fill = startFill;
  const traj = [fill];
  for (const g of gaps) {
    if (wcBlend(fill, engWeight) < g - 1e-9) return {feasible: false, fillTrajectory: traj};
    fill -= g * delta;
    if (fill < -1e-9) return {feasible: false, fillTrajectory: traj};
    traj.push(fill);
  }
  return {feasible: true, fillTrajectory: traj};
}

function minStartFillMonth(month, impGWhD, engWeight, peakShift) {
  const sim = (fp) => simulateMonth(fp, month, impGWhD, engWeight, peakShift).feasible;
  if (!sim(100)) return null;
  if (sim(0))   return 0;
  let lo = 0, hi = 100;
  while (hi - lo > 0.01) {
    const mid = (lo + hi) / 2;
    sim(mid) ? hi = mid : lo = mid;
  }
  return hi;
}

// Branch 2: Oct–Mar daily simulation
// Returns {feasible, fillTrajectory, headroomTrajectory, bindingConstraint}
function simulateSeason(startFill, impDict, engWeight, peakShift, floorTwh = 0.5) {
  const months = DATA.MONTH_ORDER;
  const daysMap = DATA.DAYS_IN_MONTH;
  const delta = 1.0 / (DATA.CAPACITY_TWH * 10);  // % per GWh/d daily
  let fill = startFill;
  const fillTraj = [fill], headroom = [];
  for (const m of months) {
    const days = daysMap[m];
    const demand = DATA.PEAK_GWH_D[m] + peakShift;
    const imp    = impDict[m];
    const gap    = Math.max(0, demand - imp);
    for (let d = 0; d < days; d++) {
      const maxWc = wcBlend(fill, engWeight);
      headroom.push(maxWc - gap);
      if (maxWc < gap - 1e-9)
        return {feasible: false, fillTrajectory: fillTraj, headroomTrajectory: headroom, bindingConstraint: "withdrawal rate"};
      fill -= gap * delta;
      if (fill < -1e-9)
        return {feasible: false, fillTrajectory: fillTraj, headroomTrajectory: headroom, bindingConstraint: "volume"};
      fillTraj.push(fill);
    }
  }
  if (fill * DATA.CAPACITY_TWH / 100 < floorTwh - 1e-9)
    return {feasible: false, fillTrajectory: fillTraj, headroomTrajectory: headroom, bindingConstraint: "end-of-season floor"};
  return {feasible: true, fillTrajectory: fillTraj, headroomTrajectory: headroom, bindingConstraint: null};
}

function minStartFillSeason(impDict, engWeight, peakShift, floorTwh = 0.5) {
  const sim = (fp) => simulateSeason(fp, impDict, engWeight, peakShift, floorTwh).feasible;
  if (!sim(100)) return null;
  if (sim(0))   return 0;
  let lo = 0, hi = 100;
  while (hi - lo > 0.01) {
    const mid = (lo + hi) / 2;
    sim(mid) ? hi = mid : lo = mid;
  }
  return hi;
}
```

### Custom percentile interpolation

The raw daily import data is not available in the browser. Interpolate between
the two bracketing stored scenarios (S1=P10, S2=P20, S3=P30, S4=P50, S5=P70):

```javascript
function interpolateImports(pct) {
  const anchors = [{p: 10, key: "S1"}, {p: 20, key: "S2"}, {p: 30, key: "S3"},
                   {p: 50, key: "S4"}, {p: 70, key: "S5"}];
  const lo = anchors.filter(a => a.p <= pct).at(-1) || anchors[0];
  const hi = anchors.filter(a => a.p >= pct)[0]     || anchors.at(-1);
  if (lo.key === hi.key) return DATA.MONTHLY_IMPORTS[lo.key];
  const t = (pct - lo.p) / (hi.p - lo.p);
  return Object.fromEntries(
    DATA.MONTH_ORDER.map(m => [m, DATA.MONTHLY_IMPORTS[lo.key][m] * (1-t)
                                  + DATA.MONTHLY_IMPORTS[hi.key][m] * t])
  );
}
```

### Charts

Use Chart.js (inline the minified bundle). Two charts per tab:

- **Tab 1 left:** horizontal bar chart, months on Y-axis, obligation TWh on X
- **Tab 1 right:** line chart, January 30-day fill trajectory (%)
- **Tab 2 left:** line chart, Oct–Mar fill trajectory (%) with horizontal lines at
  0.5/CAPACITY_TWH*100 (red dashed) and 20% (grey dashed); X-axis ticks at
  month starts
- **Tab 2 right:** line chart, headroom trajectory (GWh/d) with red dashed line at 0

### Tables

Use plain `<table>` elements styled with CSS. No JS table library needed.

### Czech month names

```javascript
const MONTH_NAMES_CS = {10:"Říjen", 11:"Listopad", 12:"Prosinec",
                         1:"Leden",  2:"Únor",      3:"Březen"};
```

### Binding constraint labels

```javascript
const BINDING_CS = {
  "end-of-season floor": "Operační rezerva 31. 3.",
  "withdrawal rate": "Rychlost těžby",
  "volume": "Objem",
  "infeasible at 100%": "Neschůdné",
};
```

---

## Step 3 — Inline the data

After verifying `app_html/data.json` is correct, paste its contents as:

```html
<script>const DATA = /* paste data.json here */;</script>
```

This makes the file self-contained and openable from `file://`.

---

## Step 4 — Test

Open `app_html/index.html` directly in Chrome/Firefox (no server). Verify:
- Both tabs render tables and charts
- Sidebar controls update all outputs reactively (via `input` event listeners)
- The custom-percentile slider appears only when "Vlastní percentil" is selected
- Blend weight sliders appear only when "Blend" is selected
- January trajectory chart updates with scenario changes
- Season fill trajectory and headroom charts update

---

## Constraints

- No external network requests — Chart.js must be inlined or CDN with `crossorigin` fallback
- No `fetch()` or `XMLHttpRequest` to local files (breaks `file://` security model)
- All simulation math must match the Python implementation — verify against the
  Streamlit Cloud app output for S2 default settings before finalising
- `delta` formula in `simulateMonth`:  `100 / (CAPACITY_TWH * 1000)` (% per GWh)
- `delta` formula in `simulateSeason`: `1 / (CAPACITY_TWH * 10)`   (% per GWh/d daily)
- Residual demand also shifts by `peakShift` (matches `app/app.py` line 288)
