"""
Compute marketing KPIs from the simulated ad data.
KPIs are computed from SUMS (total clicks / total impressions etc.),
not by averaging row-level ratios, which would be wrong.

Usage (Command Prompt):  python src\\analysis\\kpis.py --file ads_10000.csv
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

SUM_COLS = ["impressions", "clicks", "spend", "conversions", "revenue"]


def kpi_table(df, by):
    t = df.groupby(by, observed=True)[SUM_COLS].sum()
    t["CTR_%"] = (t["clicks"] / t["impressions"] * 100).round(2)
    t["CPC"] = (t["spend"] / t["clicks"]).round(1)
    t["CVR_%"] = (t["conversions"] / t["clicks"] * 100).round(2)
    t["CPA"] = (t["spend"] / t["conversions"]).round(0)
    t["ROAS"] = (t["revenue"] / t["spend"]).round(2)
    t["profit_proxy"] = t["revenue"] - t["spend"]
    return t.reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="ads_10000.csv")
    args = ap.parse_args()

    df = pd.read_csv(RAW / args.file, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    OUT.mkdir(parents=True, exist_ok=True)

    tables = {
        "kpi_platform": ["platform"],
        "kpi_campaign": ["campaign"],
        "kpi_platform_campaign": ["platform", "campaign"],
        "kpi_platform_age": ["platform", "age"],
        "kpi_platform_gender": ["platform", "gender"],
        "kpi_platform_city": ["platform", "city"],
        "kpi_platform_device": ["platform", "device"],
        "kpi_monthly": ["month", "platform"],
    }
    for name, by in tables.items():
        kpi_table(df, by).to_csv(OUT / f"{name}.csv", index=False)

    pd.set_option("display.width", 160)
    print(kpi_table(df, ["platform"]).to_string(index=False))
    print(f"\nSaved {len(tables)} KPI tables -> {OUT}")


if __name__ == "__main__":
    main()