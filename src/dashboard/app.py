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

DATA_FILE = ROOT / "data" / "raw" / "ads_10000.csv"
PROC = ROOT / "data" / "processed"
N_BOOT = 200

# ---------------- COLOURS ----------------
INK = "#15181D"          # main text
INK_2 = "#5B6270"        # secondary text
LINE = "#E3E6EB"         # hairlines / grid
NAVY = "#1E3A5F"         # the optimizer / highlight
GREY = "#9AA1AD"         # comparison strategies
GREY_LIGHT = "#C9CED6"
GOOD, BAD = "#0B7A3E", "#B42318"
# Platform colours: one fixed, colour-blind-checked palette, in order of the
# usual spend ranking so neighbours in the budget bar stay easy to tell apart.
COLORS = {"Facebook": "#2A78D6", "TikTok": "#EB6834", "Instagram": "#1BAF7A",
          "Google": "#EDA100", "YouTube": "#E87BA4"}
DARK_TEXT_ON = {"Google"}  # yellow fill needs dark text
SHAPE_COLORS = {"Same as assumed": NAVY, "Exponential": "#EB6834", "S-curve": "#1BAF7A"}
ENGINE_COLORS = {"Pandas": "#2A78D6", "Spark": "#EB6834", "Hadoop MapReduce": "#1BAF7A"}

st.set_page_config(page_title="StepUp ad budget optimizer", page_icon="📊", layout="wide")

