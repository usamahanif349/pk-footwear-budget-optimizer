"""
HARD MODE self-check: what if the real curve has a DIFFERENT shape?

The optimizer always assumes   revenue(s) = a * s / (1 + s / h).
The normal validation (validate.py) generates data with that same shape,
so it is a best case. Here the data comes from two other shapes:

  exponential : efficiency = (1 - e^-x) / x   (saturates faster, hard ceiling)
  s_curve     : efficiency = 2x / (1 + x^2)   (small budgets barely work)

with x = spend / h. The optimizer still fits its usual curve, and we score
its split against the TRUE best split of the TRUE curve.

Usage (Command Prompt):  python src\\optimizer\\hard_mode.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "simulation"))
sys.path.insert(0, str(ROOT / "src" / "optimizer"))
import generate_data as G  # noqa: E402
from optimize import fit_curves, optimize  # noqa: E402
from validate import true_params, BUDGET, SLICES  # noqa: E402

OUT = ROOT / "data" / "processed"
SIZES = [10_000, 100_000, 1_000_000]
SEEDS = [1, 2, 3, 4, 5]


def true_revenue(alloc, truth, shape):
    """Expected revenue of a split under the TRUE curve of this shape."""
    total = 0.0
    for pl, x in alloc.items():
        s = x / SLICES
        if s <= 0:
            continue
        a, h = truth[pl]["a"], truth[pl]["h"]
        total += SLICES * a * s * float(G.efficiency(s, h, shape))
    return total


def true_best(truth, shape):
    """Best split of the TRUE curve. The S-curve can have several local
    optima, so we try many starting points and keep the best."""
    plats = list(truth)
    k = len(plats)

    def neg(w):
        return -true_revenue({pl: w[i] * BUDGET for i, pl in enumerate(plats)},
                             truth, shape) / BUDGET

    rng = np.random.default_rng(0)
    starts = [np.full(k, 1 / k)] + list(np.eye(k)) + list(rng.dirichlet(np.ones(k), 40))
    best_w, best_val = None, np.inf
    for w0 in starts:
        res = minimize(neg, w0, method="SLSQP", bounds=[(0, 1)] * k,
                       constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
        if res.fun < best_val:
            best_w, best_val = res.x, res.fun
    w = np.clip(best_w, 0, None)
    w = w / w.sum()
    return {pl: float(w[i] * BUDGET) for i, pl in enumerate(plats)}


def main():
    truth = true_params()
    plats = list(truth)
    runs, optima = [], []

    for shape in G.SHAPES:
        best = true_best(truth, shape)
        best_rev = true_revenue(best, truth, shape)
        equal_rev = true_revenue({pl: BUDGET / len(plats) for pl in plats}, truth, shape)
        print(f"\n=== TRUE shape: {shape} ===")
        print("  True best split: " + ", ".join(
            f"{pl} {best[pl] / BUDGET * 100:.1f}%" for pl in plats))
        print(f"  Equal split gets {equal_rev / best_rev * 100:.1f}% of the true best")
        for pl in plats:
            optima.append(dict(shape=shape, platform=pl,
                               true_best_share_pct=best[pl] / BUDGET * 100))

        for n in SIZES:
            for seed in SEEDS:
                df = G.generate(n, seed, shape)
                alloc = optimize(fit_curves(df), BUDGET, SLICES)
                hist = df.groupby("platform", observed=True)["spend"].sum()
                hist_alloc = {str(pl): BUDGET * v / hist.sum() for pl, v in hist.items()}
                runs.append(dict(
                    shape=shape, rows=n, seed=seed,
                    optimizer_pct_of_best=true_revenue(alloc, truth, shape) / best_rev * 100,
                    lastyear_pct_of_best=true_revenue(hist_alloc, truth, shape) / best_rev * 100,
                    equal_pct_of_best=equal_rev / best_rev * 100,
                    avg_share_error_pp=np.mean(
                        [abs(alloc[pl] - best[pl]) / BUDGET * 100 for pl in plats]),
                    **{f"share_{pl}": alloc[pl] / BUDGET * 100 for pl in plats},
                ))
                r = runs[-1]
                print(f"  rows={n:>9,} seed={seed}  optimizer {r['optimizer_pct_of_best']:6.2f}% "
                      f"of best   share error {r['avg_share_error_pp']:5.2f} pp")

    runs = pd.DataFrame(runs)
    summary = runs.groupby(["shape", "rows"]).agg(
        optimizer_pct_mean=("optimizer_pct_of_best", "mean"),
        optimizer_pct_min=("optimizer_pct_of_best", "min"),
        lastyear_pct=("lastyear_pct_of_best", "mean"),
        equal_pct=("equal_pct_of_best", "mean"),
        share_error_pp_mean=("avg_share_error_pp", "mean"),
        share_error_pp_std=("avg_share_error_pp", "std"),
    ).round(3)
    summary = summary.reindex(G.SHAPES, level="shape")
    print("\nHARD MODE SUMMARY (% of the TRUE best revenue; lower error = better):")
    print(summary.to_string())

    OUT.mkdir(parents=True, exist_ok=True)
    runs.to_csv(OUT / "hard_mode_runs.csv", index=False)
    summary.to_csv(OUT / "hard_mode_summary.csv")
    pd.DataFrame(optima).to_csv(OUT / "hard_mode_true_optima.csv", index=False)
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()
