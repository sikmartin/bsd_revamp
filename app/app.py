"""Interaktivní průzkumník Czech UGS Storage Sizing — `uv run streamlit run app/app.py`"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st

import bsd
import bsd.jvs as jvs

# ---------------------------------------------------------------------------
# Stránka — konfigurace
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Zásobníky plynu — Česká republika",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

jvs.apply_style(theme="light", context="notebook")

# ---------------------------------------------------------------------------
# Nacachovaná data (načtou se jednou při startu)
# ---------------------------------------------------------------------------

@st.cache_resource
def load_data():
    prof   = bsd.load_demand_profile()
    curves = bsd.fit_withdrawal_curves()
    imp    = bsd.compute_monthly_imports(bsd.DEFAULT_SCENARIOS_DICT)
    p99c, p99u = bsd.compute_import_benchmarks()
    return prof, curves, imp, p99c, p99u

prof, curves, base_imp, p99_cold, p99_uncond = load_data()

# ---------------------------------------------------------------------------
# Postranní panel — společné ovládání
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Nastavení scénáře")

# Sekce: Scénář importu
st.sidebar.subheader("Importní scénář")
sc_options = {
    "S1 — Vysoký stres (P10)":  "S1",
    "S2 — Stresový (P20) ★":    "S2",
    "S3 — Mírný stres (P30)":   "S3",
    "S4 — Medián (P50)":        "S4",
    "S5 — Příznivý (P70)":      "S5",
    "Vlastní percentil …":      "custom",
}
sc_label = st.sidebar.selectbox(
    "Scénář",
    list(sc_options.keys()),
    index=1,  # S2 default
)
sc_key = sc_options[sc_label]

if sc_key == "custom":
    custom_pct = st.sidebar.slider(
        "Vlastní percentil importu (%)", min_value=5, max_value=70, value=20, step=1
    )
else:
    custom_pct = None

# Sekce: Těžební křivka
st.sidebar.subheader("Předpoklad těžební křivky")
wc_choice = st.sidebar.radio(
    "Křivka těžební kapacity",
    ["Empirická P95 (konzervativní)", "Blend (doporučeno)", "ENTSOG inženýrská (optimistická)"],
    index=1,
)
if wc_choice == "Blend (doporučeno)":
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        eng_weight_b1 = st.sidebar.slider(
            "Větev 1 — váha inženýrské křivky (%)", 0, 100, 50, step=5
        ) / 100
        eng_weight_b2 = st.sidebar.slider(
            "Větev 2 — váha inženýrské křivky (%)", 0, 100, 75, step=5
        ) / 100
else:
    eng_weight_b1 = 0.0 if wc_choice == "Empirická P95 (konzervativní)" else 1.0
    eng_weight_b2 = eng_weight_b1

# Sekce: Předpoklad importní kapacity
st.sidebar.subheader("Importní kapacitní strop")
import_ceiling_choice = st.sidebar.radio(
    "Strop pro analýzu P99",
    ["P99 ve studených dnech (doporučeno)", "P99 nepodmíněné"],
    index=0,
)
import_ceiling = p99_cold if import_ceiling_choice.startswith("P99 ve stud") else p99_uncond

# Sekce: Posun poptávky
st.sidebar.subheader("Citlivost poptávky")
peak_shift = st.sidebar.slider(
    "Posun špičky poptávky 1-z-20 (GWh/d)", -50, 50, 0, step=10
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Kapacita zásobníků: **{bsd.CAPACITY_TWH:.1f} TWh**  \n"
    "Data: ENTSOG fyzické toky, post-2022-03-01  \n"
    "GIE: zásobníková data do 28. 5. 2026"
)

# ---------------------------------------------------------------------------
# Výpočet (probíhá při každé změně ovládání)
# ---------------------------------------------------------------------------

def get_import_series():
    """Vrátí importní Series pro vybraný scénář (nebo vlastní percentil)."""
    if sc_key == "custom":
        daily = bsd.data.load_daily_imports(bsd.data.DATA_PATH_IMPORTS, cutoff=bsd.data.DEFAULT_CUTOFF)
        winter = daily[daily["month"].isin(bsd.MONTH_ORDER)]
        return pd.Series(
            {m: winter[winter["month"] == m]["GWh_d"].quantile(custom_pct / 100)
             for m in bsd.MONTH_ORDER}
        )
    return base_imp[sc_key]

imp_series = get_import_series()
# Wrap as a dict keyed by "active" for the bsd API
active_key = sc_key if sc_key != "custom" else "custom"
monthly_imp_single = {active_key: imp_series}

wc_b1 = curves.blend(eng_weight_b1)
wc_b2 = curves.blend(eng_weight_b2)

# Peak demand (potentially shifted)
peak_demand_shifted = prof.peak + peak_shift

# Branch 1: all months for the active scenario
@st.cache_data(ttl=300)
def run_b1(imp_arr, eng_w, shift):
    """eng_w and shift are cache-key scalars; imp_arr is a tuple for hashability."""
    imp_s = pd.Series(dict(zip(bsd.MONTH_ORDER, imp_arr)))
    wc_fn = curves.blend(eng_w)
    peak  = prof.peak + shift
    return {m: {
        "start_fill_TWh": bsd.min_start_fill_month(
            m, float(imp_s[m]), wc_fn, peak, prof.residual
        ) * bsd.CAPACITY_TWH / 100,
        "sim": bsd.simulate_month(
            (bsd.min_start_fill_month(m, float(imp_s[m]), wc_fn, peak, prof.residual) or 0.0),
            m, float(imp_s[m]), wc_fn, peak, prof.residual
        ),
    } for m in bsd.MONTH_ORDER}

@st.cache_data(ttl=300)
def run_b2(imp_arr, eng_w, shift, floor):
    imp_s = pd.Series(dict(zip(bsd.MONTH_ORDER, imp_arr)))
    wc_fn = curves.blend(eng_w)
    peak  = prof.peak + shift
    f = bsd.min_start_fill(
        "active", {"active": imp_s}, wc_fn, peak,
        end_of_march_floor_TWh=floor,
    )
    if f is None:
        return None, None, None
    twh = round(f * bsd.CAPACITY_TWH / 100, 2)
    sim = bsd.simulate(
        f, "active", {"active": imp_s}, wc_fn, peak,
        end_of_march_floor_TWh=floor,
    )
    probe = bsd.simulate(
        max(0.0, f - 0.05), "active", {"active": imp_s}, wc_fn, peak,
        end_of_march_floor_TWh=floor,
    )
    binding = probe["binding_constraint"] or "volume"
    return f, twh, sim, binding

imp_tuple = tuple(float(imp_series[m]) for m in bsd.MONTH_ORDER)

b1_results = run_b1(imp_tuple, eng_weight_b1, peak_shift)
b2_result  = run_b2(imp_tuple, eng_weight_b2, peak_shift, 0.5)

# Unpack B2
if len(b2_result) == 4:
    b2_fill_pct, b2_fill_twh, b2_sim, b2_binding = b2_result
else:
    b2_fill_pct, b2_fill_twh, b2_sim, b2_binding = None, None, None, None

# ---------------------------------------------------------------------------
# Záhlaví stránky
# ---------------------------------------------------------------------------
st.title("🔷 Zásobníky zemního plynu — Česká republika")
st.markdown(
    "**Dimenzování zásobníkových povinností a cílů plnění** na základě simulace "
    "spolehlivosti importů a těžební kapacity (ENTSOG fyzické toky, post-2022)."
)

sc_display = sc_label if sc_key != "custom" else f"Vlastní P{custom_pct}"
wc_display = (
    f"Blend B1 {eng_weight_b1:.0%}/B2 {eng_weight_b2:.0%}"
    if wc_choice == "Blend (doporučeno)"
    else wc_choice.split(" ")[0]
)
st.caption(
    f"Aktivní nastavení: **{sc_display}** · Těžební křivka: **{wc_display}** · "
    f"Posun poptávky: **{peak_shift:+d} GWh/d** · Importní strop: **{import_ceiling_choice.split(' ')[0]}**"
)

tab1, tab2 = st.tabs(["📅 Měsíční povinnosti (Větev 1)", "🎯 Sezónní cíl (Větev 2)"])

# ===========================================================================
# ZÁLOŽKA 1 — Měsíční povinnosti (Branch 1)
# ===========================================================================
with tab1:
    st.subheader("Minimální plnění zásobníku na začátku měsíce (TWh)")
    st.caption(
        "Minimální objem pracovního plynu, který musí být k dispozici na začátku každého "
        "měsíce, aby mohl být zvládnut 30denní stresový odběr dle EU Reg. 2017/1938 čl. 6."
    )

    # Tabulka obligací
    month_names_cs = {
        10: "Říjen", 11: "Listopad", 12: "Prosinec",
        1: "Leden", 2: "Únor", 3: "Březen"
    }
    rows = []
    for m in bsd.MONTH_ORDER:
        twh = b1_results[m]["start_fill_TWh"]
        rows.append({
            "Měsíc": month_names_cs[m],
            "Povinnost (TWh)": f"{twh:.2f}" if twh else "0.00",
            "% kapacity": f"{twh / bsd.CAPACITY_TWH * 100:.1f} %" if twh else "0.0 %",
        })
    df_b1 = pd.DataFrame(rows).set_index("Měsíc")
    st.dataframe(df_b1, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Sloupcový graf
        fig, ax = plt.subplots(figsize=(6, 3.5))
        months_cs = [month_names_cs[m] for m in bsd.MONTH_ORDER]
        vals = [b1_results[m]["start_fill_TWh"] or 0.0 for m in bsd.MONTH_ORDER]
        ax.bar(months_cs, vals, color=jvs.PALETTES["scenarios"][1], alpha=0.85)
        ax.axhline(bsd.CAPACITY_TWH, color="black", lw=1.0, ls="--",
                   label=f"Kapacita ({bsd.CAPACITY_TWH:.1f} TWh)")
        ax.set_ylabel("Min. plnění (TWh)")
        ax.set_title(f"Měsíční povinnosti — {sc_display}")
        ax.legend(fontsize=8)
        jvs.grid(ax=ax)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        # Lednová trajektorie
        fig, ax = plt.subplots(figsize=(6, 3.5))
        jan_sim = b1_results[1]["sim"]
        if jan_sim and jan_sim.get("fill_trajectory"):
            traj = jan_sim["fill_trajectory"]
            ax.plot(range(len(traj)), traj,
                    color=jvs.PALETTES["scenarios"][1], lw=2, label=f"{sc_display}")
        ax.axvline(bsd.STRESS_PEAK_DAYS, color="grey", lw=0.8, ls=":", alpha=0.7)
        ax.axhline(20, color="grey", lw=0.6, ls="--", alpha=0.6,
                   label="Zóna nízké spolehlivosti WK (<20 %)")
        ax.set_xlabel("Den stresového období")
        ax.set_ylabel("Plnění (%)")
        ax.set_title("Leden: průběh plnění (30denní stres)")
        ax.legend(fontsize=8)
        jvs.grid(ax=ax)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Předpoklady
    with st.expander("📋 Použité předpoklady importu a poptávky"):
        st.markdown("**Importní kapacita (GWh/d) — aktivní scénář**")
        imp_df = pd.DataFrame({
            "Měsíc": [month_names_cs[m] for m in bsd.MONTH_ORDER],
            f"{sc_display} (GWh/d)": [round(float(imp_series[m]), 1) for m in bsd.MONTH_ORDER],
            "P99 studené dny (GWh/d)": [round(float(p99_cold[m]), 1) for m in bsd.MONTH_ORDER],
        }).set_index("Měsíc")
        st.dataframe(imp_df, use_container_width=True)

        st.markdown("**Profil poptávky (1-z-20)**")
        dem_df = pd.DataFrame({
            "Měsíc": [month_names_cs[m] for m in bsd.MONTH_ORDER],
            "Špička 7d (GWh/d)": [round(float(peak_demand_shifted[m]), 1) for m in bsd.MONTH_ORDER],
            "Zbytek 23d (GWh/d)": [round(float(prof.residual[m] + peak_shift), 1) for m in bsd.MONTH_ORDER],
            "Celkem 30d (GWh)": [round(float(prof.total[m] + peak_shift * 30), 0) for m in bsd.MONTH_ORDER],
        }).set_index("Měsíc")
        st.dataframe(dem_df, use_container_width=True)

    # P99 benchmark
    st.subheader("Benchmark: povinnosti při importu P99 (studené dny)")
    ceil_rows = []
    for m in bsd.MONTH_ORDER:
        f = bsd.min_start_fill_month(m, float(import_ceiling[m]),
                                      curves.blend(eng_weight_b1),
                                      peak_demand_shifted, prof.residual)
        twh = round(f * bsd.CAPACITY_TWH / 100, 2) if f else 0.00
        ceil_rows.append({
            "Měsíc": month_names_cs[m],
            "Import P99 (GWh/d)": round(float(import_ceiling[m]), 1),
            "Povinnost (TWh)": f"{twh:.2f}",
        })
    st.dataframe(
        pd.DataFrame(ceil_rows).set_index("Měsíc"),
        use_container_width=True,
    )
    st.caption(
        "Nejpříznivější obhajitelný importní předpoklad — importy P99 ve studených dnech "
        "(dny v nejvyšším kvintilu čerpání zásobníků). Zobrazuje nejnižší obhajitelnou povinnost."
    )

# ===========================================================================
# ZÁLOŽKA 2 — Sezónní cíl (Branch 2)
# ===========================================================================
with tab2:
    st.subheader("Minimální plnění zásobníku k 1. říjnu (TWh)")
    st.caption(
        "Sezónní simulace od 1. října do 31. března. Bisekce hledá nejnižší startovní "
        "úroveň plnění, při které systém přežije zimní sezónu s rezervou ≥ 0,5 TWh k 31. 3."
    )

    if b2_fill_twh is None:
        st.error("Simulace není schůdná ani při 100% plnění. Zkontrolujte nastavení.")
    else:
        # Headline metriky
        col1, col2, col3 = st.columns(3)
        col1.metric("Min. plnění k 1. říjnu", f"{b2_fill_twh:.2f} TWh",
                    f"{b2_fill_pct:.1f} % kapacity")
        col2.metric("Kapacita zásobníků", f"{bsd.CAPACITY_TWH:.1f} TWh")
        binding_cs = {
            "end-of-season floor": "Operační rezerva 31. 3.",
            "withdrawal rate": "Rychlost těžby",
            "volume": "Objem",
            "infeasible at 100%": "Neschůdné",
        }.get(b2_binding or "", b2_binding or "—")
        col3.metric("Vázající omezení", binding_cs)

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            # Fill trajectory
            if b2_sim and b2_sim.get("fill_trajectory"):
                fig, ax = plt.subplots(figsize=(6, 4))
                traj = b2_sim["fill_trajectory"]
                month_starts = np.cumsum(
                    [0] + [bsd.DAYS_IN_MONTH[m] for m in bsd.MONTH_ORDER[:-1]]
                )
                month_labels_cs = ["Říjen", "Listopad", "Prosinec", "Leden", "Únor", "Březen"]
                ax.plot(range(len(traj)), traj,
                        color=jvs.PALETTES["scenarios"][1], lw=2.5, label=f"Plnění — {sc_display}")
                ax.axhline(0.5 / bsd.CAPACITY_TWH * 100, color="red", lw=1.0, ls="--",
                           alpha=0.7, label="Operační rezerva 31. 3. (0,5 TWh)")
                ax.axhline(20, color="grey", lw=0.6, ls="--", alpha=0.5,
                           label="Zóna nízké spolehlivosti WK")
                ax.set_xticks(month_starts)
                ax.set_xticklabels(month_labels_cs, fontsize=8)
                ax.set_ylabel("Plnění (%)")
                ax.set_title("Průběh plnění zásobníku: říjen–březen")
                ax.legend(fontsize=7.5)
                jvs.grid(ax=ax)
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        with col_chart2:
            # Headroom
            if b2_sim and b2_sim.get("headroom_trajectory"):
                fig, ax = plt.subplots(figsize=(6, 4))
                h = b2_sim["headroom_trajectory"]
                ax.plot(range(len(h)), h,
                        color=jvs.PALETTES["scenarios"][1], lw=1.8, label=sc_display)
                ax.axhline(0, color="red", lw=1, ls="--", label="Mezní rychlost těžby")
                ax.set_xticks(month_starts[:len(month_labels_cs)])
                ax.set_xticklabels(month_labels_cs, fontsize=8)
                ax.set_ylabel("Rezerva kapacity (GWh/d)")
                ax.set_title("Rezerva rychlosti těžby (max_wc − potřeba)")
                ax.legend(fontsize=7.5)
                jvs.grid(ax=ax)
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        # Citlivost na poptávku
        st.subheader("Citlivostní analýza — posun špičky poptávky")
        @st.cache_data(ttl=300)
        def sens_table(imp_arr, eng_w, floor):
            imp_s = pd.Series(dict(zip(bsd.MONTH_ORDER, imp_arr)))
            imp_d = {"active": imp_s}
            wc_fn = curves.blend(eng_w)
            rows_s = []
            for shift_val in [0, +50, -50]:
                pk = prof.peak + shift_val
                f = bsd.min_start_fill("active", imp_d, wc_fn, pk, end_of_march_floor_TWh=floor)
                label = "Základ" if shift_val == 0 else f"Špička {shift_val:+d} GWh/d"
                rows_s.append({
                    "Předpoklad poptávky": label,
                    "Min. plnění 1. října (TWh)": round(f * bsd.CAPACITY_TWH / 100, 2) if f else "—",
                    "Min. plnění 1. října (%)": f"{f:.1f} %" if f else "—",
                })
            return pd.DataFrame(rows_s).set_index("Předpoklad poptávky")

        df_sens = sens_table(imp_tuple, eng_weight_b2, 0.5)
        st.dataframe(df_sens, use_container_width=True)

        # P99 ceiling
        st.subheader("Benchmark: sezónní cíl při importu P99 (studené dny)")
        @st.cache_data(ttl=300)
        def ceiling_target(eng_w, ceiling_arr, floor):
            ceil_s = pd.Series(dict(zip(bsd.MONTH_ORDER, ceiling_arr)))
            imp_d = {"active": ceil_s}
            wc_fn = curves.blend(eng_w)
            f = bsd.min_start_fill("active", imp_d, wc_fn, prof.peak, end_of_march_floor_TWh=floor)
            return f

        ceil_arr = tuple(float(import_ceiling[m]) for m in bsd.MONTH_ORDER)
        f_ceil = ceiling_target(eng_weight_b2, ceil_arr, 0.5)
        if f_ceil:
            twh_ceil = round(f_ceil * bsd.CAPACITY_TWH / 100, 2)
            st.metric(
                "Sezónní cíl — import P99 studené dny",
                f"{twh_ceil:.2f} TWh",
                f"{f_ceil:.1f} % kapacity",
            )
            st.caption(
                "Nejpříznivější obhajitelný importní předpoklad. I při tomto optimistickém "
                "scénáři je třeba k 1. říjnu minimální objem plynu, aby byla zajištěna "
                "dodávka během stresové zimy."
            )

# ===========================================================================
# Kontextový panel
# ===========================================================================
with st.expander("📖 Metodika a předpoklady"):
    st.markdown("""
