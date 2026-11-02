"""
Simulate digital ad campaign data for a FICTIONAL Pakistani footwear brand.
ALL NUMBERS BELOW ARE ASSUMPTIONS (simulated data), not real company data.

Usage (Command Prompt):  python src\\simulation\\generate_data.py --rows 10000
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------- ASSUMPTIONS (PKR) ----------------
# cpm = cost per 1000 impressions, ctr = click-through rate,
# cvr = conversion rate (click -> order), aov = average order value,
# half_sat = spend at which ad efficiency drops by half (diminishing returns).
PLATFORMS = {
    "Facebook":  dict(cpm=150, ctr=0.012, cvr=0.012, aov=4500, half_sat=8000),
    "Instagram": dict(cpm=180, ctr=0.010, cvr=0.014, aov=4800, half_sat=7000),
    "Google":    dict(cpm=600, ctr=0.030, cvr=0.018, aov=5500, half_sat=3000),
    "TikTok":    dict(cpm=90,  ctr=0.016, cvr=0.005, aov=3800, half_sat=12000),
    "YouTube":   dict(cpm=220, ctr=0.007, cvr=0.010, aov=5000, half_sat=10000),
}
PLATFORM_SHARE = [0.28, 0.25, 0.20, 0.15, 0.12]  # share of rows per platform

# Campaign date windows (2025) and multipliers on CTR / CVR
CAMPAIGNS = {
    "Always-On Brand":   dict(start="2025-01-01", end="2025-12-31", ctr=0.90, cvr=0.70),
    "Eid ul Fitr Sale":  dict(start="2025-03-10", end="2025-03-31", ctr=1.20, cvr=1.50),
    "Eid ul Adha Sale":  dict(start="2025-05-20", end="2025-06-07", ctr=1.15, cvr=1.40),
    "Back to School":    dict(start="2025-08-01", end="2025-08-31", ctr=1.05, cvr=1.15),
    "Winter Collection": dict(start="2025-10-15", end="2025-12-31", ctr=1.00, cvr=1.10),
    "11.11 Mega Sale":   dict(start="2025-11-05", end="2025-11-12", ctr=1.30, cvr=1.60),
}
CAMPAIGN_SHARE = [0.35, 0.12, 0.10, 0.10, 0.20, 0.13]

AGES = ["18-24", "25-34", "35-44", "45+"]
AGE_SHARE = [0.30, 0.37, 0.20, 0.13]
AGE_MULT = {  # conversion multiplier by platform x age group
    "Facebook":  [0.8, 1.0, 1.2, 1.1],
    "Instagram": [1.2, 1.1, 0.8, 0.6],
    "Google":    [0.9, 1.1, 1.1, 1.0],
    "TikTok":    [1.4, 0.9, 0.6, 0.4],
    "YouTube":   [1.0, 1.0, 1.0, 1.0],
}

GENDERS = ["Male", "Female"]
GENDER_SHARE = [0.55, 0.45]
GENDER_MULT = {  # conversion multiplier by platform x gender
    "Facebook":  [1.00, 1.00],
    "Instagram": [0.90, 1.15],
    "Google":    [1.00, 1.00],
    "TikTok":    [1.00, 1.05],
    "YouTube":   [1.05, 0.95],
}

CITIES = ["Karachi", "Lahore", "Islamabad", "Rawalpindi",
          "Faisalabad", "Multan", "Peshawar", "Hyderabad"]
CITY_SHARE = [0.24, 0.22, 0.10, 0.08, 0.10, 0.08, 0.08, 0.10]
CITY_AOV_MULT = [1.05, 1.05, 1.15, 1.00, 0.90, 0.90, 0.90, 0.85]

DEVICES = ["Mobile", "Desktop", "Tablet"]
DEVICE_SHARE = [0.80, 0.15, 0.05]
DEVICE_CVR_MULT = [1.00, 1.25, 1.05]


def generate(n, seed=42):
    rng = np.random.default_rng(seed)
    plats = list(PLATFORMS)
    camps = list(CAMPAIGNS)

    p = rng.choice(len(plats), size=n, p=PLATFORM_SHARE)
    c = rng.choice(len(camps), size=n, p=CAMPAIGN_SHARE)
    a = rng.choice(len(AGES), size=n, p=AGE_SHARE)
    g = rng.choice(len(GENDERS), size=n, p=GENDER_SHARE)
    ci = rng.choice(len(CITIES), size=n, p=CITY_SHARE)
    d = rng.choice(len(DEVICES), size=n, p=DEVICE_SHARE)

    def parr(key):
        return np.array([PLATFORMS[x][key] for x in plats], dtype=float)[p]

    def carr(key):
        return np.array([CAMPAIGNS[x][key] for x in camps])

    # dates: random day inside each campaign's window
    starts = carr("start").astype("datetime64[D]")
    ends = carr("end").astype("datetime64[D]")
    lengths = (ends - starts).astype(int) + 1
    offset = (rng.random(n) * lengths[c]).astype(int)
    dates = starts[c] + offset.astype("timedelta64[D]")

    # spend per row (PKR)
    spend = np.clip(np.round(rng.lognormal(np.log(4000), 0.8, n)), 200, 150000)

    # diminishing returns: efficiency falls as spend in a slice grows
    sat = 1.0 / (1.0 + spend / parr("half_sat"))

    impressions = rng.poisson(spend / parr("cpm") * 1000 * rng.lognormal(0, 0.15, n))
    ctr = np.clip(parr("ctr") * carr("ctr").astype(float)[c] * sat
                  * rng.lognormal(0, 0.20, n), 0, 1)
    clicks = rng.binomial(impressions, ctr)

    age_mult = np.array([AGE_MULT[x] for x in plats])[p, a]
    gen_mult = np.array([GENDER_MULT[x] for x in plats])[p, g]
    dev_mult = np.array(DEVICE_CVR_MULT)[d]
    cvr = np.clip(parr("cvr") * carr("cvr").astype(float)[c] * age_mult
                  * gen_mult * dev_mult * rng.lognormal(0, 0.25, n), 0, 1)
    conversions = rng.binomial(clicks, cvr)

    revenue = np.round(conversions * parr("aov") * np.array(CITY_AOV_MULT)[ci]
                       * rng.lognormal(0, 0.10, n))

    df = pd.DataFrame({
        "date": dates,
        "campaign": pd.Categorical.from_codes(c, camps),
        "platform": pd.Categorical.from_codes(p, plats),
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend.astype(np.int64),
        "conversions": conversions,
        "revenue": revenue.astype(np.int64),
        "age": pd.Categorical.from_codes(a, AGES),
        "gender": pd.Categorical.from_codes(g, GENDERS),
        "city": pd.Categorical.from_codes(ci, CITIES),
        "device": pd.Categorical.from_codes(d, DEVICES),
    })
    return df.sort_values("date").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = generate(args.rows, args.seed)

    out_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"ads_{args.rows}.csv"
    df.to_csv(out, index=False, date_format="%Y-%m-%d")

    print(f"Saved {len(df):,} rows -> {out}")
    s = df.groupby("platform", observed=True)[["spend", "revenue"]].sum()
    s["ROAS"] = (s["revenue"] / s["spend"]).round(2)
    print(s)


if __name__ == "__main__":
    main()