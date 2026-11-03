"""
Streamlit dashboard: Digital Ad Budget Optimizer for a fictional
Pakistani footwear brand. ALL DATA IS SIMULATED.

Run locally (Command Prompt):  streamlit run src\\dashboard\\app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
for sub in ["optimizer", "analysis", "simulation"]:
    sys.path.insert(0, str(ROOT / "src" / sub))
from optimize import fit_curves, optimize, evaluate, response  # noqa: E402
from kpis import kpi_table  # noqa: E402
import generate_data as G  # noqa: E402

BRAND = "StepUp Footwear"
DATA_FILE = ROOT / "data" / "raw" / "ads_10000.csv"
PROC = ROOT / "data" / "processed"
ACCENT = "#FF6B35"
MUTED = "#8B95A9"
COLORS = {"Facebook": "#1877F2", "Instagram": "#E1306C", "Google": "#34A853",
          "TikTok": "#00BFB3", "YouTube": "#FF3B30"}

st.set_page_config(page_title="StepUp · Ad Budget Optimizer", page_icon="👟", layout="wide")

# ---------------- STYLE ----------------
CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1350px;}
h1, h2, h3 {letter-spacing: -0.02em;}
.hero {background: linear-gradient(115deg, #FF6B35 0%, #F7418F 45%, #7B2FF7 100%);
  border-radius: 22px; padding: 30px 34px; color: #fff; margin-bottom: 10px;
  box-shadow: 0 10px 40px rgba(123,47,247,0.25);}
.hero-kicker {font-size: .78rem; letter-spacing: .18em; font-weight: 700; opacity: .9;}
.hero h1 {color: #fff !important; font-size: 2.5rem; font-weight: 800; margin: 6px 0 4px; padding: 0;}
.hero p {font-size: 1.05rem; opacity: .95; margin: 0 0 6px;}
.badge {display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.35);
  padding: 4px 12px; border-radius: 999px; font-size: .8rem; margin: 10px 6px 0 0;}
.kpi {background: #151B2B; border: 1px solid #232B3E; border-radius: 16px; padding: 18px 20px; min-height: 118px;}
.kpi-label {color: #8B95A9; font-size: .75rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 600;}
.kpi-value {color: #F5F7FB; font-size: 1.55rem; white-space: nowrap; font-weight: 800; margin-top: 6px; line-height: 1.1;}
.kpi-sub {font-size: .85rem; margin-top: 6px;}
.plat {background: #151B2B; border: 1px solid #232B3E; border-top: 4px solid; border-radius: 14px;
  padding: 14px 16px; text-align: center;}
.plat-name {font-weight: 700; color: #F5F7FB;}
.plat-share {font-size: 1.7rem; font-weight: 800; margin: 2px 0;}
.plat-amt {color: #8B95A9; font-size: .82rem;}
.why {background: linear-gradient(135deg, rgba(255,107,53,.14), rgba(123,47,247,.14));
  border: 1px solid #2A3350; border-radius: 16px; padding: 18px 22px; margin: 16px 0 6px; line-height: 1.6;}
.section h3 {margin: 22px 0 0; font-weight: 800;}
.section p {color: #8B95A9; margin: 2px 0 8px;}
.side-brand {font-size: 1.4rem; font-weight: 800; margin-bottom: 6px;}
.side-brand span {display: block; font-size: .8rem; font-weight: 600; color: #FF6B35; letter-spacing: .12em;}
.stTabs [data-baseweb="tab-list"] {gap: 6px; flex-wrap: wrap;}
.stTabs [data-baseweb="tab"] {background: #151B2B; border-radius: 10px; padding: 8px 16px; height: auto;}
.stTabs [aria-selected="true"] {background: #FF6B35 !important;}
.stTabs [aria-selected="true"] p {color: #fff !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

pio.templates["stepup"] = go.layout.Template(layout=go.Layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#C9D1E0", family="Inter, Segoe UI, sans-serif", size=13),
    colorway=list(COLORS.values()),
    xaxis=dict(gridcolor="#232B3E", zerolinecolor="#232B3E"),
    yaxis=dict(gridcolor="#232B3E", zerolinecolor="#232B3E"),
    margin=dict(t=60, l=10, r=10, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    title=dict(font=dict(size=16, color="#F5F7FB"))))
pio.templates.default = "plotly_dark+stepup"


def show(fig, height=None):
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, theme=None)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def rs(x):
    return f"Rs. {x:,.0f}"


def card(label, value, sub="", sub_color="#4ADE80"):
    return (f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub" style="color:{sub_color}">{sub}</div></div>')


def section(title, subtitle=""):
    html(f'<div class="section"><h3>{title}</h3><p>{subtitle}</p></div>')


# ---------------- DATA + CACHED MODELS ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def get_curves():
    return fit_curves(load_data())


@st.cache_data
def bootstrap_curves(n_boot=50, seed=0):
    """Refit the curves on 50 random resamples of the data (with replacement)."""
    data = load_data()
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(data), len(data))
        try:
            out.append(fit_curves(data.iloc[idx]))
        except RuntimeError:
            pass  # skip the rare resample where the fit does not converge
    return out


@st.cache_data
def profit_curve(plats, slices, margin, min_share, max_share, max_budget):
    curves = get_curves()
    ps = {p: curves[p] for p in plats}
    out = []
    for b in np.linspace(100_000, max_budget, 50):
        al = optimize(ps, b, slices, min_share, max_share)
        t = evaluate(al, ps, slices, margin)
        out.append(dict(budget=b, revenue=t.revenue.sum(), profit=t.profit.sum()))
    return pd.DataFrame(out)


df = load_data()
curves = get_curves()
all_plats = list(curves)

# ---------------- SIDEBAR (with scenario presets) ----------------
DEFAULTS = dict(budget=1_000_000, margin=0.50, slices=60, platforms=list(all_plats),
                min_share=0, max_share=100)
PRESETS = {
    "⚖️ Balanced (default)": {},
    "📺 Keep YouTube alive (min 5% each)": dict(min_share=5),
    "🌙 Eid push (Rs. 2M budget)": dict(budget=2_000_000),
    "🔍 Google paused": dict(platforms=[p for p in all_plats if p != "Google"]),
    "🛡️ Spread risk (max 30% each)": dict(max_share=30),
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def apply_preset():
    chosen = PRESETS[st.session_state["preset"]]
    for k, v in DEFAULTS.items():
        st.session_state[k] = chosen.get(k, v)


with st.sidebar:
    html('<div class="side-brand">👟 StepUp<span>BUDGET LAB</span></div>')
    st.selectbox("Quick scenario", list(PRESETS), key="preset", on_change=apply_preset)
    st.divider()
    budget = st.number_input("Monthly ad budget (Rs.)", min_value=100_000,
                             max_value=50_000_000, step=100_000, key="budget")
    margin = st.slider("Gross margin on shoes", min_value=0.20, max_value=0.80, step=0.05,
                       key="margin", help="Share of revenue left after product cost. ASSUMPTION.")
    slices = st.slider("Ad slices per platform (days × ad sets)", min_value=15, max_value=180,
                       step=15, key="slices",
                       help="Default 60 = 30 days × 2 ad sets. Sets the scale. ASSUMPTION.")
    platforms = st.multiselect("Platforms allowed", all_plats, key="platforms")
    min_share = st.slider("Minimum share per allowed platform (%)", min_value=0, max_value=20,
                          key="min_share") / 100
    max_share = st.slider("Maximum share per platform (%)", min_value=20, max_value=100,
                          key="max_share") / 100
    st.caption("⚠️ All data is simulated. Assumptions are listed in the About tab.")

if not platforms:
    st.error("Pick at least one platform.")
    st.stop()
if min_share * len(platforms) > 1:
    st.error("Minimum shares add up to more than 100%. Lower the minimum.")
    st.stop()
if max_share * len(platforms) < 1:
    st.error("Maximum shares can't cover 100% of the budget. Raise the maximum.")
    st.stop()

# ---------------- OPTIMISE ----------------
sel = {p: curves[p] for p in platforms}
alloc_sel = optimize(sel, budget, slices, min_share, max_share)
alloc = {p: alloc_sel.get(p, 0.0) for p in all_plats}
rec = evaluate(alloc, curves, slices, margin)

hist = df.groupby("platform", observed=True)["spend"].sum()
hist = (hist / hist.sum()).to_dict()
avg_roas = (df.groupby("platform", observed=True)["revenue"].sum()
            / df.groupby("platform", observed=True)["spend"].sum())
best = str(avg_roas.idxmax())
strategies = {
    "Optimizer": alloc,
    "Equal split": {p: budget / len(all_plats) for p in all_plats},
    "Last year's split": {p: budget * hist[p] for p in all_plats},
    f"All on {best}": {p: (budget if p == best else 0.0) for p in all_plats},
}
comp = []
for name, al in strategies.items():
    t = evaluate(al, curves, slices, margin)
    comp.append(dict(strategy=name, revenue=t.revenue.sum(), profit=t.profit.sum()))
comp = pd.DataFrame(comp)
eq_rev = comp.loc[comp.strategy == "Equal split", "revenue"].iloc[0]
comp["vs_equal_%"] = (comp.revenue / eq_rev - 1) * 100

tot_rev, tot_profit = rec.revenue.sum(), rec.profit.sum()
opt_gain = comp.loc[comp.strategy == "Optimizer", "vs_equal_%"].iloc[0]
allbest_rev = comp.loc[comp.strategy == f"All on {best}", "revenue"].iloc[0]
breakeven = 1 / margin

# ---------------- HERO ----------------
html("".join([
    '<div class="hero">',
    '<div class="hero-kicker">STEPUP FOOTWEAR · FICTIONAL BRAND · PAKISTAN</div>',
    f'<h1>Where should the next {rs(budget)} go?</h1>',
    '<p>An optimizer that learns each platform\'s diminishing returns and splits the ad '
    'budget across Facebook, Instagram, Google, TikTok and YouTube for maximum revenue.</p>',
    '<span class="badge">📊 Simulated data</span>',
    '<span class="badge">🧮 SciPy optimizer</span>',
    '<span class="badge">✅ Validated vs true optimum</span>',
    '<span class="badge">⚡ Pandas · Hadoop · Spark</span>',
    '</div>']))

tabs = st.tabs(["🎯 Recommendation", "📈 Response curves", "🔍 KPI explorer",
                "✅ Validation", "⚡ Big Data benchmark", "ℹ️ About & limitations"])

# ---------------- TAB 1: RECOMMENDATION ----------------
with tabs[0]:
    c = st.columns(4)
    c[0].markdown(card("Expected revenue", rs(tot_rev), f"ROAS {tot_rev / budget:.2f}"),
                  unsafe_allow_html=True)
    c[1].markdown(card("Expected profit", rs(tot_profit),
                       f"after {margin:.0%} margin & ad spend", MUTED), unsafe_allow_html=True)
    c[2].markdown(card("Gain vs equal split", f"{opt_gain:+.1f}%",
                       f"{rs(tot_rev - eq_rev)} more revenue"), unsafe_allow_html=True)
    c[3].markdown(card(f"vs all on {best}", f"{(tot_rev / allbest_rev - 1) * 100:+.0f}%",
                       "why 'just pick the best ROAS' fails", "#F87171"), unsafe_allow_html=True)

    section("The plan", "Recommended monthly spend per platform")
    order = rec.sort_values("spend", ascending=False)
    pc = st.columns(len(order))
    for col, (_, r) in zip(pc, order.iterrows()):
        color = COLORS[r["platform"]]
        status = f"ROAS {r['ROAS']:.2f}" if r["spend"] > 1 else "not funded"
        col.markdown(
            f'<div class="plat" style="border-top-color:{color}">'
            f'<div class="plat-name">{r["platform"]}</div>'
            f'<div class="plat-share" style="color:{color}">{r["share_%"]:.1f}%</div>'
            f'<div class="plat-amt">{rs(r["spend"])}</div>'
            f'<div class="plat-amt">{status}</div></div>', unsafe_allow_html=True)

    funded = rec[rec.spend > 1].sort_values("spend", ascending=False)
    names = funded.platform.tolist()
    zero = [p for p in platforms if alloc[p] <= 1]
    lo, hi = funded.marginal_ROAS.min(), funded.marginal_ROAS.max()
    why = f"<b>💡 Why this split?</b><br>Lead with <b>{names[0]}</b>"
    if len(names) > 1:
        why += f" and <b>{names[1]}</b>"
    why += (". Each platform gets money until its <i>next</i> rupee earns about the same as "
            f"everywhere else: <b>Rs. {lo:.2f}–{hi:.2f}</b> back per rupee. ")
    if zero:
        verb = "gets" if len(zero) == 1 else "get"
        why += f"<b>{', '.join(zero)}</b> {verb} nothing: the first rupee there earns less than that. "
    why += f"Break-even at a {margin:.0%} margin is ROAS <b>{breakeven:.2f}</b>."
    html(f'<div class="why">{why}</div>')
    if lo < breakeven:
        st.warning("Some of the last rupees **lose money** after product costs: this budget is "
                   "bigger than the profit-maximising level. See 📈 Response curves.")

    left, right = st.columns(2)
    with left:
        fig = px.pie(rec[rec.spend > 1], names="platform", values="spend", hole=0.62,
                     color="platform", color_discrete_map=COLORS)
        fig.update_traces(textinfo="percent", marker=dict(line=dict(color="#0B0F19", width=3)))
        fig.add_annotation(text=f"<b>{rs(budget)}</b><br>per month", showarrow=False,
                           font=dict(size=15, color="#F5F7FB"))
        fig.update_layout(title="Budget split", legend=dict(orientation="h", y=-0.1))
        show(fig, 420)
    with right:
        bar_colors = [ACCENT if s == "Optimizer" else "#3A4560" for s in comp.strategy]
        fig = go.Figure(go.Bar(x=comp.strategy, y=comp.revenue, marker_color=bar_colors,
                               text=comp["vs_equal_%"].map(lambda v: f"{v:+.1f}% vs equal"),
                               textposition="outside"))
        fig.update_layout(title="Optimizer vs simple strategies",
                          yaxis_title="Expected revenue (Rs.)",
                          yaxis_range=[0, comp.revenue.max() * 1.18])
        show(fig, 420)

    with st.expander("📋 Detailed table + download"):
        show_t = rec[["platform", "share_%", "spend", "revenue", "ROAS",
                      "marginal_ROAS", "profit"]]
        st.dataframe(show_t.style.format({
            "share_%": "{:.1f}%", "spend": "Rs. {:,.0f}", "revenue": "Rs. {:,.0f}",
            "ROAS": "{:.2f}", "marginal_ROAS": "{:.2f}", "profit": "Rs. {:,.0f}"},
            na_rep="–"), hide_index=True)
        st.download_button("⬇️ Download plan (CSV)", show_t.to_csv(index=False),
                           "stepup_budget_plan.csv", "text/csv")

    section("How sure are we?",
            "The whole fit + optimisation rerun on 50 bootstrap resamples of the data")
    boots = bootstrap_curves()
    shares = []
    for bc in boots:
        al = optimize({p: bc[p] for p in platforms}, budget, slices, min_share, max_share)
        shares.append({p: al.get(p, 0.0) / budget * 100 for p in all_plats})
    sh = pd.DataFrame(shares)
    ci = pd.DataFrame({"platform": all_plats,
                       "recommended_%": [alloc[p] / budget * 100 for p in all_plats],
                       "low_%": sh.quantile(0.05).to_numpy(),
                       "high_%": sh.quantile(0.95).to_numpy()})
    ci["plus"] = (ci["high_%"] - ci["recommended_%"]).clip(lower=0)
    ci["minus"] = (ci["recommended_%"] - ci["low_%"]).clip(lower=0)
    fig = px.bar(ci, x="platform", y="recommended_%", error_y="plus", error_y_minus="minus",
                 color="platform", color_discrete_map=COLORS)
    fig.update_layout(showlegend=False, yaxis_title="Share of budget (%)", xaxis_title="",
                      title=f"Recommended share with 90% range ({len(boots)} resamples)")
    show(fig, 380)
    st.dataframe(ci[["platform", "recommended_%", "low_%", "high_%"]].style.format(
        {"recommended_%": "{:.1f}%", "low_%": "{:.1f}%", "high_%": "{:.1f}%"}), hide_index=True)
    st.caption("Ranges show uncertainty from the limited sample (10k rows) only. They do NOT "
               "cover wrong assumptions or a wrong curve shape. In the self-check, 2 of 5 true "
               "shares fell just outside these ranges, so treat them as a guide.")

# ---------------- TAB 2: RESPONSE CURVES ----------------
with tabs[1]:
    section("Diminishing returns per platform",
            "Expected monthly revenue for a given monthly spend. Lines flatten as spend grows. "
            "⭐ = recommended spend.")
    xs = np.linspace(0, budget, 200)
    fig = go.Figure()
    for p in all_plats:
        cv = curves[p]
        fig.add_trace(go.Scatter(x=xs, y=slices * response(xs / slices, cv["a"], cv["h"]),
                                 name=p, line=dict(color=COLORS[p], width=3)))
        if alloc[p] > 1:
            fig.add_trace(go.Scatter(
                x=[alloc[p]], y=[slices * response(alloc[p] / slices, cv["a"], cv["h"])],
                mode="markers", showlegend=False, name=f"{p} pick",
                marker=dict(size=16, color=COLORS[p], symbol="star",
                            line=dict(color="#fff", width=1))))
    fig.update_layout(xaxis_title="Monthly spend on platform (Rs.)",
                      yaxis_title="Expected revenue (Rs.)")
    show(fig, 460)

    fit = pd.DataFrame(curves).T.reset_index().rename(columns={"index": "platform"})
    fit = fit[["platform", "a", "a_se", "h", "h_se", "rows"]]
    st.dataframe(fit.style.format({"a": "{:.2f}", "a_se": "±{:.2f}", "h": "{:,.0f}",
                                   "h_se": "±{:,.0f}"}), hide_index=True)
    st.caption("a = ROAS at very small spend · h = spend per slice where efficiency halves · "
               "± = standard error of the fit.")

    section("Is this even the right total budget?",
            "Expected profit if the whole budget is split optimally")
    pcurve = profit_curve(tuple(platforms), slices, margin, min_share, max_share,
                          float(max(5_000_000, 2 * budget)))
    top = pcurve.loc[pcurve.profit.idxmax()]
    fig = go.Figure(go.Scatter(x=pcurve.budget, y=pcurve.profit, mode="lines",
                               line=dict(color=ACCENT, width=3), fill="tozeroy",
                               fillcolor="rgba(255,107,53,0.15)"))
    fig.add_vline(x=budget, line_dash="dash", line_color="#C9D1E0",
                  annotation_text="your budget")
    fig.add_vline(x=top.budget, line_dash="dot", line_color="#4ADE80",
                  annotation_text="profit peak")
    fig.update_layout(xaxis_title="Total monthly budget (Rs.)",
                      yaxis_title="Expected profit (Rs.)")
    show(fig, 420)
    st.write(f"Under these assumptions, profit peaks near **{rs(top.budget)}** "
             f"(about {rs(top.profit)} profit). Beyond that, extra ad spend earns back "
             f"less than it costs.")

# ---------------- TAB 3: KPI EXPLORER ----------------
with tabs[2]:
    section("KPIs by platform", "Historical (simulated) performance, computed from totals")
    k = kpi_table(df, ["platform"])
    st.dataframe(k.style.format({
        "impressions": "{:,.0f}", "clicks": "{:,.0f}", "spend": "Rs. {:,.0f}",
        "conversions": "{:,.0f}", "revenue": "Rs. {:,.0f}", "CPC": "Rs. {:.1f}",
        "CPA": "Rs. {:,.0f}", "profit_proxy": "Rs. {:,.0f}"}), hide_index=True)
    st.caption("profit_proxy = revenue − ad spend (ignores product cost).")

    dims = {"Campaign": "campaign", "Age": "age", "Gender": "gender",
            "City": "city", "Device": "device"}
    c1, c2 = st.columns(2)
    dim = dims[c1.selectbox("Break down by", list(dims))]
    metric = c2.selectbox("Metric", ["ROAS", "CTR_%", "CVR_%", "CPC", "CPA"])
    t = kpi_table(df, ["platform", dim])
    pivot = t.pivot(index="platform", columns=dim, values=metric)
    scale = "RdYlGn_r" if metric in ["CPC", "CPA"] else "RdYlGn"
    fig = px.imshow(pivot, text_auto=".2f", aspect="auto", color_continuous_scale=scale)
    fig.update_layout(title=f"{metric} by platform × {dim}")
    show(fig, 420)
    st.caption("Green = better. For CPC and CPA lower is better, so the colours are reversed.")

    m = kpi_table(df, ["month", "platform"])
    fig = px.line(m, x="month", y=metric, color="platform", markers=True,
                  color_discrete_map=COLORS)
    fig.update_traces(line=dict(width=3))
    fig.update_layout(title=f"Monthly {metric}")
    show(fig, 420)
    st.caption("Peaks match the simulated Eid ul Fitr (Mar), Eid ul Adha (late May–Jun) "
               "and 11.11 (Nov) campaigns.")

# ---------------- TAB 4: VALIDATION ----------------
with tabs[3]:
    section("Self-check: does the optimizer find the TRUE best split?",
            "The data is simulated, so the true best split is known. Data was regenerated 5 "
            "times at 10k, 100k and 1M rows, and each result was scored against the truth.")
    vs_file, tr_file = PROC / "validation_summary.csv", PROC / "true_optimum.csv"
    if vs_file.exists():
        vs = pd.read_csv(vs_file)
        c = st.columns(3)
        c[0].markdown(card("Optimizer at 10k rows", f"{vs.optimizer_pct_mean.iloc[0]:.2f}%",
                           "of the true best revenue"), unsafe_allow_html=True)
        c[1].markdown(card("Equal split", f"{vs.equal_pct.iloc[0]:.1f}%",
                           "of the true best revenue", MUTED), unsafe_allow_html=True)
        c[2].markdown(card("Share error, 10k → 1M rows",
                           f"{vs.share_error_pp_mean.iloc[0]:.2f} → "
                           f"{vs.share_error_pp_mean.iloc[-1]:.2f} pp",
                           "more data = more precise split"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            fig = px.line(vs, x="rows", y="share_error_pp_mean", log_x=True, markers=True,
                          error_y="share_error_pp_std")
            fig.update_traces(line=dict(color=ACCENT, width=3), marker=dict(size=10))
            fig.update_layout(xaxis_title="Rows of data (log scale)",
                              yaxis_title="Avg share error (pp)",
                              title="More data → more precise split")
            show(fig, 400)
        with c2:
            long = vs.melt(id_vars="rows",
                           value_vars=["optimizer_pct_mean", "lastyear_pct", "equal_pct"],
                           var_name="strategy", value_name="pct_of_best")
            long["strategy"] = long.strategy.map({"optimizer_pct_mean": "Optimizer",
                                                  "lastyear_pct": "Last year's split",
                                                  "equal_pct": "Equal split"})
            long["rows"] = long.rows.map(lambda r: f"{r:,}")
            fig = px.bar(long, x="rows", y="pct_of_best", color="strategy", barmode="group",
                         color_discrete_map={"Optimizer": ACCENT,
                                             "Last year's split": "#7B2FF7",
                                             "Equal split": "#3A4560"})
            fig.update_layout(yaxis_range=[90, 100.5], xaxis_title="Rows of data",
                              yaxis_title="% of true best revenue",
                              title="Revenue captured vs the true best")
            show(fig, 400)
        st.dataframe(vs, hide_index=True)
    else:
        st.info("Run src/optimizer/validate.py to create the validation results.")
    if tr_file.exists():
        tr = pd.read_csv(tr_file)
        tr["fitted_a (10k)"] = tr.platform.map(lambda p: curves[p]["a"])
        tr["fitted_h (10k)"] = tr.platform.map(lambda p: curves[p]["h"])
        st.write("**True vs fitted curve parameters**")
        st.dataframe(tr.round(2), hide_index=True)
    st.warning("**Honest caveat:** this is a best-case test. The optimizer assumes the same "
               "curve shape the generator used, and simulated spend is random. Real data has "
               "wrong-shaped curves, seasonality and spend that follows demand, so real "
               "accuracy would be lower.")

# ---------------- TAB 5: BIG DATA BENCHMARK ----------------
with tabs[4]:
    section("Pandas vs Hadoop MapReduce vs Spark",
            "Same job on every engine: read the CSV, group by platform + campaign, sum 5 "
            "metrics. Google Colab free tier (1 machine, 2 cores, 12 GB RAM), median of 3 runs, "
            "Hadoop 3.5.0 Streaming (local mode), PySpark 4.0.5 local[*]. All engines produced "
            "identical totals at every size.")
    b_file, big_file = PROC / "benchmark_results.csv", PROC / "benchmark_100M.csv"
    eng_colors = {"Pandas": "#4ADE80", "Hadoop MapReduce": "#FBBF24", "Spark": ACCENT}

    if big_file.exists():
        big = pd.read_csv(big_file)
        st.markdown("**🔥 Stress test: 100M rows (8 GB file)**")
        cols = st.columns(len(big))
        for col, (_, r) in zip(cols, big.iterrows()):
            if r["status"] == "OK":
                col.markdown(card(r["engine"], f"{r['seconds']:.0f} s",
                                  "✓ correct totals" if r["correct"] else "✗ wrong totals"),
                             unsafe_allow_html=True)
            else:
                col.markdown(card(r["engine"], "Crashed", "out of memory", "#F87171"),
                             unsafe_allow_html=True)
        st.caption(f"The 100M file is the 10M file **replicated 10×** (tests scale, not new "
                   f"information). Plain Pandas ran in a separate process with a "
                   f"{big.memory_cap_gb.iloc[0]} GB memory cap (free RAM at the time). Chunked "
                   f"Pandas reads 2M rows at a time. 1 run each.")

    if b_file.exists():
        b = pd.read_csv(b_file)
        c1, c2 = st.columns(2)
        with c1:
            fig = px.line(b, x="rows", y="median_s", color="engine", markers=True,
                          log_x=True, log_y=True, color_discrete_map=eng_colors)
            fig.update_traces(line=dict(width=3), marker=dict(size=10))
            fig.update_layout(xaxis_title="Rows (log scale)", yaxis_title="Seconds (log scale)",
                              title="Read + aggregate time, 10k → 10M rows")
            show(fig, 420)
        with c2:
            b["rows_lbl"] = b.rows.map(lambda r: f"{r:,}")
            fig = px.bar(b, x="rows_lbl", y="rows_per_s", color="engine", barmode="group",
                         color_discrete_map=eng_colors)
            fig.update_layout(xaxis_title="Rows", yaxis_title="Rows processed per second",
                              title="Throughput")
            show(fig, 420)
        piv = b.pivot(index="rows", columns="engine", values="median_s")
        piv.index = piv.index.map(lambda r: f"{r:,} rows")
        st.dataframe(piv.style.format("{:.2f} s"))
    else:
        st.info("benchmark_results.csv not found.")

    st.success(
        "**Key takeaways**\n"
        "- **On one machine, Pandas is fastest up to 10M rows.** Hadoop pays about 4.5 s and "
        "Spark about 1 s of start-up per job, and on 2 cores neither catches up per row.\n"
        "- **At 100M rows (8 GB), plain Pandas ran out of memory**; Spark and Hadoop finished "
        "with correct results.\n"
        "- **Chunked Pandas was still fastest (83 s vs Spark 137 s vs Hadoop 213 s).** The real "
        "value of Spark and Hadoop is spreading work over **many machines** and surviving "
        "failures, which a single free Colab machine can't show.\n"
        "- **Decision rule:** use Pandas while data fits in memory, chunk it when it doesn't, "
        "and move to Spark when you need a cluster. Hadoop MapReduce is the slowest and mostly "
        "legacy; Spark replaced it for this kind of job.")
    st.warning("**Limitations:** one 2-core machine only (no real cluster); 100M rows are "
               "replicated; a simple group-by job (joins or ML would behave differently); "
               "the Spark JVM start-up was excluded from timings; Colab's speed varies run to run.")

# ---------------- TAB 6: ABOUT ----------------
with tabs[5]:
    section("Method")
    st.markdown(
        "1. **Simulate** campaign data with the brief's schema (date, campaign, platform, "
        "impressions, clicks, spend, conversions, revenue, age, gender, city, device).\n"
        "2. **KPIs** from sums: CTR, CPC, CVR, CPA, ROAS.\n"
        "3. **Fit** a diminishing-returns curve per platform: "
        "revenue(s) = a·s / (1 + s/h), using non-linear least squares (scipy).\n"
        "4. **Optimise** the split with SLSQP: maximise total expected revenue subject to "
        "the budget and min/max share limits. With a fixed budget, max revenue = max profit.\n"
        "5. **Validate** against the known true optimum at 10k / 100k / 1M rows, and "
        "**bootstrap** for uncertainty.\n"
        "6. **Benchmark** Pandas vs Hadoop MapReduce vs Spark from 10k to 100M rows.")
    section("Simulation assumptions (PKR)")
    a = pd.DataFrame(G.PLATFORMS).T.reset_index().rename(columns={"index": "platform"})
    a["row_share"] = G.PLATFORM_SHARE
    st.dataframe(a, hide_index=True)
    st.caption("cpm = cost per 1,000 impressions · ctr/cvr = base click & conversion rates · "
               "aov = average order value · half_sat = spend per slice where efficiency halves.")
    section("Limitations")
    st.markdown(
        "- **Simulated data:** results reflect the assumptions, not real Pakistani ad prices.\n"
        "- **Best-case validation:** the fitted curve shape matches the generator's.\n"
        "- **No confounding:** simulated spend is random; real brands spend more when demand "
        "is already high, which makes ads look more effective.\n"
        "- **Revenue only:** brand awareness (YouTube's main job) isn't measured, so YouTube "
        "can look worse than it is. Use the minimum-share slider or the preset to keep a presence.\n"
        "- **No time dynamics:** no ad fatigue, carry-over effects, or seasonality in the optimizer.\n"
        "- **Pooled curves:** one curve per platform; segments (age, city…) aren't optimised separately.\n"
        "- **Scale assumption:** absolute revenue depends on the slices setting; comparisons "
        "between strategies are more reliable than the absolute numbers.")
    st.markdown("**Links:** [GitHub repo](https://github.com/usamahanif349/pk-footwear-budget-optimizer) · "
                "[Project 1: sentiment analysis](https://github.com/usamahanif349/pk-footwear-sentiment-analysis)")