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
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
for sub in ["optimizer", "analysis", "simulation"]:
    sys.path.insert(0, str(ROOT / "src" / sub))
from optimize import fit_curves, optimize, evaluate, response  # noqa: E402
from kpis import kpi_table  # noqa: E402
import generate_data as G  # noqa: E402

BRAND = "StepUp Footwear (fictional)"
DATA_FILE = ROOT / "data" / "raw" / "ads_10000.csv"
PROC = ROOT / "data" / "processed"
COLORS = {"Facebook": "#1877F2", "Instagram": "#E1306C", "Google": "#34A853",
          "TikTok": "#00BFB3", "YouTube": "#FF0000"}

st.set_page_config(page_title="Ad Budget Optimizer", page_icon="👟", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def get_curves():
    return fit_curves(load_data())


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


def rs(x):
    return f"Rs. {x:,.0f}"


df = load_data()
curves = get_curves()
all_plats = list(curves)

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Budget settings")
budget = st.sidebar.number_input("Monthly ad budget (Rs.)", 100_000, 50_000_000,
                                 1_000_000, step=100_000)
margin = st.sidebar.slider("Gross margin on shoes", 0.20, 0.80, 0.50, 0.05,
                           help="Share of revenue left after product cost. ASSUMPTION.")
slices = st.sidebar.slider("Ad slices per platform (days × ad sets)", 15, 180, 60, 15,
                           help="Default 60 = 30 days × 2 ad sets. Sets the scale. ASSUMPTION.")
platforms = st.sidebar.multiselect("Platforms allowed", all_plats, default=all_plats)
min_share = st.sidebar.slider("Minimum share per allowed platform (%)", 0, 20, 0) / 100
max_share = st.sidebar.slider("Maximum share per platform (%)", 20, 100, 100) / 100

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

# ---------------- HEADER ----------------
st.title("👟 Digital Ad Budget Optimizer")
st.caption(f"{BRAND} · Facebook · Instagram · Google · TikTok · YouTube")
st.warning("⚠️ All data is **simulated** for a fictional brand, using stated assumptions "
           "(see the About tab). It shows the method, not real Pakistani ad prices.")

tabs = st.tabs(["🎯 Recommendation", "📈 Response curves", "🔍 KPI explorer",
                "✅ Validation", "ℹ️ About & limitations"])

# ---------------- TAB 1 ----------------
with tabs[0]:
    tot_rev, tot_profit = rec.revenue.sum(), rec.profit.sum()
    opt_gain = comp.loc[comp.strategy == "Optimizer", "vs_equal_%"].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected revenue", rs(tot_rev))
    c2.metric("Expected ROAS", f"{tot_rev / budget:.2f}")
    c3.metric("Expected profit", rs(tot_profit),
              help="margin × revenue − ad spend")
    c4.metric("Gain vs equal split", f"{opt_gain:+.1f}%")

    left, right = st.columns(2)
    with left:
        st.subheader(f"Where to spend {rs(budget)}")
        fig = px.pie(rec[rec.spend > 1], names="platform", values="spend", hole=0.55,
                     color="platform", color_discrete_map=COLORS)
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig)
    with right:
        st.subheader("Optimizer vs simple strategies")
        fig = px.bar(comp, x="strategy", y="revenue", color="strategy",
                     text=comp["vs_equal_%"].map(lambda v: f"{v:+.1f}% vs equal"))
        fig.update_layout(showlegend=False, yaxis_title="Expected revenue (Rs.)",
                          xaxis_title="")
        st.plotly_chart(fig)

    show = rec[["platform", "share_%", "spend", "revenue", "ROAS",
                "marginal_ROAS", "profit"]]
    st.dataframe(show.style.format({
        "share_%": "{:.1f}%", "spend": "Rs. {:,.0f}", "revenue": "Rs. {:,.0f}",
        "ROAS": "{:.2f}", "marginal_ROAS": "{:.2f}", "profit": "Rs. {:,.0f}"},
        na_rep="–"), hide_index=True)

    breakeven = 1 / margin
    funded = rec[rec.spend > 1]
    lo, hi = funded.marginal_ROAS.min(), funded.marginal_ROAS.max()
    st.info(f"**Why this split?** The last rupee on every funded platform earns about "
            f"Rs. {lo:.2f}–{hi:.2f}. If one platform's last rupee earned more, moving money "
            f"there would raise revenue, so at the best split these values are (near) equal. "
            f"Break-even ROAS at a {margin:.0%} margin is **{breakeven:.2f}**.")
    for p in all_plats:
        if p in platforms and alloc[p] <= 1:
            st.caption(f"• **{p}** gets nothing: even its first rupee earns only "
                       f"Rs. {curves[p]['a']:.2f}, below what the others still earn.")
    if lo < breakeven:
        st.warning("Some of the last rupees **lose money** after product costs: this "
                   "budget is bigger than the profit-maximising level. See 📈 Response curves.")