# ---------------- STYLE ----------------
CSS = """
<style>
.block-container {padding-top: 4.5rem; max-width: 1240px;}
h1, h2, h3 {letter-spacing: -0.01em;}

/* page head */
.head-brand {color: #5B6270; font-size: .95rem; margin: 0 0 .35rem;}
.head-brand b {color: #15181D; font-weight: 600;}
.head h1 {font-size: 2.35rem; line-height: 1.15; font-weight: 700; color: #15181D;
  margin: 0 0 .5rem; padding: 0;}
.head p.lede {color: #5B6270; font-size: 1.05rem; max-width: 62ch; margin: 0 0 1.4rem;}

/* allocation: the signature element */
.alloc-bar {display: flex; gap: 2px; height: 58px; border-radius: 6px; overflow: hidden;
  margin-bottom: .9rem;}
.seg {display: flex; align-items: center; padding: 0 12px; min-width: 0; color: #fff;
  font-weight: 600; font-size: .92rem; white-space: nowrap; overflow: hidden;}
.seg span.pct {font-weight: 500; opacity: .9; margin-left: 6px;}
.alloc-wrap {overflow-x: auto;}
table.alloc {width: 100%; border-collapse: collapse; font-size: .93rem; border: 0;
  font-variant-numeric: tabular-nums; margin: 0;}
table.alloc tr, table.alloc th, table.alloc td {border: 0; background: transparent;}
table.alloc th {text-align: right; color: #5B6270; font-weight: 500; padding: 6px 10px;
  border-bottom: 1px solid #E3E6EB !important; white-space: nowrap;}
table.alloc th:first-child, table.alloc td:first-child {text-align: left;}
table.alloc td {text-align: right; padding: 9px 10px; border-bottom: 1px solid #F0F2F5 !important;
  color: #15181D; white-space: nowrap;}
table.alloc tr.off td {color: #8A909B;}
.sw {display: inline-block; width: 10px; height: 10px; border-radius: 2px;
  margin-right: 10px; vertical-align: 0;}

/* key numbers */
.stats {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid #E3E6EB; border-bottom: 1px solid #E3E6EB; margin: 1.6rem 0 .4rem;}
.stat {padding: 16px 18px 15px; border-left: 1px solid #E3E6EB;}
.stat:first-child {border-left: 0; padding-left: 0;}
.stat .lbl {color: #5B6270; font-size: .88rem;}
.stat .val {color: #15181D; font-size: 1.6rem; font-weight: 600; margin-top: 2px;
  line-height: 1.2; white-space: nowrap;}
.stat .sub {color: #5B6270; font-size: .84rem; margin-top: 3px;}
.stat .sub.good {color: #0B7A3E;}
.stat .sub.bad {color: #B42318;}
@media (max-width: 800px) {
  .stats {grid-template-columns: repeat(2, minmax(0, 1fr));}
  .stat:nth-child(3) {border-left: 0; padding-left: 0;}
  .stat:nth-child(n+3) {border-top: 1px solid #E3E6EB;}
  .stat, .stat:first-child {padding: 12px 10px 11px 12px;}
  .stat:nth-child(odd) {padding-left: 0;}
  .stat .val {font-size: 1.2rem; white-space: normal;}
  .head h1 {font-size: 1.8rem;}
  .alloc-bar {height: 44px;}
  .seg {padding: 0 8px; font-size: .82rem;}
  .seg span.pct {display: none;}
}

/* explanation note */
.note {border-left: 3px solid #1E3A5F; background: #F5F7FA; padding: 14px 18px;
  margin: 1.2rem 0 .4rem; line-height: 1.6; color: #2B3038; max-width: 90ch;}

/* section heads */
.section h3 {margin: 1.9rem 0 0; font-weight: 600; font-size: 1.3rem; color: #15181D;}
.section p {color: #5B6270; margin: 4px 0 10px; max-width: 80ch;}

/* sidebar */
.side-brand {font-size: 1.25rem; font-weight: 700; color: #15181D; line-height: 1.2;}
.side-brand span {display: block; font-size: .9rem; font-weight: 400; color: #5B6270;}

/* tabs: a segmented control so the sections stand out */
.stTabs {margin-top: 1.6rem;}
.stTabs [data-baseweb="tab-list"] {gap: 4px; background: #EEF1F5; padding: 5px;
  border-radius: 10px; border: 1px solid #E3E6EB; width: fit-content; max-width: 100%;
  flex-wrap: wrap;}
.stTabs [data-baseweb="tab"] {padding: 9px 18px; height: auto; border-radius: 7px;
  background: transparent;}
.stTabs [data-baseweb="tab"] p {font-size: .98rem; color: #3B414B; font-weight: 500;}
.stTabs [data-baseweb="tab"]:hover {background: #E3E7ED;}
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"]:hover {background: #1E3A5F !important;
  box-shadow: 0 1px 2px rgba(21, 24, 29, .18);}
.stTabs [aria-selected="true"] p {color: #FFFFFF !important; font-weight: 600;}
.stTabs [data-baseweb="tab"]:focus-visible {outline: 2px solid #1E3A5F; outline-offset: 2px;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

pio.templates["stepup"] = go.layout.Template(layout=go.Layout(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    font=dict(color="#3B414B", family="Source Sans 3, Source Sans Pro, Segoe UI, sans-serif", size=13),
    colorway=list(COLORS.values()),
    xaxis=dict(gridcolor="#EEF0F3", zerolinecolor="#C9CED6", linecolor="#C9CED6",
               ticks="", showline=True),
    yaxis=dict(gridcolor="#EEF0F3", zerolinecolor="#C9CED6", linecolor="#C9CED6",
               ticks=""),
    margin=dict(t=56, l=10, r=16, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.0,
                xanchor="left", x=0, title_text=""),
    title=dict(font=dict(size=15, color=INK), x=0, xanchor="left", y=0.98),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#D5D9E0",
                    font=dict(color=INK, family="Source Sans 3, Source Sans Pro, sans-serif"))))
pio.templates.default = "plotly_white+stepup"


def show(fig, height=None):
    if height:
        fig.update_layout(height=height)
    if fig.layout.title.text and fig.layout.showlegend is not False:
        fig.update_layout(margin=dict(t=80), legend=dict(y=1.02))
    st.plotly_chart(fig, theme=None, config={"displaylogo": False})


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def rs(x):
    return f"Rs. {x:,.0f}"


def stats(items):
    """items: list of (label, value, sub, tone) with tone in '', 'good', 'bad'."""
    cells = "".join(f'<div class="stat"><div class="lbl">{lbl}</div><div class="val">{val}</div>'
                    f'<div class="sub {tone}">{sub}</div></div>'
                    for lbl, val, sub, tone in items)
    return f'<div class="stats">{cells}</div>'


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
def bootstrap_curves(n_boot=N_BOOT, seed=0):
    """Refit the curves on random resamples of the data (with replacement)."""
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
    "Balanced (default)": {},
    "Keep YouTube alive (min 5% each)": dict(min_share=5),
    "Eid push (Rs. 2M budget)": dict(budget=2_000_000),
    "Google paused": dict(platforms=[p for p in all_plats if p != "Google"]),
    "Spread risk (max 30% each)": dict(max_share=30),
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def apply_preset():
    chosen = PRESETS[st.session_state["preset"]]
    for k, v in DEFAULTS.items():
        st.session_state[k] = chosen.get(k, v)


with st.sidebar:
    html('<div class="side-brand">StepUp Footwear<span>Ad budget optimizer</span></div>')
    st.selectbox("Scenario", list(PRESETS), key="preset", on_change=apply_preset)
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
    st.caption("All data is simulated for a fictional brand. The assumptions are listed in "
               "the About tab.")

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
    "Last year's split": {p: budget * hist[p] for p in all_plats},
    "Equal split": {p: budget / len(all_plats) for p in all_plats},
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

# ---------------- PAGE HEAD: the answer first ----------------
order = rec.sort_values("spend", ascending=False)
funded = order[order.spend > 1]
segs = []
for _, r in funded.iterrows():
    p = r["platform"]
    fg = INK if p in DARK_TEXT_ON else "#FFFFFF"
    label = (f'{p}<span class="pct">{r["share_%"]:.1f}%</span>' if r["share_%"] >= 9
             else (f'{r["share_%"]:.0f}%' if r["share_%"] >= 4 else ""))
    segs.append(f'<div class="seg" style="flex:{r["share_%"]:.4f} 0 0;background:{COLORS[p]};'
                f'color:{fg}" title="{p}: {r["share_%"]:.1f}%">{label}</div>')
rows_html = []
for _, r in order.iterrows():
    p = r["platform"]
    on = r["spend"] > 1
    roas_txt = f"{r['ROAS']:.2f}" if on else "Not funded"
    rev_txt = rs(r["revenue"]) if on else "–"
    rows_html.append(
        f'<tr class="{"" if on else "off"}"><td><span class="sw" style="background:{COLORS[p]}">'
        f'</span>{p}</td><td>{r["share_%"]:.1f}%</td><td>{rs(r["spend"])}</td>'
        f'<td>{rev_txt}</td><td>{roas_txt}</td>'
        f'<td>{r["marginal_ROAS"]:.2f}</td></tr>')

html("".join([
    '<div class="head">',
    '<p class="head-brand"><b>StepUp Footwear</b>, a fictional Pakistani shoe brand. '
    'All data is simulated.</p>',
    f'<h1>Where should the next {rs(budget)} go?</h1>',
    '<p class="lede">The optimizer learns how fast each platform runs out of steam, then splits '
    'the monthly budget so every rupee goes where it earns the most.</p>',
    f'<div class="alloc-bar">{"".join(segs)}</div>',
    '<div class="alloc-wrap"><table class="alloc"><thead><tr><th>Platform</th><th>Share</th>'
    '<th>Monthly spend</th><th>Expected revenue</th><th>ROAS</th>'
    '<th>Return on the next rupee</th></tr></thead>',
    f'<tbody>{"".join(rows_html)}</tbody></table></div>',
    stats([
        ("Expected revenue", rs(tot_rev), f"ROAS {tot_rev / budget:.2f}", ""),
        ("Expected profit", rs(tot_profit), f"after {margin:.0%} margin and ad spend", ""),
        ("Gain vs equal split", f"{opt_gain:+.1f}%", f"{rs(tot_rev - eq_rev)} more revenue",
         "good" if opt_gain >= 0 else "bad"),
        (f"Gain vs all on {best}", f"{(tot_rev / allbest_rev - 1) * 100:+.0f}%",
         "why picking the best ROAS fails", ""),
    ]),
    '</div>']))

tabs = st.tabs(["Recommendation", "Response curves", "KPI explorer",
                "Validation", "Big Data benchmark", "About & limitations"])

# ---------------- TAB 1: RECOMMENDATION ----------------
with tabs[0]:
    names = funded.platform.tolist()
    zero = [p for p in platforms if alloc[p] <= 1]
    lo, hi = funded.marginal_ROAS.min(), funded.marginal_ROAS.max()
    back = f"Rs. {lo:.2f}" if f"{lo:.2f}" == f"{hi:.2f}" else f"Rs. {lo:.2f} to {hi:.2f}"
    why = f"<b>Why this split?</b> Lead with {names[0]}"
    if len(names) > 1:
        why += f" and {names[1]}"
    why += (". Each platform gets money until its <i>next</i> rupee earns about the same as "
            f"everywhere else: about <b>{back}</b> back per rupee. ")
    if zero:
        verb = "gets" if len(zero) == 1 else "get"
        why += f"{', '.join(zero)} {verb} nothing, because its first rupee earns less than that. "
    why += f"At a {margin:.0%} margin, break-even is a ROAS of <b>{breakeven:.2f}</b>."
    html(f'<div class="note">{why}</div>')
    if lo < breakeven:
        st.warning("Some of the last rupees **lose money** after product costs, so this budget is "
                   "bigger than the profit-maximising level. See the Response curves tab.")

    section("Optimizer vs simple strategies",
            "Expected monthly revenue for the same budget, split four different ways")
    cmp = comp.iloc[::-1]
    fig = go.Figure(go.Bar(
        y=cmp.strategy, x=cmp.revenue, orientation="h",
        marker_color=[NAVY if s == "Optimizer" else GREY_LIGHT for s in cmp.strategy],
        text=[f"{rs(v)}   {g:+.1f}% vs equal" for v, g in zip(cmp.revenue, cmp["vs_equal_%"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: Rs. %{x:,.0f}<extra></extra>"))
    fig.update_layout(xaxis_title="Expected revenue (Rs.)", showlegend=False,
                      xaxis_range=[0, comp.revenue.max() * 1.38], margin=dict(t=10),
                      yaxis=dict(showline=False), xaxis=dict(showgrid=True))
    show(fig, 260)
    st.caption(f"Putting everything on {best}, the platform with the best average ROAS, "
               "earns the least: diminishing returns punish putting all eggs in one basket.")

    with st.expander("Detailed table and download"):
        show_t = rec[["platform", "share_%", "spend", "revenue", "ROAS",
                      "marginal_ROAS", "profit"]]
        st.dataframe(show_t.style.format({
            "share_%": "{:.1f}%", "spend": "Rs. {:,.0f}", "revenue": "Rs. {:,.0f}",
            "ROAS": "{:.2f}", "marginal_ROAS": "{:.2f}", "profit": "Rs. {:,.0f}"},
            na_rep="–"), hide_index=True)
        st.download_button("Download plan (CSV)", show_t.to_csv(index=False),
                           "stepup_budget_plan.csv", "text/csv")

    section("How sure are we?",
            f"The whole fit and optimisation rerun on {N_BOOT} bootstrap resamples of the data. "
            "Dots are the recommended shares; lines show the 90% range.")
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
    ci = ci.set_index("platform").loc[order.platform.tolist()[::-1]].reset_index()
    fig = go.Figure()
    for _, r in ci.iterrows():
        p = r["platform"]
        fig.add_trace(go.Scatter(
            x=[r["recommended_%"]], y=[p], mode="markers", name=p, showlegend=False,
            marker=dict(size=12, color=COLORS[p], line=dict(color="#FFFFFF", width=2)),
            error_x=dict(type="data", symmetric=False, thickness=2, width=6, color=COLORS[p],
                         array=[max(r["high_%"] - r["recommended_%"], 0)],
                         arrayminus=[max(r["recommended_%"] - r["low_%"], 0)]),
            hovertemplate=(f"{p}: %{{x:.1f}}% (90% range {r['low_%']:.1f}% to "
                           f"{r['high_%']:.1f}%)<extra></extra>")))
    fig.update_layout(xaxis_title="Share of budget (%)", margin=dict(t=10),
                      xaxis_range=[0, max(ci["high_%"].max() * 1.12, 5)])
    show(fig, 300)
    st.dataframe(ci[["platform", "recommended_%", "low_%", "high_%"]].iloc[::-1].style.format(
        {"recommended_%": "{:.1f}%", "low_%": "{:.1f}%", "high_%": "{:.1f}%"}), hide_index=True)
    cov_file = PROC / "bootstrap_coverage_summary.csv"
    cov_note = ""
    if cov_file.exists():
        cov = pd.read_csv(cov_file)
        c200 = cov[cov.n_boot == cov.n_boot.max()]
        cov_note = (f" Tested on 30 fresh simulated datasets, the true best share fell inside the "
                    f"range {c200.percentile_coverage.mean():.0f}% of the time (target 90%), "
                    f"so the ranges are honest. YouTube, whose true share sits next to zero, "
                    f"was the weakest at {c200.loc[c200.platform == 'YouTube', 'percentile_coverage'].iloc[0]:.0f}%.")
    st.caption("These ranges only show uncertainty from having 10k rows of data. They do NOT "
               "cover a wrong curve shape or wrong assumptions." + cov_note)

# ---------------- TAB 2: RESPONSE CURVES ----------------
with tabs[1]:
    section("Diminishing returns per platform",
            "Expected monthly revenue for a given monthly spend. Each line flattens as spend "
            "grows. Dots mark the recommended spend.")
    xs = np.linspace(0, budget, 200)
    fig = go.Figure()
    for p in order.platform:
        cv = curves[p]
        fig.add_trace(go.Scatter(x=xs, y=slices * response(xs / slices, cv["a"], cv["h"]),
                                 name=p, line=dict(color=COLORS[p], width=2),
                                 hovertemplate=f"{p}: spend Rs. %{{x:,.0f}} → revenue "
                                               f"Rs. %{{y:,.0f}}<extra></extra>"))
        if alloc[p] > 1:
            fig.add_trace(go.Scatter(
                x=[alloc[p]], y=[slices * response(alloc[p] / slices, cv["a"], cv["h"])],
                mode="markers", showlegend=False, name=f"{p} pick",
                marker=dict(size=12, color=COLORS[p], line=dict(color="#FFFFFF", width=2)),
                hovertemplate=f"{p} recommended: Rs. %{{x:,.0f}}<extra></extra>"))
    fig.update_layout(xaxis_title="Monthly spend on platform (Rs.)",
                      yaxis_title="Expected revenue (Rs.)", hovermode="closest")
    show(fig, 460)

    fit = pd.DataFrame(curves).T.reset_index().rename(columns={"index": "platform"})
    fit = fit[["platform", "a", "a_se", "h", "h_se", "rows"]]
    st.dataframe(fit.style.format({"a": "{:.2f}", "a_se": "±{:.2f}", "h": "{:,.0f}",
                                   "h_se": "±{:,.0f}"}), hide_index=True)
    st.caption("a is the ROAS at very small spend, h is the spend per slice where efficiency "
               "halves, and ± is the standard error of the fit.")

    section("Is this even the right total budget?",
            "Expected profit if the whole budget is split optimally")
    pcurve = profit_curve(tuple(platforms), slices, margin, min_share, max_share,
                          float(max(5_000_000, 2 * budget)))
    top = pcurve.loc[pcurve.profit.idxmax()]
    fig = go.Figure(go.Scatter(x=pcurve.budget, y=pcurve.profit, mode="lines",
                               line=dict(color=NAVY, width=2), showlegend=False,
                               hovertemplate="Budget Rs. %{x:,.0f} → profit Rs. %{y:,.0f}"
                                             "<extra></extra>"))
    fig.add_vline(x=budget, line_dash="dash", line_color=GREY, line_width=1,
                  annotation_text="Your budget", annotation_font_color=INK_2)
    fig.add_vline(x=top.budget, line_dash="dot", line_color=GOOD, line_width=1,
                  annotation_text="Profit peak", annotation_font_color=GOOD,
                  annotation_position="top left")
    fig.update_layout(xaxis_title="Total monthly budget (Rs.)",
                      yaxis_title="Expected profit (Rs.)", margin=dict(t=30))
    show(fig, 400)
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
    fig = px.imshow(pivot, text_auto=".2f", aspect="auto", color_continuous_scale="Blues")
    fig.update_traces(xgap=2, ygap=2)
    fig.update_layout(title=f"{metric} by platform and {dim}", xaxis_title="", yaxis_title="",
                      coloraxis_colorbar=dict(title="", thickness=12))
    show(fig, 400)
    st.caption("Darker means a higher value. For CPC and CPA, lower is better.")

    m = kpi_table(df, ["month", "platform"])
    fig = go.Figure()
    for p in order.platform:
        mp = m[m.platform == p]
        fig.add_trace(go.Scatter(x=mp.month, y=mp[metric], name=p, mode="lines+markers",
                                 line=dict(color=COLORS[p], width=2), marker=dict(size=7)))
    fig.update_layout(title=f"Monthly {metric}", hovermode="x unified")
    show(fig, 420)
    st.caption("Peaks match the simulated Eid ul Fitr (Mar), Eid ul Adha (late May to Jun) "
               "and 11.11 (Nov) campaigns.")

# ---------------- TAB 4: VALIDATION ----------------
with tabs[3]:
    section("Does the optimizer find the true best split?",
            "The data is simulated, so the true best split is known. The data was regenerated "
            "5 times at 10k, 100k and 1M rows, and each result was scored against the truth.")
    vs_file, tr_file = PROC / "validation_summary.csv", PROC / "true_optimum.csv"
    if vs_file.exists():
        vs = pd.read_csv(vs_file)
        html(stats([
            ("Optimizer at 10k rows", f"{vs.optimizer_pct_mean.iloc[0]:.2f}%",
             "of the true best revenue", ""),
            ("Last year's split", f"{vs.lastyear_pct.iloc[0]:.1f}%",
             "of the true best revenue", ""),
            ("Equal split", f"{vs.equal_pct.iloc[0]:.1f}%", "of the true best revenue", ""),
            ("Share error, 10k to 1M rows",
             f"{vs.share_error_pp_mean.iloc[0]:.2f} → {vs.share_error_pp_mean.iloc[-1]:.2f} pp",
             "more data gives a more precise split", ""),
        ]))
        fig = go.Figure(go.Scatter(
            x=vs.rows, y=vs.share_error_pp_mean, mode="lines+markers", showlegend=False,
            line=dict(color=NAVY, width=2), marker=dict(size=9),
            error_y=dict(array=vs.share_error_pp_std, thickness=1.5, width=5, color=NAVY),
            hovertemplate="%{x:,} rows: %{y:.2f} pp<extra></extra>"))
        fig.update_layout(xaxis_type="log", xaxis_title="Rows of data (log scale)",
                          yaxis_title="Average share error (pp)", yaxis_rangemode="tozero",
                          title="Each 10× more data cuts the error about 3×")
        show(fig, 360)
        with st.expander("Validation table"):
            st.dataframe(vs, hide_index=True)
    else:
        st.info("Run src/optimizer/validate.py to create the validation results.")
    if tr_file.exists():
        tr = pd.read_csv(tr_file)
        tr["fitted_a (10k)"] = tr.platform.map(lambda p: curves[p]["a"])
        tr["fitted_h (10k)"] = tr.platform.map(lambda p: curves[p]["h"])
        with st.expander("True vs fitted curve parameters"):
            st.dataframe(tr.round(2), hide_index=True)

    section("Hard mode: what if the real curve has a different shape?",
            "The test above is a best case, because the data uses the same curve shape the "
            "optimizer assumes. Here the data comes from two other shapes: an exponential "
            "curve that saturates faster, and an S-curve where small budgets barely work. "
            "The optimizer still fits its usual curve.")
    hm_file = PROC / "hard_mode_summary.csv"
    if hm_file.exists():
        hm = pd.read_csv(hm_file)
        hm["shape_lbl"] = hm["shape"].map({"hyperbolic": "Same as assumed",
                                           "exponential": "Exponential", "s_curve": "S-curve"})
        s10 = hm[hm.rows == hm.rows.min()].set_index("shape_lbl")
        html(stats([
            ("Same shape, 10k rows", f"{s10.loc['Same as assumed', 'optimizer_pct_mean']:.2f}%",
             "of the true best revenue", ""),
            ("Exponential, 10k rows", f"{s10.loc['Exponential', 'optimizer_pct_mean']:.2f}%",
             f"equal split: {s10.loc['Exponential', 'equal_pct']:.1f}%", ""),
            ("S-curve, 10k rows", f"{s10.loc['S-curve', 'optimizer_pct_mean']:.2f}%",
             f"equal split: {s10.loc['S-curve', 'equal_pct']:.1f}%", ""),
            ("Worst single run", f"{hm.optimizer_pct_min.min():.1f}%",
             "S-curve, 10k rows", "bad"),
        ]))
        c1, c2 = st.columns(2)
        with c1:
            long = s10.reset_index().melt(
                id_vars="shape_lbl", value_vars=["optimizer_pct_mean", "lastyear_pct", "equal_pct"],
                var_name="strategy", value_name="pct")
            long["strategy"] = long.strategy.map({"optimizer_pct_mean": "Optimizer",
                                                  "lastyear_pct": "Last year's split",
                                                  "equal_pct": "Equal split"})
            fig = go.Figure()
            for strat, col, size in [("Equal split", GREY_LIGHT, 11),
                                     ("Last year's split", GREY, 11), ("Optimizer", NAVY, 13)]:
                d = long[long.strategy == strat]
                fig.add_trace(go.Scatter(
                    x=d.pct, y=d.shape_lbl, mode="markers", name=strat,
                    marker=dict(size=size, color=col, line=dict(color="#FFFFFF", width=2)),
                    hovertemplate=f"{strat}, %{{y}}: %{{x:.1f}}%<extra></extra>"))
            fig.update_layout(title="Revenue captured at 10k rows (% of true best)",
                              xaxis_title="% of the true best revenue",
                              yaxis=dict(categoryorder="array",
                                         categoryarray=["S-curve", "Exponential",
                                                        "Same as assumed"]))
            show(fig, 340)
        with c2:
            fig = go.Figure()
            for lbl, col in SHAPE_COLORS.items():
                d = hm[hm.shape_lbl == lbl]
                fig.add_trace(go.Scatter(
                    x=d.rows, y=d.share_error_pp_mean, name=lbl, mode="lines+markers",
                    line=dict(color=col, width=2), marker=dict(size=8),
                    hovertemplate=f"{lbl}, %{{x:,}} rows: %{{y:.2f}} pp<extra></extra>"))
            fig.update_layout(title="Share error vs data size",
                              xaxis_type="log", xaxis_title="Rows of data (log scale)",
                              yaxis_title="Average share error (pp)", yaxis_rangemode="tozero")
            show(fig, 340)
        st.markdown(
            "- **Robust where it matters:** even with the wrong curve shape, the optimizer gets "
            "96% or more of the best revenue on average and always beats the equal and "
            "last-year splits. The gap is biggest on the S-curve, where spreading money thin "
            "wastes most of it.\n"
            "- **Weak spot:** with the right shape, more data keeps shrinking the error. With the "
            "wrong shape it gets stuck (about 0.8 pp exponential, 1.6 pp S-curve). More data "
            "cannot fix a wrong model; only a better curve can.")
        with st.expander("Hard mode table"):
            st.dataframe(hm.drop(columns="shape_lbl"), hide_index=True)
    else:
        st.info("Run src/optimizer/hard_mode.py to create the hard mode results.")
    st.warning("**Still a simulation:** spend here is random and there is no seasonality in the "
               "optimizer. Real data has spend that follows demand, so real accuracy would "
               "be lower.")

# ---------------- TAB 5: BIG DATA BENCHMARK ----------------
with tabs[4]:
    section("Pandas vs Hadoop MapReduce vs Spark",
            "Same job on every engine: read the CSV, group by platform and campaign, sum 5 "
            "metrics. Google Colab free tier (1 machine, 2 cores, 12 GB RAM), median of 3 runs, "
            "Hadoop 3.5.0 Streaming (local mode), PySpark 4.0.5 local[*]. All engines produced "
            "identical totals at every size.")
    b_file, big_file = PROC / "benchmark_results.csv", PROC / "benchmark_100M.csv"

    if big_file.exists():
        big = pd.read_csv(big_file)
        items = []
        for _, r in big.iterrows():
            if r["status"] == "OK":
                items.append((r["engine"], f"{r['seconds']:.0f} s",
                              "correct totals" if r["correct"] else "wrong totals", ""))
            else:
                items.append((r["engine"], "Crashed", "out of memory", "bad"))
        st.markdown("**Stress test: 100M rows (8 GB file)**")
        html(stats(items))
        st.caption(f"The 100M file is the 10M file replicated 10× (it tests scale, not new "
                   f"information). Plain Pandas ran in a separate process with a "
                   f"{big.memory_cap_gb.iloc[0]} GB memory cap (free RAM at the time). Chunked "
                   f"Pandas reads 2M rows at a time. 1 run each.")

    if b_file.exists():
        b = pd.read_csv(b_file)
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            for eng, col in ENGINE_COLORS.items():
                d = b[b.engine == eng]
                fig.add_trace(go.Scatter(x=d.rows, y=d.median_s, name=eng, mode="lines+markers",
                                         line=dict(color=col, width=2), marker=dict(size=8),
                                         hovertemplate=f"{eng}, %{{x:,}} rows: %{{y:.2f}} s"
                                                       f"<extra></extra>"))
            fig.update_layout(xaxis_type="log", yaxis_type="log",
                              xaxis_title="Rows (log scale)", yaxis_title="Seconds (log scale)",
                              title="Read and aggregate time, 10k to 10M rows")
            show(fig, 400)
        with c2:
            b["rows_lbl"] = b.rows.map(lambda r: f"{r:,}")
            fig = go.Figure()
            for eng, col in ENGINE_COLORS.items():
                d = b[b.engine == eng]
                fig.add_trace(go.Bar(x=d.rows_lbl, y=d.rows_per_s, name=eng, marker_color=col,
                                     hovertemplate=f"{eng}, %{{x}} rows: %{{y:,.0f}} rows/s"
                                                   f"<extra></extra>"))
            fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08,
                              xaxis_title="Rows", yaxis_title="Rows processed per second",
                              title="Throughput")
            show(fig, 400)
        piv = b.pivot(index="rows", columns="engine", values="median_s")
        piv.index = piv.index.map(lambda r: f"{r:,} rows")
        st.dataframe(piv.style.format("{:.2f} s"))
    else:
        st.info("benchmark_results.csv not found.")

    section("Key takeaways")
    st.markdown(
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
        "5. **Validate** against the known true optimum at 10k, 100k and 1M rows, then repeat "
        "in **hard mode** with data from two other curve shapes.\n"
        f"6. **Bootstrap** ({N_BOOT} resamples) for uncertainty, and check on 30 fresh "
        "datasets that the 90% ranges really contain the truth about 90% of the time.\n"
        "7. **Benchmark** Pandas vs Hadoop MapReduce vs Spark from 10k to 100M rows.")
    section("Simulation assumptions (PKR)")
    a = pd.DataFrame(G.PLATFORMS).T.reset_index().rename(columns={"index": "platform"})
    a["row_share"] = G.PLATFORM_SHARE
    st.dataframe(a, hide_index=True)
    st.caption("cpm is the cost per 1,000 impressions, ctr and cvr are the base click and "
               "conversion rates, aov is the average order value, and half_sat is the spend per "
               "slice where efficiency halves.")
    section("Limitations")
    st.markdown(
        "- **Simulated data:** results reflect the assumptions, not real Pakistani ad prices.\n"
        "- **Curve shape:** the main validation uses the same curve shape as the generator. In "
        "hard mode the optimizer still gets 96%+ of the best revenue, but its error stops "
        "shrinking with more data, so a wrong shape has a cost that more rows can't remove.\n"
        "- **Uncertainty ranges** only cover noise from limited data, not a wrong curve shape "
        "or wrong assumptions.\n"
        "- **No confounding:** simulated spend is random; real brands spend more when demand "
        "is already high, which makes ads look more effective.\n"
        "- **Revenue only:** brand awareness (YouTube's main job) isn't measured, so YouTube "
        "can look worse than it is. Use the minimum-share slider or the preset to keep a presence.\n"
        "- **No time dynamics:** no ad fatigue, carry-over effects, or seasonality in the optimizer.\n"
        "- **Pooled curves:** one curve per platform; segments (age, city…) aren't optimised separately.\n"
        "- **Scale assumption:** absolute revenue depends on the slices setting; comparisons "
        "between strategies are more reliable than the absolute numbers.")
    st.markdown("**Links:** [GitHub repo](https://github.com/usamahanif349/pk-footwear-budget-optimizer), "
                "[Project 1: sentiment analysis](https://github.com/usamahanif349/pk-footwear-sentiment-analysis)")
