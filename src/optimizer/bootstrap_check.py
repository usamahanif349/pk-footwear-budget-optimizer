"""
Are the bootstrap 90% ranges honest?

A 90% range should contain the TRUE best share about 90% of the time.
One dataset cannot tell us that (the "2 of 5 outside" result could be luck),
so we regenerate the data many times, build the bootstrap range each time,
and count how often the true share falls inside.

Two ways to build the range from the same bootstrap results:
  percentile : 5th to 95th percentile of the bootstrap shares (current dashboard)
  basic      : mirror the percentiles around the estimate
               (corrects for a fit that is pushed one way)

Usage (Command Prompt):  python src\\optimizer\\bootstrap_check.py
(takes a few minutes)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "simulation"))
sys.path.insert(0, str(ROOT / "src" / "optimizer"))
import generate_data as G  # noqa: E402
from optimize import fit_curves, optimize  # noqa: E402
from validate import true_params, BUDGET, SLICES  # noqa: E402

OUT = ROOT / "data" / "processed"
ROWS = 10_000
DATASETS = 30          # independent simulated datasets
N_BOOT = 200           # bootstrap resamples per dataset


def shares(params):
    alloc = optimize(params, BUDGET, SLICES)
    return {pl: alloc[pl] / BUDGET * 100 for pl in params}


def main():
    truth = true_params()
    plats = list(truth)
    true_share = shares(truth)
    print("True best shares: " + ", ".join(f"{p} {true_share[p]:.1f}%" for p in plats))

    rows = []
    for seed in range(1, DATASETS + 1):
        df = G.generate(ROWS, 1000 + seed)
        est = shares(fit_curves(df))
        rng = np.random.default_rng(seed)
        boot = []
        for _ in range(N_BOOT):
            idx = rng.integers(0, len(df), len(df))
            try:
                boot.append(shares(fit_curves(df.iloc[idx])))
            except RuntimeError:
                pass
        boot = pd.DataFrame(boot)
        for n_boot in (50, N_BOOT):
            b = boot.iloc[:n_boot]
            lo, hi = b.quantile(0.05), b.quantile(0.95)
            for p in plats:
                t = true_share[p]
                basic_lo = max(0.0, 2 * est[p] - hi[p])
                basic_hi = min(100.0, 2 * est[p] - lo[p])
                rows.append(dict(
                    seed=seed, n_boot=n_boot, platform=p, true=t, estimate=est[p],
                    pct_lo=lo[p], pct_hi=hi[p], basic_lo=basic_lo, basic_hi=basic_hi,
                    pct_covered=lo[p] - 1e-6 <= t <= hi[p] + 1e-6,
                    basic_covered=basic_lo - 1e-6 <= t <= basic_hi + 1e-6,
                    pct_width=hi[p] - lo[p], basic_width=basic_hi - basic_lo,
                ))
        print(f"  dataset {seed:2d}/{DATASETS} done")

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "bootstrap_coverage_runs.csv", index=False)

    summary = res.groupby(["n_boot", "platform"]).agg(
        true_share=("true", "first"),
        mean_estimate=("estimate", "mean"),
        percentile_coverage=("pct_covered", "mean"),
        basic_coverage=("basic_covered", "mean"),
        percentile_width=("pct_width", "mean"),
        basic_width=("basic_width", "mean"),
    )
    overall = res.groupby("n_boot").agg(
        percentile_coverage=("pct_covered", "mean"),
        basic_coverage=("basic_covered", "mean"),
        percentile_width=("pct_width", "mean"),
        basic_width=("basic_width", "mean"),
    )
    summary[["percentile_coverage", "basic_coverage"]] *= 100
    overall[["percentile_coverage", "basic_coverage"]] *= 100
    print("\nCOVERAGE BY PLATFORM (target: 90%):")
    print(summary.round(1).to_string())
    print("\nOVERALL (target: 90%):")
    print(overall.round(1).to_string())
    summary.round(3).to_csv(OUT / "bootstrap_coverage_summary.csv")
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    main()