# ---------------- TAB 2 ----------------
with tabs[1]:
    st.subheader("Diminishing returns per platform")
    st.write("Each line shows expected monthly revenue for a given monthly spend on that "
             "platform. Lines flatten as spend grows. ⭐ = the recommended spend.")
    xs = np.linspace(0, budget, 200)
    fig = go.Figure()
    for p in all_plats:
        c = curves[p]
        fig.add_trace(go.Scatter(x=xs, y=slices * response(xs / slices, c["a"], c["h"]),
                                 name=p, line=dict(color=COLORS[p])))
        if alloc[p] > 1:
            fig.add_trace(go.Scatter(
                x=[alloc[p]], y=[slices * response(alloc[p] / slices, c["a"], c["h"])],
                mode="markers", marker=dict(size=14, color=COLORS[p], symbol="star"),
                showlegend=False, name=f"{p} pick"))
    fig.update_layout(xaxis_title="Monthly spend on platform (Rs.)",
                      yaxis_title="Expected revenue (Rs.)")
    st.plotly_chart(fig)

    fit = pd.DataFrame(curves).T.reset_index().rename(columns={"index": "platform"})
    fit = fit[["platform", "a", "a_se", "h", "h_se", "rows"]]
    st.dataframe(fit.style.format({"a": "{:.2f}", "a_se": "±{:.2f}", "h": "{:,.0f}",
                                   "h_se": "±{:,.0f}"}), hide_index=True)
    st.caption("a = ROAS at very small spend · h = spend per slice where efficiency halves · "
               "± = standard error of the fit.")

    st.subheader("Is this even the right total budget?")
    pc = profit_curve(tuple(platforms), slices, margin, min_share, max_share,
                      float(max(5_000_000, 2 * budget)))
    top = pc.loc[pc.profit.idxmax()]
    fig = px.line(pc, x="budget", y="profit", markers=True)
    fig.add_vline(x=budget, line_dash="dash", annotation_text="your budget")
    fig.add_vline(x=top.budget, line_dash="dot", line_color="green",
                  annotation_text="profit peak")
    fig.update_layout(xaxis_title="Total monthly budget (Rs.)",
                      yaxis_title="Expected profit (Rs.)")
    st.plotly_chart(fig)
    st.write(f"Under these assumptions, profit peaks near **{rs(top.budget)}** "
             f"(about {rs(top.profit)} profit). Beyond that, extra ad spend earns back "
             f"less than it costs.")

# ---------------- TAB 3 ----------------
with tabs[2]:
    st.subheader("KPIs by platform (historical, simulated)")
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
    st.plotly_chart(fig)
    st.caption("Green = better. For CPC and CPA lower is better, so the colours are reversed.")

    st.subheader("Monthly trend")
    m = kpi_table(df, ["month", "platform"])
    fig = px.line(m, x="month", y=metric, color="platform", markers=True,
                  color_discrete_map=COLORS)
    st.plotly_chart(fig)
    st.caption("Peaks match the simulated Eid ul Fitr (Mar), Eid ul Adha (late May–Jun) "
               "and 11.11 (Nov) campaigns.")