**Datová základna**
- Zdroj: ENTSOG Transparency Platform — Agregovaná data pro českou vyrovnávací zónu (NET4GAS)
- Indikátor: Fyzické toky (*Physical Flow*) — co skutečně překročilo hranici
- Časové omezení: od 1. 3. 2022 — vylučuje ruský tranzit a plnění 2021
- Zásobníková data: GIE AGSI+ pro českou agregaci

**Kapacita zásobníků**
- Použitá kapacita: **{cap:.4f} TWh** — hodnota z AGSI+ před zavedením inverzního uskladňování
- Poznámka: Aktuální hlášení AGSI mohou být navýšena o inverzní uskladnění; ověřte aktuální hodnotu

**Model — Větev 1 (měsíční povinnosti)**
- 30denní simulace na začátku každého měsíce (říjen–březen)
- 7 dnů na špičce `R.max.den` + 23 dnů na reziduálním průměru `r_30dnu`
- Stresová událost nastává jednou za sezónu → měsíce jsou nezávislé stresové testy
- Dodržování kontrolováno pouze k začátku měsíce (1. října, 1. listopadu atd.)

**Model — Větev 2 (sezónní cíl)**
- Denní simulace říjen–březen (182 dní)
- Každý den se používá celý špičkový denní odběr (konzervativní)
- Bisekce hledá nejnižší startovní plnění; zahrnuje operační rezervu 0,5 TWh k 31. 3.
- Vázající omezení: operační rezerva k 31. 3. (při 75/25 blend rychlost těžby dostačující)

