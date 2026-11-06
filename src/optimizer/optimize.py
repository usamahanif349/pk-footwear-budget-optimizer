"""
Budget optimizer: learns a diminishing-returns curve per platform from the
(simulated) data, then splits the budget to maximise expected revenue.

Response curve per ad slice (one ad set for one day):
    revenue(s) = a * s / (1 + s / h)
    a = ROAS at very small spend,  h = spend where efficiency halves

Each brand (Borjan, Servis, Ndure) gets its own curves and its own budget split.

Usage (Command Prompt):  python src\\optimizer\\optimize.py --file ads_30000.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, minimize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"


def response(s, a, h):
    return a * s / (1 + s / h)


def marginal_roas(s, a, h):
    return a / (1 + s / h) ** 2


def fit_curves(df):
    params = {}
    for plat, g in df.groupby("platform", observed=True):
        s = g["spend"].to_numpy(float)
        r = g["revenue"].to_numpy(float)
        p0 = [2 * r.sum() / s.sum(), float(np.median(s))]
        (a, h), cov = curve_fit(response, s, r, p0=p0,
                                bounds=([0, 1], [np.inf, np.inf]), maxfev=20000)
        a_se, h_se = np.sqrt(np.diag(cov))
        params[str(plat)] = dict(a=float(a), h=float(h),
                                 a_se=float(a_se), h_se=float(h_se), rows=len(g))
    return params


def evaluate(alloc, params, n_slices, margin):
    rows = []
    for plat, x in alloc.items():
        p = params[plat]
        s = x / n_slices
        rev = n_slices * response(s, p["a"], p["h"])
        rows.append(dict(platform=plat, spend=x, revenue=rev,
                         ROAS=rev / x if x > 0 else np.nan,
                         marginal_ROAS=marginal_roas(s, p["a"], p["h"])))
    t = pd.DataFrame(rows)
    t["share_%"] = t["spend"] / t["spend"].sum() * 100
    t["profit"] = margin * t["revenue"] - t["spend"]
    return t


def optimize(params, budget, n_slices, min_share=0.0, max_share=1.0):
    plats = list(params)
    k = len(plats)

    def neg_revenue(w):
        x = w * budget
        return -sum(n_slices * response(x[i] / n_slices, params[pl]["a"], params[pl]["h"])
                    for i, pl in enumerate(plats)) / budget

    res = minimize(neg_revenue, np.full(k, 1 / k), method="SLSQP",
                   bounds=[(min_share, max_share)] * k,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    w = np.clip(res.x, 0, None)
    w = w / w.sum()
    return {pl: float(w[i] * budget) for i, pl in enumerate(plats)}


def plan_for_brand(df, budget, n_slices, margin, min_share=0.0):
    """Fit curves for one brand's data and compare the optimizer with simple splits."""
    params = fit_curves(df)
    plats = list(params)
    hist = df.groupby("platform", observed=True)["spend"].sum()
    hist = (hist / hist.sum()).to_dict()
    best = max(params, key=lambda pl: df.loc[df.platform == pl, "revenue"].sum()
               / df.loc[df.platform == pl, "spend"].sum())
    strategies = {
        "Optimizer": optimize(params, budget, n_slices, min_share),
        "Last year's split": {pl: budget * hist[pl] for pl in plats},
        "Equal split": {pl: budget / len(plats) for pl in plats},
        f"All on best avg ROAS ({best})": {pl: (budget if pl == best else 0.0) for pl in plats},
    }
    rec = evaluate(strategies["Optimizer"], params, n_slices, margin)
    summary = []
    for name, alloc in strategies.items():
        t = evaluate(alloc, params, n_slices, margin)
        summary.append(dict(strategy=name, revenue=t.revenue.sum(),
                            ROAS=t.revenue.sum() / budget, profit=t.profit.sum()))
    summary = pd.DataFrame(summary)
    base = summary.loc[summary.strategy == "Equal split", "revenue"].iloc[0]
    summary["vs_equal_%"] = (summary.revenue / base - 1) * 100
    return params, rec, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="ads_30000.csv")
    ap.add_argument("--budget", type=float, default=1_000_000)
    ap.add_argument("--slices", type=int, default=60,
                    help="ad slices per platform in the period (30 days x 2 ad sets)")
    ap.add_argument("--margin", type=float, default=0.5,
                    help="gross margin on shoes (ASSUMPTION)")
    ap.add_argument("--min_share", type=float, default=0.0)
    args = ap.parse_args()

    df = pd.read_csv(RAW / args.file)
    B, N, m = args.budget, args.slices, args.margin
    pd.set_option("display.width", 160)
    all_params, recs, sums = {}, [], []
    for brand, g in df.groupby("brand", sort=False):
        params, rec, summary = plan_for_brand(g, B, N, m, args.min_share)
        all_params[brand] = params
        print(f"\n=============== {brand} ===============")
        print("Fitted curves (a = ROAS at tiny spend, h = half-saturation spend):")
        for pl, p in params.items():
            print(f"  {pl:10s} a={p['a']:.2f} (+/-{p['a_se']:.2f})   "
                  f"h={p['h']:,.0f} (+/-{p['h_se']:,.0f})")
        print(f"\nRECOMMENDED SPLIT of Rs. {B:,.0f} (margin {m:.0%}):")
        print(rec.round({"spend": 0, "revenue": 0, "ROAS": 2, "marginal_ROAS": 2,
                         "share_%": 1, "profit": 0}).to_string(index=False))
        print("\nSTRATEGY COMPARISON:")
        print(summary.round(2).to_string(index=False))
        recs.append(rec.assign(brand=brand))
        sums.append(summary.assign(brand=brand))

    OUT.mkdir(parents=True, exist_ok=True)
    pd.concat(recs).to_csv(OUT / "recommendation.csv", index=False)
    pd.concat(sums).to_csv(OUT / "strategy_comparison.csv", index=False)
    with open(OUT / "response_curves.json", "w") as f:
        json.dump(dict(params=all_params, budget=B, slices=N, margin=m), f, indent=2)
    print(f"\nSaved results -> {OUT}")


if __name__ == "__main__":
    main()
