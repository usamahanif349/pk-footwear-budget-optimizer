"""
Streamlit dashboard: Digital Ad Budget Optimizer for three Pakistani footwear
brands (Borjan, Servis, Ndure). The AD DATA IS SIMULATED; each brand's customer
sentiment comes from Project 1.

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
for sub in ["optimizer", "analysis", "simulation", "marketing"]:
    sys.path.insert(0, str(ROOT / "src" / sub))
from optimize import fit_curves, optimize, evaluate, response  # noqa: E402
from kpis import kpi_table  # noqa: E402
import generate_data as G  # noqa: E402
import ad_copy as AC  # noqa: E402

DATA_FILE = ROOT / "data" / "raw" / "ads_30000.csv"
PROC = ROOT / "data" / "processed"
N_BOOT = 200
P1_URL = "https://github.com/usamahanif349/pk-footwear-sentiment-analysis"
REPO_URL = "https://github.com/usamahanif349/pk-footwear-budget-optimizer"

# ---------------- COLOURS ----------------
INK, INK_2, MUTED = "#101828", "#475467", "#667085"
LINE = "#E4E7EC"
NAVY = "#1E3A5F"
GREY, GREY_LIGHT = "#98A2B3", "#D0D5DD"
GOOD, BAD = "#067647", "#B42318"
# Platform colours: one colour-blind-checked palette, in the usual spend order
# so neighbours in a stacked view stay easy to tell apart.
COLORS = {"Facebook": "#2A78D6", "TikTok": "#EB6834", "Instagram": "#1BAF7A",
          "Google": "#EDA100", "YouTube": "#E87BA4"}
SHAPE_COLORS = {"Same as assumed": NAVY, "Exponential": "#EB6834", "S-curve": "#1BAF7A"}
SHAPE_LABELS = {"hyperbolic": "Same as assumed", "exponential": "Exponential",
                "s_curve": "S-curve"}
ENGINE_COLORS = {"Pandas": "#2A78D6", "Spark": "#EB6834", "Hadoop MapReduce": "#1BAF7A"}
# System fonts only: a web font that loads late makes Plotly misplace legend labels.
CHART_FONT = "Segoe UI, -apple-system, Helvetica Neue, Arial, sans-serif"

st.set_page_config(page_title="Footwear ad budget optimizer", page_icon="📊", layout="wide")

# ---------------- STYLE ----------------
CSS = """
<style>
.stApp {background: #F6F7F9;}
.block-container {padding-top: 3.2rem; padding-bottom: 3rem; max-width: 1280px;}
[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid #E4E7EC;}
[data-testid="stSidebarNav"] a span {font-size: .97rem;}

/* page header */
.page-h {display: flex; justify-content: space-between; align-items: flex-end;
  gap: 16px; flex-wrap: wrap; margin-bottom: 1.1rem;}
.page-h .crumb {color: #667085; font-size: .86rem; margin: 0 0 4px;}
.page-h h1 {font-size: 1.85rem; font-weight: 700; color: #101828; margin: 0; padding: 0;
  letter-spacing: -0.01em; line-height: 1.2;}
.page-h .sub {color: #475467; margin: 6px 0 0; font-size: 1rem; max-width: 70ch;}
.tag {display: inline-block; font-size: .8rem; font-weight: 600; padding: 4px 10px;
  border-radius: 999px; background: #EEF2F7; color: #1E3A5F; border: 1px solid #D5DEEA;
  white-space: nowrap;}
.tag.sim {background: #FFF7E6; color: #8A5300; border-color: #F5DDB0;}

/* cards: any st.container whose key starts with "card_" */
[class*="st-key-card_"] {background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 14px;
  padding: 18px 20px 14px; box-shadow: 0 1px 2px rgba(16, 24, 40, .05);}
.card-h h4 {font-size: 1.05rem; font-weight: 600; color: #101828; margin: 0; padding: 0;}
.card-h p {color: #667085; font-size: .88rem; margin: 3px 0 10px;}

/* KPI cards */
.kpis {display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px;
  margin-bottom: 14px;}
.kpi {background: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 14px;
  padding: 16px 18px; box-shadow: 0 1px 2px rgba(16, 24, 40, .05);}
.kpi .lbl {color: #475467; font-size: .88rem; font-weight: 500;}
.kpi .row {display: flex; align-items: center; gap: 10px; margin-top: 6px; flex-wrap: wrap;}
.kpi .val {color: #101828; font-size: 1.6rem; font-weight: 700; line-height: 1.15;
  white-space: nowrap;}
.kpi .note {color: #667085; font-size: .82rem; margin-top: 6px;}
.chip {font-size: .78rem; font-weight: 600; padding: 2px 8px; border-radius: 999px;
  white-space: nowrap;}
.chip.good {background: #ECFDF3; color: #067647;}
.chip.bad {background: #FEF3F2; color: #B42318;}
.chip.neutral {background: #F2F4F7; color: #344054;}
@media (max-width: 900px) {
  .kpis {grid-template-columns: repeat(2, minmax(0, 1fr));}
  .kpi .val {font-size: 1.25rem; white-space: normal;}
  .page-h h1 {font-size: 1.5rem;}
}

/* allocation bars */
.alloc-row {padding: 9px 0 10px; border-bottom: 1px solid #F2F4F7;}
.alloc-row:last-child {border-bottom: 0;}
.alloc-top {display: flex; justify-content: space-between; align-items: baseline; gap: 10px;}
.alloc-name {font-weight: 600; color: #101828;}
.alloc-name .sw {display: inline-block; width: 10px; height: 10px; border-radius: 3px;
  margin-right: 8px;}
.alloc-pct {font-weight: 700; color: #101828; font-variant-numeric: tabular-nums;}
.alloc-track {height: 10px; background: #F2F4F7; border-radius: 6px; margin: 7px 0 5px;
  overflow: hidden;}
.alloc-fill {height: 100%; border-radius: 6px;}
.alloc-meta {color: #667085; font-size: .84rem; font-variant-numeric: tabular-nums;}
.alloc-row.off .alloc-name, .alloc-row.off .alloc-pct {color: #98A2B3;}

/* text blocks */
.why {color: #344054; line-height: 1.6; font-size: .97rem;}
.why b {color: #101828;}
.fact {display: flex; justify-content: space-between; padding: 8px 0;
  border-bottom: 1px solid #F2F4F7; font-size: .93rem; color: #344054;}
.fact:last-child {border-bottom: 0;}
.fact b {color: #101828; font-variant-numeric: tabular-nums;}

/* sidebar brand */
.side-brand {font-size: 1.1rem; font-weight: 700; color: #101828; line-height: 1.25;
  margin-bottom: 2px;}
.side-brand span {display: block; font-size: .85rem; font-weight: 400; color: #667085;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

pio.templates["clean"] = go.layout.Template(layout=go.Layout(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    font=dict(color="#475467", family=CHART_FONT, size=13),
    colorway=list(COLORS.values()),
    xaxis=dict(gridcolor="#F0F2F5", zerolinecolor="#D0D5DD", linecolor="#D0D5DD",
               ticks="", showline=True),
    yaxis=dict(gridcolor="#F0F2F5", zerolinecolor="#D0D5DD", linecolor="#D0D5DD", ticks=""),
    margin=dict(t=30, l=8, r=16, b=8),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02,
                xanchor="left", x=0, title_text=""),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#D0D5DD",
                    font=dict(color=INK, family=CHART_FONT))))
ROW_TICKS = dict(tickvals=[1e4, 1e5, 1e6, 1e7], ticktext=["10k", "100k", "1M", "10M"])


# ---------------- SMALL HELPERS ----------------
def show(fig, height=None):
    # Set the look on each chart directly: Streamlit otherwise paints the plot area.
    fig.update_layout(template="plotly_white+clean", paper_bgcolor="#FFFFFF",
                      plot_bgcolor="#FFFFFF",
                      font=dict(color="#475467", family=CHART_FONT, size=13))
    axis = dict(gridcolor="#F0F2F5", zerolinecolor="#D0D5DD", linecolor="#D0D5DD")
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, theme=None, config={"displaylogo": False})


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def rs(x):
    return f"Rs. {x:,.0f}"


def card(name):
    return st.container(key=f"card_{name}")


def card_head(title, sub=""):
    html(f'<div class="card-h"><h4>{title}</h4><p>{sub}</p></div>')


def page_head(crumb, title, sub, tags=()):
    tag_html = "".join(f'<span class="tag {cls}">{t}</span> ' for t, cls in tags)
    html(f'<div class="page-h"><div><p class="crumb">{crumb}</p><h1>{title}</h1>'
         f'<p class="sub">{sub}</p></div><div>{tag_html}</div></div>')


def kpi_cards(items):
    """items: (label, value, chip_text, chip_tone, note)."""
    cells = []
    for lbl, val, chip, tone, note in items:
        chip_html = f'<span class="chip {tone}">{chip}</span>' if chip else ""
        cells.append(f'<div class="kpi"><div class="lbl">{lbl}</div><div class="row">'
                     f'<span class="val">{val}</span>{chip_html}</div>'
                     f'<div class="note">{note}</div></div>')
    html(f'<div class="kpis">{"".join(cells)}</div>')


def segmented(label, options, key, default):
    """Segmented control where available (Streamlit 1.40+), radio otherwise."""
    if key not in st.session_state:
        st.session_state[key] = default
    if hasattr(st, "segmented_control"):
        val = st.segmented_control(label, options, key=key)
    else:
        val = st.radio(label, options, key=key, horizontal=True)
    if val is None:  # clicking the active option un-selects it; keep a brand chosen
        val = default
    return val


# ---------------- DATA + CACHED MODELS ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def get_curves(brand):
    d = load_data()
    return fit_curves(d[d.brand == brand])


@st.cache_data
def bootstrap_curves(brand, n_boot=N_BOOT, seed=0):
    """Refit the curves on random resamples of one brand's data."""
    d = load_data()
    d = d[d.brand == brand]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(d), len(d))
        try:
            out.append(fit_curves(d.iloc[idx]))
        except RuntimeError:
            pass  # skip the rare resample where the fit does not converge
    return out


@st.cache_data
def profit_curve(brand, plats, slices, margin, min_share, max_share, max_budget):
    curves = get_curves(brand)
    ps = {p: curves[p] for p in plats}
    out = []
    for b in np.linspace(100_000, max_budget, 50):
        al = optimize(ps, b, slices, min_share, max_share)
        t = evaluate(al, ps, slices, margin)
        out.append(dict(budget=b, revenue=t.revenue.sum(), profit=t.profit.sum()))
    return pd.DataFrame(out)


@st.cache_data
def read_csv(name):
    f = PROC / name
    return pd.read_csv(f) if f.exists() else None


df_all = load_data()
all_plats = list(COLORS)

# ---------------- SIDEBAR: brand + settings ----------------
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
    html('<div class="side-brand">Ad budget optimizer<span>Borjan, Servis and Ndure</span></div>')
    brand = segmented("Brand", G.BRANDS, key="brand", default=G.BRANDS[0])
    with st.expander("Budget settings", expanded=True):
        st.selectbox("Scenario", list(PRESETS), key="preset", on_change=apply_preset)
        budget = st.number_input("Monthly ad budget (Rs.)", min_value=100_000,
                                 max_value=50_000_000, step=100_000, key="budget")
        margin = st.slider("Gross margin on shoes", min_value=0.20, max_value=0.80, step=0.05,
                           key="margin",
                           help="Share of revenue left after product cost. ASSUMPTION.")
        slices = st.slider("Ad slices per platform (days × ad sets)", min_value=15,
                           max_value=180, step=15, key="slices",
                           help="Default 60 = 30 days × 2 ad sets. Sets the scale. ASSUMPTION.")
        platforms = st.multiselect("Platforms allowed", all_plats, key="platforms")
        min_share = st.slider("Minimum share per platform (%)", min_value=0, max_value=20,
                              key="min_share") / 100
        max_share = st.slider("Maximum share per platform (%)", min_value=20, max_value=100,
                              key="max_share") / 100
    st.caption("Ad data is simulated. Customer sentiment per brand comes from Project 1.")

# ---------------- OPTIMISE FOR THE CHOSEN BRAND ----------------
df = df_all[df_all.brand == brand]
curves = get_curves(brand)
settings_ok = True
problem = ""
if not platforms:
    settings_ok, problem = False, "Pick at least one platform."
elif min_share * len(platforms) > 1:
    settings_ok, problem = False, "Minimum shares add up to more than 100%. Lower the minimum."
elif max_share * len(platforms) < 1:
    settings_ok, problem = False, "Maximum shares can't cover 100% of the budget. Raise the maximum."

if settings_ok:
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
    order = rec.sort_values("spend", ascending=False)
    funded = order[order.spend > 1]

SIM_TAG = ("Simulated ad data", "sim")


def need_settings():
    if not settings_ok:
        st.error(problem)
        st.stop()


# =====================================================================
# PAGE 1: OVERVIEW
# =====================================================================
def page_overview():
    need_settings()
    page_head("Dashboard / Overview", f"{brand}: where should the next {rs(budget)} go?",
              "The optimizer learns how fast each platform runs out of steam for this brand, "
              "then splits the monthly budget so every rupee goes where it earns the most.",
              [(brand, ""), SIM_TAG])
    kpi_cards([
        ("Expected revenue", rs(tot_rev), f"ROAS {tot_rev / budget:.2f}", "neutral",
         "per month, with the recommended split"),
        ("Expected profit", rs(tot_profit), "", "",
         f"after a {margin:.0%} margin and the ad spend"),
        ("Gain vs equal split", f"{opt_gain:+.1f}%", f"+{rs(tot_rev - eq_rev)}",
         "good" if opt_gain >= 0 else "bad", "more revenue than splitting evenly"),
        (f"Gain vs all on {best}", f"{(tot_rev / allbest_rev - 1) * 100:+.0f}%",
         "", "", "why just picking the best ROAS fails"),
    ])

    left, right = st.columns([7, 5], gap="medium")
    with left:
        with card("alloc"):
            card_head("Recommended allocation", f"Monthly spend per platform for {brand}")
            rows = []
            for _, r in order.iterrows():
                p, on = r["platform"], r["spend"] > 1
                meta = (f'{rs(r["spend"])} &nbsp;·&nbsp; expected revenue {rs(r["revenue"])} '
                        f'&nbsp;·&nbsp; ROAS {r["ROAS"]:.2f}' if on else
                        f'Not funded: its first rupee returns only Rs. {r["marginal_ROAS"]:.2f}')
                rows.append(
                    f'<div class="alloc-row{"" if on else " off"}"><div class="alloc-top">'
                    f'<span class="alloc-name"><span class="sw" style="background:{COLORS[p]}">'
                    f'</span>{p}</span><span class="alloc-pct">{r["share_%"]:.1f}%</span></div>'
                    f'<div class="alloc-track"><div class="alloc-fill" style="width:'
                    f'{r["share_%"]:.2f}%;background:{COLORS[p]}"></div></div>'
                    f'<div class="alloc-meta">{meta}</div></div>')
            html("".join(rows))
    with right:
        with card("why"):
            card_head("Why this split?", "The rule the optimizer follows")
            names = funded.platform.tolist()
            zero = [p for p in platforms if alloc[p] <= 1]
            lo, hi = funded.marginal_ROAS.min(), funded.marginal_ROAS.max()
            back = f"Rs. {lo:.2f}" if f"{lo:.2f}" == f"{hi:.2f}" else f"Rs. {lo:.2f} to {hi:.2f}"
            why = f"Lead with <b>{names[0]}</b>"
            if len(names) > 1:
                why += f" and <b>{names[1]}</b>"
            why += (". Each platform gets money until its <i>next</i> rupee earns about the "
                    f"same as everywhere else: about <b>{back}</b> back per rupee. ")
            if zero:
                verb = "gets" if len(zero) == 1 else "get"
                why += f"{', '.join(zero)} {verb} nothing, because the first rupee there earns less. "
            why += f"At a {margin:.0%} margin, break-even is a ROAS of <b>{breakeven:.2f}</b>."
            html(f'<div class="why">{why}</div>')
            if lo < breakeven:
                st.warning("Some of the last rupees lose money after product costs: this "
                           "budget is above the profit-maximising level (see Plan & scenarios).")
        with card("sentiment"):
            s = G.SENTIMENT[brand]
            card_head("Customer sentiment (Project 1)",
                      f"XLM-R predictions on {s['reviews']} {brand} reviews and comments")
            html(f'<div class="fact"><span>Positive</span><b>{s["positive"] * 100:.0f}%</b></div>'
                 f'<div class="fact"><span>Negative</span><b>{s["negative"] * 100:.0f}%</b></div>'
                 f'<div class="fact"><span>Effect on ad conversion rate</span>'
                 f'<b>{(G.sentiment_mult(brand) - 1) * 100:+.1f}%</b></div>')
            st.caption(f"Better-liked brands convert more of their clicks. "
                       f"[Project 1 repo]({P1_URL})")

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with card("strategies"):
            card_head("Optimizer vs simple strategies",
                      "Expected monthly revenue for the same budget, split four ways")
            cmp = comp.iloc[::-1]
            fig = go.Figure(go.Bar(
                y=cmp.strategy, x=cmp.revenue, orientation="h",
                marker_color=[NAVY if s == "Optimizer" else GREY_LIGHT for s in cmp.strategy],
                text=[f"{g:+.1f}%" for g in cmp["vs_equal_%"]], textposition="outside",
                cliponaxis=False,
                hovertemplate="%{y}: Rs. %{x:,.0f}<extra></extra>"))
            fig.update_layout(xaxis_title="Expected revenue (Rs.)", showlegend=False,
                              xaxis_range=[0, comp.revenue.max() * 1.18], margin=dict(t=6),
                              yaxis=dict(showline=False, ticksuffix="  "))
            show(fig, 260)
            st.caption("Percentages are vs the equal split.")
    with c2:
        with card("bootstrap"):
            card_head("How sure are we?",
                      f"Recommended share with its 90% range ({N_BOOT} bootstrap resamples)")
            boots = bootstrap_curves(brand)
            shares = []
            for bc in boots:
                al = optimize({p: bc[p] for p in platforms}, budget, slices, min_share, max_share)
                shares.append({p: al.get(p, 0.0) / budget * 100 for p in all_plats})
            sh = pd.DataFrame(shares)
            ci = pd.DataFrame({"platform": all_plats,
                               "recommended_%": [alloc[p] / budget * 100 for p in all_plats],
                               "low_%": sh[all_plats].quantile(0.05).to_numpy(),
                               "high_%": sh[all_plats].quantile(0.95).to_numpy()})
            ci = ci.set_index("platform").loc[order.platform.tolist()[::-1]].reset_index()
            fig = go.Figure()
            for _, r in ci.iterrows():
                p = r["platform"]
                fig.add_trace(go.Scatter(
                    x=[r["recommended_%"]], y=[p], mode="markers", showlegend=False,
                    marker=dict(size=11, color=COLORS[p], line=dict(color="#FFFFFF", width=2)),
                    error_x=dict(type="data", symmetric=False, thickness=2, width=5,
                                 color=COLORS[p],
                                 array=[max(r["high_%"] - r["recommended_%"], 0)],
                                 arrayminus=[max(r["recommended_%"] - r["low_%"], 0)]),
                    hovertemplate=(f"{p}: %{{x:.1f}}% (90% range {r['low_%']:.1f}% to "
                                   f"{r['high_%']:.1f}%)<extra></extra>")))
            fig.update_layout(xaxis_title="Share of budget (%)", margin=dict(t=6),
                              xaxis_range=[0, max(ci["high_%"].max() * 1.12, 5)],
                              yaxis=dict(ticksuffix="  "))
            show(fig, 260)
            st.caption("Covers noise from limited data only, not a wrong curve shape. "
                       "The Validation page checks that these ranges are honest.")

    with st.expander("Detailed plan table and download"):
        show_t = rec[["platform", "share_%", "spend", "revenue", "ROAS", "marginal_ROAS", "profit"]]
        st.dataframe(show_t.style.format({
            "share_%": "{:.1f}%", "spend": "Rs. {:,.0f}", "revenue": "Rs. {:,.0f}",
            "ROAS": "{:.2f}", "marginal_ROAS": "{:.2f}", "profit": "Rs. {:,.0f}"},
            na_rep="–"), hide_index=True)
        st.download_button("Download plan (CSV)", show_t.assign(brand=brand).to_csv(index=False),
                           f"{brand.lower()}_budget_plan.csv", "text/csv")



# =====================================================================
# PAGE 2: MARKETING PLAN (where to spend, who to target, what to say, when)
# =====================================================================
PRAISE_ANGLE = {
    "comfort": "Lead with all-day comfort: walking shots, 'comfortable from day one' claims.",
    "design": "Lead with the look: new-collection visuals, styling reels, colour variety.",
    "staff": "Show the in-store experience: helpful staff, 'visit your nearest outlet'.",
    "quality": "Lead with durability: materials, stitching close-ups, 'built to last'.",
    "price": "Lead with value: price points on the creative, bundles, 'worth every rupee'.",
    "size": "Lead with fit: true-to-size claims and the full size range.",
    "delivery": "Lead with convenience: fast delivery and easy online ordering.",
}
FIX_ANGLE = {
    "price": "Price is a pain point: show offers, bundles and sale prices clearly in the ad.",
    "size": "Sizing is a pain point: add a size guide and 'easy exchange' to the ad and landing page.",
    "staff": "In-store service gets complaints: push online ordering and fix service before driving footfall.",
    "quality": "Quality is doubted: use proof (warranty, materials, reviews) rather than claims.",
    "design": "Designs split opinion: test several creatives and keep the winners.",
    "comfort": "Comfort gets complaints: avoid comfort claims until the product answers them.",
    "delivery": "Delivery gets complaints: promise only delivery times you can keep.",
}
MIN_MENTIONS = 10  # below this an aspect is shown as a weak signal only


def segment_view(d, dim):
    """Per platform: the segment that brings most revenue (reach) and the one with the
    best ROAS, flagged only when it beats the platform average by 10% or more."""
    t = kpi_table(d, ["platform", dim])
    out = {}
    for p, g in t.groupby("platform"):
        core = g.loc[g.revenue.idxmax(), dim]
        avg = g.revenue.sum() / g.spend.sum()
        top = g.loc[g.ROAS.idxmax()]
        out[p] = (str(core), str(top[dim]) if top.ROAS >= 1.1 * avg else "no clear winner",
                  top.ROAS / avg - 1)
    return out


def say_card(praise, fixes):
    """Headline for the 'What to say' card: the top praise, else the top complaint to fix."""
    if len(praise):
        r = praise.iloc[0]
        return ("What to say", r.aspect.capitalize(), f"{r.positive:.0%} positive", "good",
                "what customers praise most (Project 1)")
    if len(fixes):
        r = fixes.iloc[0]
        name = {"size": "sizing", "staff": "store service"}.get(r.aspect, r.aspect)
        return ("What to say", f"Fix {name}", f"{r.negative:.0%} negative", "bad",
                "the top complaint in Project 1 reviews")
    return ("What to say", "Test creatives", "", "", "no clear strength or complaint yet")


def brand_messaging(b):
    """Aspect table for a brand, plus what customers praise and complain about
    (only aspects with enough mentions)."""
    asp = read_csv("brand_aspects.csv")
    a = asp[asp.brand == b] if asp is not None else pd.DataFrame(
        columns=["brand", "aspect", "mentions", "positive", "negative", "net"])
    solid = a[a.mentions >= MIN_MENTIONS]
    praise = solid[solid.positive >= 0.5].sort_values("positive", ascending=False)
    fixes = solid[solid.negative >= 0.35].sort_values("negative", ascending=False)
    return a, praise, fixes


def page_marketing():
    need_settings()
    page_head("Dashboard / Marketing plan", f"{brand} marketing plan",
              "Where to spend, who to target, what to say and when to push, in one page.",
              [(brand, ""), SIM_TAG])
    a, praise, fixes = brand_messaging(brand)
    camp = kpi_table(df, ["campaign"]).sort_values("ROAS", ascending=False)
    avg_roas = df.revenue.sum() / df.spend.sum()
    ages, cities = segment_view(df, "age"), segment_view(df, "city")
    devices, genders = segment_view(df, "device"), segment_view(df, "gender")
    lead = order.iloc[0]

    kpi_cards([
        ("Where to spend", f"{lead.platform} {lead['share_%']:.0f}%", "", "",
         f"then {order.iloc[1].platform} {order.iloc[1]['share_%']:.0f}% and "
         f"{order.iloc[2].platform} {order.iloc[2]['share_%']:.0f}%"),
        ("Who to target", f"{ages[lead.platform][0]}", "", "",
         f"core age group on {lead.platform}, mostly {cities[lead.platform][0]}"),
        say_card(praise, fixes),
        ("When to push", camp.campaign.iloc[0],
         f"ROAS {camp.ROAS.iloc[0]:.2f}", "good", "the campaign that earns the most per rupee"),
    ])

    with card("mk_where"):
        card_head("1. Where to spend and who to target",
                  "Core audience = the segment that brings the most revenue. Best return = the "
                  "segment with the highest ROAS, shown only if it beats the platform average by "
                  "10% or more.")
        rows = []
        for _, r in order.iterrows():
            p = r["platform"]
            if r["spend"] <= 1:
                continue
            br = [f"{v[1]} ({v[2]:+.0%})" if v[1] != "no clear winner" else "–"
                  for v in (ages[p], cities[p], devices[p])]
            rows.append({"Platform": p, "Share": f"{r['share_%']:.1f}%", "Monthly spend": rs(r["spend"]),
                         "Core age": ages[p][0], "Core city": cities[p][0],
                         "Core device": devices[p][0], "Best-return age": br[0],
                         "Best-return city": br[1], "Best-return device": br[2]})
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("Segment results come from the simulated ad data, so they reflect the "
                   "assumptions (for example younger audiences on TikTok and Instagram). Gender "
                   "differences were too small to act on.")

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with card("mk_say"):
            card_head("2. What to say in the ads",
                      f"From Project 1: what {brand} customers praise and complain about")
            if a.empty:
                st.info("Run src/analysis/project1_aspects.py to create brand_aspects.csv.")
            else:
                html('<p class="why"><b>Lead with</b></p>')
                if len(praise):
                    for _, r in praise.head(2).iterrows():
                        html(f'<div class="fact"><span>{PRAISE_ANGLE[r.aspect]}</span>'
                             f'<b>{r.positive:.0%} positive</b></div>')
                else:
                    html('<div class="fact"><span>No aspect is clearly praised yet: test several '
                         'creative angles and keep the winners.</span><b>–</b></div>')
                html('<p class="why" style="margin-top:12px"><b>Fix or answer</b></p>')
                if len(fixes):
                    for _, r in fixes.head(2).iterrows():
                        html(f'<div class="fact"><span>{FIX_ANGLE[r.aspect]}</span>'
                             f'<b>{r.negative:.0%} negative</b></div>')
                else:
                    html('<div class="fact"><span>No strong complaint found.</span><b>–</b></div>')
                with st.expander("All aspects (mentions, positive, negative)"):
                    st.dataframe(a.drop(columns="brand").style.format(
                        {"positive": "{:.0%}", "negative": "{:.0%}", "net": "{:+.0%}"}),
                        hide_index=True)
                st.caption(f"Based on real reviews and comments from Project 1, labelled by a "
                           f"moderately accurate model (accuracy 0.55). Aspects with fewer than "
                           f"{MIN_MENTIONS} mentions are left out of the advice.")
    with c2:
        with card("mk_when"):
            card_head("3. When to push", "Campaign return per rupee, compared with this brand's "
                      "average")
            cm = camp[["campaign", "ROAS", "spend", "revenue"]].copy()
            cm["Advice"] = np.where(cm.ROAS >= 1.2 * avg_roas, "Boost",
                                    np.where(cm.ROAS <= 0.8 * avg_roas, "Reduce", "Keep"))
            st.dataframe(cm.rename(columns={"campaign": "Campaign", "spend": "Spend",
                                            "revenue": "Revenue"}).style.format(
                {"ROAS": "{:.2f}", "Spend": "Rs. {:,.0f}", "Revenue": "Rs. {:,.0f}"}),
                hide_index=True)
            boost = cm[cm.Advice == "Boost"].campaign.tolist()
            reduce_ = cm[cm.Advice == "Reduce"].campaign.tolist()
            msg = ""
            if boost:
                msg += f"Move budget into **{', '.join(boost)}**"
            if reduce_:
                msg += f"{' and away from' if boost else 'Cut'} **{', '.join(reduce_)}**"
            if msg:
                st.markdown(msg + ".")
            st.caption("Campaign windows use 2025 dates in the simulation; Eid dates move each year.")

    # one-page plan to download
    lines = [f"{brand.upper()} MARKETING PLAN (budget {rs(budget)} per month)",
             "Ad data is simulated; customer sentiment is from Project 1.", "",
             "1. WHERE TO SPEND AND WHO TO TARGET"]
    for _, r in order.iterrows():
        if r["spend"] > 1:
            p = r["platform"]
            lines.append(f"- {p}: {r['share_%']:.1f}% ({rs(r['spend'])}). Core audience: "
                         f"{ages[p][0]}, {cities[p][0]}, {devices[p][0]}.")
    lines += ["", "2. WHAT TO SAY"]
    lines += [f"- {PRAISE_ANGLE[x]}" for x in praise.aspect.head(2)] or ["- Test several creative angles."]
    lines += [f"- {FIX_ANGLE[x]}" for x in fixes.aspect.head(2)]
    lines += ["", "3. WHEN TO PUSH"]
    lines += [f"- {r.campaign}: ROAS {r.ROAS:.2f} -> {r.Advice}" for r in cm.itertuples()]
    st.download_button("Download this marketing plan (TXT)", "\n".join(lines),
                       f"{brand.lower()}_marketing_plan.txt", "text/plain", type="primary")


# =====================================================================
# PAGE: AD COPY STUDIO
# =====================================================================
LANG_LABEL = {"en": "English", "ru": "Roman Urdu"}


def page_adcopy():
    need_settings()
    page_head("Dashboard / Ad copy studio", f"{brand} ad copy studio",
              "Ready-to-use ad copy for every funded platform, built from the budget plan and "
              "what real customers say about the brand.", [(brand, ""), ("Sample copy", "sim")])
    a, praise, fixes = brand_messaging(brand)
    lead, test, fix = AC.angles_for(praise.aspect.tolist(), fixes.aspect.tolist())
    praised, complained = set(praise.aspect), set(fixes.aspect)

    def source(angle):
        if angle in praised:
            r = praise[praise.aspect == angle].iloc[0]
            return f"customers praise it ({r.positive:.0%} positive)"
        if angle in complained:
            r = fixes[fixes.aspect == angle].iloc[0]
            return f"answers a complaint ({r.negative:.0%} negative)"
        return "a test idea, not from reviews"

    c1, c2 = st.columns([3, 2])
    campaign = c1.selectbox("Campaign", list(AC.CAMPAIGNS),
                            index=list(AC.CAMPAIGNS).index("11.11 Mega Sale"))
    lang = c2.radio("Language", ["en", "ru"], format_func=LANG_LABEL.get, horizontal=True)

    ages, cities = segment_view(df, "age"), segment_view(df, "city")
    devices = segment_view(df, "device")
    plan_rows = [(r["platform"], r["share_%"], r["spend"]) for _, r in order.iterrows()
                 if r["spend"] > 1 and r["share_%"] >= 3]
    audiences = {p: f"{ages[p][0]}, {cities[p][0]}, {devices[p][0]}" for p, _, _ in plan_rows}
    copies = {p: {lg: AC.ad_copy(brand, p, campaign, lead, test, fix, lg) for lg in ("en", "ru")}
              for p, _, _ in plan_rows}

    kpi_cards([
        ("Lead message (A)", lead.capitalize(), "", "", source(lead)),
        ("Test message (B)", test.capitalize(), "", "", source(test)),
        ("Reassure on", fix.capitalize() if fix else "Nothing", "", "",
         "a short line in every ad" if fix else "no other strong complaint"),
        ("Campaign", campaign.replace(" Sale", ""), "", "", AC.CAMPAIGNS[campaign][lang]),
    ])

    for p, share, spend in plan_rows:
        x = copies[p][lang]
        with card(f"ad_{p}"):
            card_head(f"{p}: {share:.1f}% of the budget ({rs(spend)} a month)",
                      f"{AC.PLATFORMS[p]['format']}. Audience: {audiences[p]}.")
            left, right = st.columns([3, 2], gap="medium")
            with left:
                st.caption("Headline A")
                st.code(x["headline_a"], language=None)
                st.caption("Ad text A")
                st.code(x["text_a"], language=None, wrap_lines=True)
                st.caption("Headline B (for the A/B test)")
                st.code(x["headline_b"], language=None)
                if "google_headlines" in x:
                    st.caption("Search ad headlines (each 30 characters or fewer)")
                    st.code("\n".join(x["google_headlines"]), language=None)
                    st.caption("Search ad descriptions (each 90 characters or fewer)")
                    st.code("\n".join(x["google_descriptions"]), language=None, wrap_lines=True)
                    st.caption("Keywords")
                    st.code(", ".join(x["keywords"]), language=None)
                else:
                    st.caption("Hashtags")
                    st.code(x["hashtags"], language=None)
            with right:
                html(f'<div class="fact"><span>Call to action</span><b>{x["cta"]}</b></div>'
                     f'<div class="fact"><span>Format</span><b>{AC.PLATFORMS[p]["format"].split(",")[0]}</b></div>')
                html(f'<p class="why" style="margin-top:10px"><b>Creative tips.</b> '
                     f'{AC.PLATFORMS[p]["tips"]}</p>')

    with card("ad_test"):
        card_head("How to use this copy", "")
        st.markdown(
            "1. **Run A and B side by side** with equal budget for the first week.\n"
            "2. **Keep the winner:** move the budget to whichever headline gets more orders per "
            "rupee.\n"
            "3. **Reply to comments fast:** questions about price, size and delivery are buying "
            "signals.")
        st.caption("This is sample copy written by the tool for a class project. It is not the "
                   "brand's real advertising and uses none of its real slogans.")
    st.download_button("Download the campaign brief (TXT)",
                       AC.brief_text(brand, campaign, budget, plan_rows, copies, audiences,
                                     lead, test, fix),
                       f"{brand.lower()}_campaign_brief.txt", "text/plain", type="primary")

# =====================================================================
# PAGE 3: PLAN & SCENARIOS
# =====================================================================
def page_plan():
    need_settings()
    page_head("Dashboard / Plan & scenarios", "Plan & scenarios",
              "How each platform's returns flatten out, and whether the total budget itself "
              "is the right size. Change the settings in the sidebar to try scenarios.",
              [(brand, ""), SIM_TAG])
    with card("curves"):
        card_head("Diminishing returns per platform",
                  "Expected monthly revenue for a given monthly spend. "
                  "Dots mark the recommended spend.")
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
                    mode="markers", showlegend=False,
                    marker=dict(size=11, color=COLORS[p], line=dict(color="#FFFFFF", width=2)),
                    hovertemplate=f"{p} recommended: Rs. %{{x:,.0f}}<extra></extra>"))
        fig.update_layout(xaxis_title="Monthly spend on platform (Rs.)",
                          yaxis_title="Expected revenue (Rs.)", margin=dict(t=40))
        show(fig, 430)

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        with card("profit"):
            card_head("Is this the right total budget?",
                      "Expected profit if the whole budget is split optimally")
            pcurve = profit_curve(brand, tuple(platforms), slices, margin, min_share, max_share,
                                  float(max(5_000_000, 2 * budget)))
            top = pcurve.loc[pcurve.profit.idxmax()]
            fig = go.Figure(go.Scatter(x=pcurve.budget, y=pcurve.profit, mode="lines",
                                       line=dict(color=NAVY, width=2), showlegend=False,
                                       hovertemplate="Budget Rs. %{x:,.0f} → profit "
                                                     "Rs. %{y:,.0f}<extra></extra>"))
            fig.add_vline(x=budget, line_dash="dash", line_color=GREY, line_width=1,
                          annotation_text="Your budget", annotation_font_color=INK_2)
            fig.add_vline(x=top.budget, line_dash="dot", line_color=GOOD, line_width=1,
                          annotation_text="Profit peak", annotation_font_color=GOOD,
                          annotation_position="top left")
            fig.update_layout(xaxis_title="Total monthly budget (Rs.)",
                              yaxis_title="Expected profit (Rs.)", margin=dict(t=24))
            show(fig, 340)
            st.caption(f"Profit peaks near {rs(top.budget)} (about {rs(top.profit)}). Beyond "
                       "that, extra ad spend earns back less than it costs.")
    with c2:
        with card("fit"):
            card_head("Fitted curve per platform",
                      "revenue(s) = a·s / (1 + s/h), fitted on this brand's data")
            fit = pd.DataFrame(curves).T.reset_index().rename(columns={"index": "platform"})
            fit = fit[["platform", "a", "a_se", "h", "h_se"]]
            st.dataframe(fit.style.format({"a": "{:.2f}", "a_se": "±{:.2f}", "h": "{:,.0f}",
                                           "h_se": "±{:,.0f}"}), hide_index=True)
            st.caption("a is the ROAS at very small spend, h is the spend per slice where "
                       "efficiency halves, and ± is the standard error of the fit.")


# =====================================================================
# PAGE 3: PERFORMANCE (KPI explorer)
# =====================================================================
def page_performance():
    page_head("Dashboard / Performance", "Campaign performance",
              "Historical (simulated) KPIs, always computed from totals, never by averaging "
              "row-level ratios.", [(brand, ""), SIM_TAG])
    with card("brands"):
        card_head("All three brands", "Same platforms and campaigns, different audiences "
                  "and customer sentiment")
        kb = kpi_table(df_all, ["brand"]).set_index("brand").loc[G.BRANDS].reset_index()
        kb["sentiment"] = kb.brand.map(lambda b: f"{G.net_sentiment(b) * 100:+.0f} pts")
        st.dataframe(kb[["brand", "spend", "revenue", "ROAS", "CTR_%", "CVR_%", "CPA",
                         "sentiment"]].style.format({
            "spend": "Rs. {:,.0f}", "revenue": "Rs. {:,.0f}", "ROAS": "{:.2f}",
            "CTR_%": "{:.2f}%", "CVR_%": "{:.2f}%", "CPA": "Rs. {:,.0f}"}), hide_index=True)
        st.caption("sentiment = positive minus negative share from Project 1.")

    with card("kpi_plat"):
        card_head(f"{brand}: KPIs by platform")
        k = kpi_table(df, ["platform"])
        st.dataframe(k.style.format({
            "impressions": "{:,.0f}", "clicks": "{:,.0f}", "spend": "Rs. {:,.0f}",
            "conversions": "{:,.0f}", "revenue": "Rs. {:,.0f}", "CPC": "Rs. {:.1f}",
            "CPA": "Rs. {:,.0f}", "profit_proxy": "Rs. {:,.0f}"}), hide_index=True)
        st.caption("profit_proxy = revenue − ad spend (ignores product cost).")

    with card("explore"):
        card_head("Explore segments", "Pick a breakdown and a metric")
        dims = {"Campaign": "campaign", "Age": "age", "Gender": "gender",
                "City": "city", "Device": "device"}
        c1, c2 = st.columns(2)
        dim = dims[c1.selectbox("Break down by", list(dims))]
        metric = c2.selectbox("Metric", ["ROAS", "CTR_%", "CVR_%", "CPC", "CPA"])
        t = kpi_table(df, ["platform", dim])
        pivot = t.pivot(index="platform", columns=dim, values=metric)
        fig = px.imshow(pivot, text_auto=".2f", aspect="auto", color_continuous_scale="Blues")
        fig.update_traces(xgap=2, ygap=2)
        fig.update_layout(xaxis_title="", yaxis_title="", margin=dict(t=10),
                          coloraxis_colorbar=dict(title="", thickness=12))
        show(fig, 360)
        st.caption("Darker means a higher value. For CPC and CPA, lower is better.")

        m = kpi_table(df, ["month", "platform"])
        fig = go.Figure()
        for p in all_plats:
            mp = m[m.platform == p]
            fig.add_trace(go.Scatter(x=mp.month, y=mp[metric], name=p, mode="lines+markers",
                                     line=dict(color=COLORS[p], width=2), marker=dict(size=6)))
        fig.update_layout(yaxis_title=f"Monthly {metric}", hovermode="x unified",
                          margin=dict(t=40))
        show(fig, 360)
        st.caption("Peaks match the simulated Eid ul Fitr (Mar), Eid ul Adha (late May to Jun) "
                   "and 11.11 (Nov) campaigns.")


# =====================================================================
# PAGE 4: VALIDATION
# =====================================================================
def page_validation():
    page_head("Dashboard / Validation", "Can we trust the optimizer?",
              "The data is simulated, so the true best split is known. Three checks score the "
              "optimizer against it.", [(brand, ""), SIM_TAG])
    vs, tr = read_csv("validation_summary.csv"), read_csv("true_optimum.csv")
    hm, cov = read_csv("hard_mode_summary.csv"), read_csv("bootstrap_coverage_overall.csv")

    # ---- 1. best case ----
    with card("val1"):
        card_head("1. Does it find the true best split?",
                  "Data regenerated 5 times at 10k, 100k and 1M rows of this brand; every "
                  "result scored against the truth")
        if vs is None:
            st.info("Run src/optimizer/validate.py to create these results.")
        else:
            v = vs[vs.brand == brand].reset_index(drop=True)
            kpi_cards([
                ("Optimizer at 10k rows", f"{v.optimizer_pct_mean.iloc[0]:.2f}%", "", "",
                 "of the true best revenue"),
                ("Last year's split", f"{v.lastyear_pct.iloc[0]:.1f}%", "", "",
                 "of the true best revenue"),
                ("Equal split", f"{v.equal_pct.iloc[0]:.1f}%", "", "",
                 "of the true best revenue"),
                ("Share error (pp)",
                 f"{v.share_error_pp_mean.iloc[0]:.2f} → {v.share_error_pp_mean.iloc[-1]:.2f}",
                 "", "", "from 10k to 1M rows: more data, more precise"),
            ])
            fig = go.Figure(go.Scatter(
                x=v.rows, y=v.share_error_pp_mean, mode="lines+markers", showlegend=False,
                line=dict(color=NAVY, width=2), marker=dict(size=9),
                error_y=dict(array=v.share_error_pp_std, thickness=1.5, width=5, color=NAVY),
                hovertemplate="%{x:,} rows: %{y:.2f} pp<extra></extra>"))
            fig.update_xaxes(**ROW_TICKS)
            fig.update_layout(xaxis_type="log", xaxis_title="Rows of data (log scale)",
                              yaxis_title="Average share error (pp)", yaxis_rangemode="tozero",
                              margin=dict(t=10))
            show(fig, 300)
            with st.expander("Validation table and true vs fitted parameters"):
                st.dataframe(v.drop(columns="brand").rename(columns={
                    "rows": "Rows", "optimizer_pct_mean": "Optimizer (% of best)",
                    "optimizer_pct_std": "Optimizer spread",
                    "lastyear_pct": "Last year's split (%)", "equal_pct": "Equal split (%)",
                    "share_error_pp_mean": "Share error (pp)",
                    "share_error_pp_std": "Error spread (pp)"}).style.format(
                    {"Rows": "{:,}", "Optimizer (% of best)": "{:.2f}%",
                     "Optimizer spread": "±{:.2f}", "Last year's split (%)": "{:.1f}%",
                     "Equal split (%)": "{:.1f}%", "Share error (pp)": "{:.2f}",
                     "Error spread (pp)": "±{:.2f}"}), hide_index=True)
                if tr is not None:
                    t = tr[tr.brand == brand].copy()
                    t["fitted_a (10k)"] = t.platform.map(lambda p: curves[p]["a"])
                    t["fitted_h (10k)"] = t.platform.map(lambda p: curves[p]["h"])
                    st.dataframe(t.drop(columns="brand").round(2), hide_index=True)

    # ---- 2. hard mode ----
    with card("val2"):
        card_head("2. Hard mode: what if the real curve has a different shape?",
                  "Check 1 is a best case: the data uses the curve shape the optimizer assumes. "
                  "Here the data comes from an exponential curve (saturates faster) and an "
                  "S-curve (small budgets barely work).")
        if hm is None:
            st.info("Run src/optimizer/hard_mode.py to create these results.")
        else:
            h = hm[hm.brand == brand].copy()
            h["shape_lbl"] = h["shape"].map(SHAPE_LABELS)
            h10 = h[h.rows == h.rows.min()].set_index("shape_lbl")
            h1m = h[h.rows == h.rows.max()].set_index("shape_lbl")
            worst = h.optimizer_pct_min.min()
            kpi_cards([
                ("Same shape, 10k rows", f"{h10.loc['Same as assumed', 'optimizer_pct_mean']:.2f}%",
                 "", "", "of the true best revenue"),
                ("Exponential, 1M rows", f"{h1m.loc['Exponential', 'optimizer_pct_mean']:.2f}%",
                 "", "", f"equal split: {h1m.loc['Exponential', 'equal_pct']:.1f}%"),
                ("S-curve, 1M rows", f"{h1m.loc['S-curve', 'optimizer_pct_mean']:.2f}%",
                 "", "", f"equal split: {h1m.loc['S-curve', 'equal_pct']:.1f}%"),
                ("Worst single run", f"{worst:.1f}%", "weakest" if worst < 95 else "",
                 "bad" if worst < 95 else "", "lowest of all hard-mode runs"),
            ])
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                long = h1m.reset_index().melt(
                    id_vars="shape_lbl",
                    value_vars=["optimizer_pct_mean", "lastyear_pct", "equal_pct"],
                    var_name="strategy", value_name="pct")
                long["strategy"] = long.strategy.map({"optimizer_pct_mean": "Optimizer",
                                                      "lastyear_pct": "Last year's split",
                                                      "equal_pct": "Equal split"})
                fig = go.Figure()
                for strat, col, size in [("Equal split", GREY_LIGHT, 11),
                                         ("Last year's split", GREY, 11),
                                         ("Optimizer", NAVY, 13)]:
                    d = long[long.strategy == strat]
                    fig.add_trace(go.Scatter(
                        x=d.pct, y=d.shape_lbl, mode="markers", name=strat,
                        marker=dict(size=size, color=col, line=dict(color="#FFFFFF", width=2)),
                        hovertemplate=f"{strat}, %{{y}}: %{{x:.1f}}%<extra></extra>"))
                fig.update_layout(xaxis_title="% of the true best revenue (1M rows)",
                                  margin=dict(t=40),
                                  yaxis=dict(ticksuffix="  ", categoryorder="array",
                                             categoryarray=["S-curve", "Exponential",
                                                            "Same as assumed"]))
                show(fig, 300)
            with c2:
                fig = go.Figure()
                for lbl, col in SHAPE_COLORS.items():
                    d = h[h.shape_lbl == lbl]
                    fig.add_trace(go.Scatter(
                        x=d.rows, y=d.share_error_pp_mean, name=lbl, mode="lines+markers",
                        line=dict(color=col, width=2), marker=dict(size=8),
                        hovertemplate=f"{lbl}, %{{x:,}} rows: %{{y:.2f}} pp<extra></extra>"))
                fig.update_xaxes(**ROW_TICKS)
                fig.update_layout(xaxis_type="log", xaxis_title="Rows of data (log scale)",
                                  yaxis_title="Average share error (pp)",
                                  yaxis_rangemode="tozero", margin=dict(t=40))
                show(fig, 300)
            s_best = h1m.loc["S-curve", "optimizer_pct_mean"]
            st.markdown(
                "- **Exponential curve:** the optimizer stays at 99.6%+ of the best for all three "
                "brands.\n"
                f"- **S-curve:** {brand} gets {s_best:.1f}% of the best. When small budgets barely "
                "work, the true best plan **concentrates** money on fewer platforms, while the "
                "assumed curve always favours spreading. The gap is largest for Ndure (about "
                "84%, where the true best is 78% TikTok and 22% Google), and more data does "
                "not close it. It still beats the equal and last-year splits by a wide margin.\n"
                "- **Lesson:** more data cannot fix a wrong model. Fitting several curve shapes "
                "and picking the best fit is the natural next step.")
            with st.expander("Hard mode table"):
                st.dataframe(h[["shape_lbl", "rows", "optimizer_pct_mean", "optimizer_pct_min",
                                "lastyear_pct", "equal_pct", "share_error_pp_mean",
                                "share_error_pp_std"]].rename(columns={
                    "shape_lbl": "True curve shape", "rows": "Rows",
                    "optimizer_pct_mean": "Optimizer (% of best)",
                    "optimizer_pct_min": "Worst run (%)",
                    "lastyear_pct": "Last year's split (%)", "equal_pct": "Equal split (%)",
                    "share_error_pp_mean": "Share error (pp)",
                    "share_error_pp_std": "Error spread (pp)"}).style.format(
                    {"Rows": "{:,}", "Optimizer (% of best)": "{:.2f}%",
                     "Worst run (%)": "{:.2f}%", "Last year's split (%)": "{:.1f}%",
                     "Equal split (%)": "{:.1f}%", "Share error (pp)": "{:.2f}",
                     "Error spread (pp)": "±{:.2f}"}), hide_index=True)

    # ---- 3. bootstrap honesty ----
    with card("val3"):
        card_head("3. Are the uncertainty ranges honest?",
                  "On 30 fresh datasets per brand, how often did the true best share fall "
                  "inside the 90% bootstrap range? Target: about 90%.")
        if cov is None:
            st.info("Run src/optimizer/bootstrap_check.py to create these results.")
        else:
            c = cov.copy()
            c["Bootstrap resamples"] = c.n_boot
            piv = c.pivot(index="brand", columns="n_boot", values="percentile_coverage")
            piv = piv.loc[[b for b in G.BRANDS if b in piv.index]]
            piv.columns = [f"{n} resamples" for n in piv.columns]
            st.dataframe(piv.style.format("{:.1f}%"))
            st.caption("Coverage close to 90% means the ranges are honest. They only cover "
                       "noise from limited data, not a wrong curve shape.")
    st.warning("**Still a simulation:** spend here is random and there is no seasonality in the "
               "optimizer. Real data has spend that follows demand, so real accuracy would be lower.")


# =====================================================================
# PAGE 5: BIG DATA BENCHMARK
# =====================================================================
def page_bigdata():
    page_head("Dashboard / Big Data", "Pandas vs Hadoop MapReduce vs Spark",
              "Same job on every engine: read the CSV, group by platform and campaign, and sum "
              "5 metrics. Google Colab free tier (1 machine, 2 cores, 12 GB RAM).",
              [("Benchmark", "")])
    b, big = read_csv("benchmark_results.csv"), read_csv("benchmark_100M.csv")
    if big is not None:
        with card("big"):
            card_head("Stress test: 100M rows (8 GB file)",
                      "The 10M file replicated 10× (tests scale, not new information). 1 run each.")
            items = []
            for _, r in big.iterrows():
                if r["status"] == "OK":
                    items.append((r["engine"], f"{r['seconds']:.0f} s",
                                  "correct" if r["correct"] else "wrong totals",
                                  "good" if r["correct"] else "bad", "read and aggregate"))
                else:
                    items.append((r["engine"], "Crashed", "out of memory", "bad",
                                  f"{big.memory_cap_gb.iloc[0]} GB memory cap"))
            kpi_cards(items)
    if b is not None:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            with card("bench_time"):
                card_head("Time to read and aggregate", "10k to 10M rows, median of 3 runs")
                fig = go.Figure()
                for eng, col in ENGINE_COLORS.items():
                    d = b[b.engine == eng]
                    fig.add_trace(go.Scatter(x=d.rows, y=d.median_s, name=eng,
                                             mode="lines+markers", line=dict(color=col, width=2),
                                             marker=dict(size=8),
                                             hovertemplate=f"{eng}, %{{x:,}} rows: %{{y:.2f}} s"
                                                           f"<extra></extra>"))
                fig.update_xaxes(**ROW_TICKS)
                fig.update_yaxes(dtick=1)
                fig.update_layout(xaxis_type="log", yaxis_type="log",
                                  xaxis_title="Rows (log scale)",
                                  yaxis_title="Seconds (log scale)", margin=dict(t=40))
                show(fig, 340)
        with c2:
            with card("bench_thru"):
                card_head("Throughput", "Rows processed per second")
                b2 = b.copy()
                b2["rows_lbl"] = b2.rows.map(lambda r: f"{r:,}")
                fig = go.Figure()
                for eng, col in ENGINE_COLORS.items():
                    d = b2[b2.engine == eng]
                    fig.add_trace(go.Bar(x=d.rows_lbl, y=d.rows_per_s, name=eng, marker_color=col,
                                         hovertemplate=f"{eng}, %{{x}} rows: %{{y:,.0f}} rows/s"
                                                       f"<extra></extra>"))
                fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08,
                                  xaxis_title="Rows", yaxis_title="Rows per second",
                                  margin=dict(t=40))
                show(fig, 340)
        with card("bench_table"):
            card_head("Median time per engine")
            piv = b.pivot(index="rows", columns="engine", values="median_s")
            piv.index = piv.index.map(lambda r: f"{r:,} rows")
            st.dataframe(piv.style.format("{:.2f} s"))
    with card("bench_take"):
        card_head("Key takeaways")
        st.markdown(
            "- **On one machine, Pandas is fastest up to 10M rows.** Hadoop pays about 4.5 s and "
            "Spark about 1 s of start-up per job, and on 2 cores neither catches up per row.\n"
            "- **At 100M rows (8 GB), plain Pandas ran out of memory**; Spark and Hadoop finished "
            "with correct results.\n"
            "- **Chunked Pandas was still fastest (83 s vs Spark 137 s vs Hadoop 213 s).** The real "
            "value of Spark and Hadoop is spreading work over **many machines** and surviving "
            "failures, which a single free Colab machine can't show.\n"
            "- **Decision rule:** Pandas while data fits in memory, chunked processing when it "
            "doesn't, and Spark when a cluster is needed.")
        st.caption("Limitations: one 2-core machine (no real cluster); the 100M file is replicated; "
                   "a simple group-by job; Spark JVM start-up excluded; Colab speed varies. The "
                   "benchmark was run before the brand column was added. The job reads the same "
                   "columns in the same positions, so the timings still apply.")


# =====================================================================
# PAGE 6: ABOUT
# =====================================================================
def page_about():
    page_head("Dashboard / About", "Method, assumptions and limitations",
              "How the recommendation is built, what is real and what is assumed.", [SIM_TAG])
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        with card("method"):
            card_head("Method")
            st.markdown(
                "1. **Simulate** campaign data with the brief's schema (date, campaign, platform, "
                "impressions, clicks, spend, conversions, revenue, age, gender, city, device) "
                "plus a **brand** column for Borjan, Servis and Ndure.\n"
                "2. **Link Project 1:** each brand's real customer sentiment adjusts its "
                "conversion rate.\n"
                "3. **KPIs** from sums: CTR, CPC, CVR, CPA, ROAS.\n"
                "4. **Fit** a diminishing-returns curve per brand and platform: "
                "revenue(s) = a·s / (1 + s/h).\n"
                "5. **Optimise** the split (SLSQP) to maximise expected revenue under the budget "
                "and min/max share limits.\n"
                "6. **Validate** against the known true optimum, in **hard mode** with two other "
                "curve shapes, and check that the **bootstrap** ranges are honest.\n"
                "7. **Benchmark** Pandas vs Hadoop MapReduce vs Spark from 10k to 100M rows.")
    with c2:
        with card("real"):
            card_head("What is real and what is assumed")
            st.markdown(
                "- **Real:** brand sentiment from Project 1 (XLM-R predictions on 881 YouTube "
                "comments and Google Maps reviews), the KPI formulas, the optimizer, and the "
                "benchmark timings.\n"
                "- **Assumed:** all ad prices, click and conversion rates, each brand's order "
                "value and platform fit, the margin, and the size of the sentiment effect "
                "(+10 points of net sentiment = +5% conversion rate).\n"
                "- **Simulated:** every ad record. These are not the brands' real ad results.")
            sent = pd.DataFrame([{"brand": b, "positive": G.SENTIMENT[b]["positive"],
                                  "negative": G.SENTIMENT[b]["negative"],
                                  "reviews": G.SENTIMENT[b]["reviews"],
                                  "conversion effect": G.sentiment_mult(b) - 1}
                                 for b in G.BRANDS])
            st.dataframe(sent.style.format({"positive": "{:.0%}", "negative": "{:.0%}",
                                            "conversion effect": "{:+.1%}"}), hide_index=True)
    with card("assump"):
        card_head("Simulation assumptions (PKR)", "Platform settings shared by all brands, then "
                  "each brand's positioning")
        a = pd.DataFrame(G.PLATFORMS).T.reset_index().rename(columns={"index": "platform"})
        a["row_share"] = G.PLATFORM_SHARE
        st.dataframe(a, hide_index=True)
        bp = pd.DataFrame([{"brand": b, "order value ×": G.BRAND_PROFILE[b]["aov"],
                            **{f"{p} fit": G.BRAND_PROFILE[b]["aff"][p] for p in G.PLATFORMS}}
                           for b in G.BRANDS])
        st.dataframe(bp, hide_index=True)
        st.caption("cpm is the cost per 1,000 impressions; ctr and cvr are base click and "
                   "conversion rates; aov is the average order value; half_sat is the spend per "
                   "slice where efficiency halves. Brand 'fit' multiplies the click-through rate.")
    with card("limits"):
        card_head("Limitations")
        st.markdown(
            "- **Simulated ad data:** results reflect the assumptions, not these brands' real "
            "ad accounts or real Pakistani ad prices.\n"
            "- **Weak sentiment input:** the Project 1 model is only moderately accurate "
            "(XLM-R accuracy 0.55), and Servis's sentiment comes from YouTube comments only.\n"
            "- **Curve shape:** with an S-curve the optimizer loses up to about 15% of the best "
            "revenue (Ndure), and more data does not fix it.\n"
            "- **Uncertainty ranges** only cover noise from limited data.\n"
            "- **No confounding:** simulated spend is random; real brands spend more when demand "
            "is already high, which makes ads look more effective.\n"
            "- **Revenue only:** brand awareness (YouTube's main job) isn't measured. Use the "
            "minimum-share setting to keep a presence.\n"
            "- **No time dynamics:** no ad fatigue, carry-over or seasonality in the optimizer.\n"
            "- **Scale assumption:** absolute revenue depends on the slices setting; comparisons "
            "between strategies are more reliable than the absolute numbers.")
        st.markdown(f"**Links:** [GitHub repo]({REPO_URL}), "
                    f"[Project 1: sentiment analysis]({P1_URL})")


# ---------------- NAVIGATION ----------------
pages = [
    st.Page(page_overview, title="Overview", icon=":material/space_dashboard:",
            url_path="overview", default=True),
    st.Page(page_marketing, title="Marketing plan", icon=":material/campaign:",
            url_path="marketing-plan"),
    st.Page(page_adcopy, title="Ad copy studio", icon=":material/edit_note:",
            url_path="ad-copy"),
    st.Page(page_plan, title="Plan & scenarios", icon=":material/tune:", url_path="plan"),
    st.Page(page_performance, title="Performance", icon=":material/insights:",
            url_path="performance"),
    st.Page(page_validation, title="Validation", icon=":material/verified:",
            url_path="validation"),
    st.Page(page_bigdata, title="Big Data benchmark", icon=":material/storage:",
            url_path="big-data"),
    st.Page(page_about, title="About & limitations", icon=":material/info:", url_path="about"),
]
st.navigation(pages).run()
