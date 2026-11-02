"""
Self-check: does the optimizer recover the TRUE best budget split?

Because the data is simulated, we know the generator's hidden settings,
so we can compute the true expected response curve for every platform
(exact expected value of the generator, ignoring tiny clipping effects).
Then we regenerate data at several sizes and seeds, run the optimizer on
each, and score its split against the true optimum.

Usage (Command Prompt):  python src\\optimizer\\validate.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "simulation"))
sys.path.insert(0, str(ROOT / "src" / "optimizer"))
import generate_data as G  # noqa: E402
from optimize import fit_curves, optimize, evaluate  # noqa: E402

OUT = ROOT / "data" / "processed"
BUDGET, SLICES, MARGIN = 1_000_000, 60, 0.5
SIZES = [10_000, 100_000, 1_000_000]
SEEDS = [1, 2, 3, 4, 5]

# mean of the lognormal noise terms used in the generator (imp, ctr, cvr, revenue)
LN_BOOST = np.exp((0.15**2 + 0.20**2 + 0.25**2 + 0.10**2) / 2)


def true_params():
    camp_ctr = np.array([c["ctr"] for c in G.CAMPAIGNS.values()])
    camp_cvr = np.array([c["cvr"] for c in G.CAMPAIGNS.values()])
    e_camp = np.sum(np.array(G.CAMPAIGN_SHARE) * camp_ctr * camp_cvr)
    e_dev = np.dot(G.DEVICE_SHARE, G.DEVICE_CVR_MULT)
    e_city = np.dot(G.CITY_SHARE, G.CITY_AOV_MULT)
    params = {}
    for pl, p in G.PLATFORMS.items():
        e_age = np.dot(G.AGE_SHARE, G.AGE_MULT[pl])
        e_gen = np.dot(G.GENDER_SHARE, G.GENDER_MULT[pl])
        a = (1000 / p["cpm"] * p["ctr"] * p["cvr"] * p["aov"]
             * e_camp * e_age * e_gen * e_dev * e_city * LN_BOOST)
        params[pl] = dict(a=float(a), h=float(p["half_sat"]))
    return params


def true_revenue(alloc, truth):
    return evaluate(alloc, truth, SLICES, MARGIN)["revenue"].sum()


def main():
    truth = true_params()
    plats = list(truth)
    best = optimize(truth, BUDGET, SLICES)
    best_rev = true_revenue(best, truth)
    equal_rev = true_revenue({pl: BUDGET / len(plats) for pl in plats}, truth)

    print("TRUE curves and TRUE best split:")
    for pl in plats:
        print(f"  {pl:10s} a={truth[pl]['a']:.2f}  h={truth[pl]['h']:,.0f}  "
              f"best share={best[pl] / BUDGET * 100:5.1f}%")
    print(f"  True best revenue: Rs. {best_rev:,.0f}   "
          f"(equal split gets {equal_rev / best_rev * 100:.1f}% of it)\n")

    runs = []
    for n in SIZES:
        for seed in SEEDS:
            df = G.generate(n, seed)
            alloc = optimize(fit_curves(df), BUDGET, SLICES)
            hist = df.groupby("platform", observed=True)["spend"].sum()
            hist_alloc = {str(pl): BUDGET * v / hist.sum() for pl, v in hist.items()}
            share_err = np.mean([abs(alloc[pl] - best[pl]) / BUDGET * 100 for pl in plats])
            runs.append(dict(
                rows=n, seed=seed,
                optimizer_pct_of_best=true_revenue(alloc, truth) / best_rev * 100,
                lastyear_pct_of_best=true_revenue(hist_alloc, truth) / best_rev * 100,
                equal_pct_of_best=equal_rev / best_rev * 100,
                avg_share_error_pp=share_err,
                **{f"share_{pl}": alloc[pl] / BUDGET * 100 for pl in plats},
            ))
            print(f"  rows={n:>9,}  seed={seed}  "
                  f"optimizer gets {runs[-1]['optimizer_pct_of_best']:.2f}% of best  "
                  f"share error {share_err:.2f} pp")

    runs = pd.DataFrame(runs)
    summary = runs.groupby("rows").agg(
        optimizer_pct_mean=("optimizer_pct_of_best", "mean"),
        optimizer_pct_std=("optimizer_pct_of_best", "std"),
        lastyear_pct=("lastyear_pct_of_best", "mean"),
        equal_pct=("equal_pct_of_best", "mean"),
        share_error_pp_mean=("avg_share_error_pp", "mean"),
        share_error_pp_std=("avg_share_error_pp", "std"),
    ).round(3)
    print("\nSUMMARY (higher % = closer to the true best; lower error = better):")
    print(summary.to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    runs.to_csv(OUT / "validation_runs.csv", index=False)
    summary.to_csv(OUT / "validation_summary.csv")
    pd.DataFrame([{"platform": pl, "true_a": truth[pl]["a"], "true_h": truth[pl]["h"],
                   "true_best_share_%": best[pl] / BUDGET * 100} for pl in plats]
                 ).to_csv(OUT / "true_optimum.csv", index=False)
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()