# ---------------- TAB 4 ----------------
with tabs[3]:
    st.subheader("Self-check: does the optimizer find the TRUE best split?")
    st.write("Because the data is simulated, the true best split is known. The data was "
             "regenerated 5 times at 10k, 100k and 1M rows, and each optimizer result was "
             "scored against the true optimum.")
    vs_file, tr_file = PROC / "validation_summary.csv", PROC / "true_optimum.csv"
    if vs_file.exists():
        vs = pd.read_csv(vs_file)
        c1, c2 = st.columns(2)
        with c1:
            fig = px.line(vs, x="rows", y="share_error_pp_mean", log_x=True, markers=True,
                          error_y="share_error_pp_std")
            fig.update_layout(xaxis_title="Rows of data (log scale)",
                              yaxis_title="Avg share error (percentage points)",
                              title="More data → more precise split")
            st.plotly_chart(fig)
        with c2:
            long = vs.melt(id_vars="rows",
                           value_vars=["optimizer_pct_mean", "lastyear_pct", "equal_pct"],
                           var_name="strategy", value_name="pct_of_best")
            long["strategy"] = long.strategy.map({"optimizer_pct_mean": "Optimizer",
                                                  "lastyear_pct": "Last year's split",
                                                  "equal_pct": "Equal split"})
            long["rows"] = long.rows.map(lambda r: f"{r:,}")
            fig = px.bar(long, x="rows", y="pct_of_best", color="strategy", barmode="group")
            fig.update_layout(yaxis_range=[90, 100.5], xaxis_title="Rows of data",
                              yaxis_title="% of true best revenue",
                              title="Revenue captured vs the true best")
            st.plotly_chart(fig)
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

# ---------------- TAB 5 ----------------
with tabs[4]:
    st.subheader("Method")
    st.markdown(
        "1. **Simulate** campaign data with the brief's schema (date, campaign, platform, "
        "impressions, clicks, spend, conversions, revenue, age, gender, city, device).\n"
        "2. **KPIs** from sums: CTR, CPC, CVR, CPA, ROAS.\n"
        "3. **Fit** a diminishing-returns curve per platform: "
        "revenue(s) = a·s / (1 + s/h), using non-linear least squares (scipy).\n"
        "4. **Optimise** the split with SLSQP: maximise total expected revenue subject to "
        "the budget and min/max share limits. With a fixed budget, max revenue = max profit.\n"
        "5. **Validate** against the known true optimum at 10k / 100k / 1M rows.")
    st.subheader("Simulation assumptions (PKR)")
    a = pd.DataFrame(G.PLATFORMS).T.reset_index().rename(columns={"index": "platform"})
    a["row_share"] = G.PLATFORM_SHARE
    st.dataframe(a, hide_index=True)
    st.caption("cpm = cost per 1,000 impressions · ctr/cvr = base click & conversion rates · "
               "aov = average order value · half_sat = spend per slice where efficiency halves.")
    st.subheader("Limitations")
    st.markdown(
        "- **Simulated data:** results reflect the assumptions, not real Pakistani ad prices.\n"
        "- **Best-case validation:** the fitted curve shape matches the generator's.\n"
        "- **Revenue only:** brand awareness (YouTube's main job) isn't measured, so YouTube "
        "can look worse than it is. Use the minimum-share slider to keep a presence.\n"
        "- **No time dynamics:** no ad fatigue, carry-over effects, or seasonality in the optimizer.\n"
        "- **Pooled curves:** one curve per platform; segments (age, city…) aren't optimised separately.\n"
        "- **Scale assumption:** absolute revenue depends on the slices setting; comparisons "
        "between strategies are more reliable than the absolute numbers.")