**Těžební křivka (WK)**
- Empirická P95: konzervativní dolní mez — stlačena komerčním chováním při studených dnech
- ENTSOG inženýrská: fyzický strop — deklarovaná technická kapacita se slevou 10 %
- Blend: doporučená kombinace; B1 výchozí 50/50, B2 výchozí 75/25 (dle `docs/wc_blend_decision.md`)

**Výhrada k doporučení S2**
- S2 (P20 importů × 1-z-20 poptávka) ≈ 1-z-40 pod pozorovanou korelací poptávka/import
- Operační rezerva 31. 3. je doporučována jako samostatný regulatorní nástroj
- Výsledky jsou konzervativní horní meze — skutečná potřeba může být nižší
""".format(cap=bsd.CAPACITY_TWH))

# ===========================================================================
# Upozornění v zápatí
# ===========================================================================
st.divider()
st.markdown(
    """<small>
    ⚠️ <b>Výhrady:</b>
    Importy jsou modelovány jako pevné měsíční percentily (deterministický přístup) — skutečná variabilita
    by umožnila částečné vyrovnávání ze dne na den, výsledky jsou proto konzervativní horní odhady.
    Těžební křivka je špatně identifikována při plnění pod ~20 % (málo pozorování).
    Letní injektáž není kontrolována — doporučeno ověřit pro cíle nad ~22 TWh k 1. říjnu.
    Česká měsíční pravidla jsou přísnější než EU Reg. 2025/1733 — tento rozdíl je třeba v regulatorní
    diskusi explicitně zdůvodnit.
    Tato analýza není ekonometrickým modelem — cenovými odezvami importů ani tržním dopadem se nezabývá.
    </small>""",
    unsafe_allow_html=True,
)
