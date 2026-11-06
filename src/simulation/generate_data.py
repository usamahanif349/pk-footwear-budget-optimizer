"""
Simulate digital ad campaign data for three Pakistani footwear brands:
Borjan, Servis and Ndure (the brands from Project 1).

The ADS DATA IS SIMULATED: we have no access to these brands' real ad accounts.
What is real: each brand's customer sentiment from Project 1 (XLM-R predictions
on 881 YouTube comments and Google Maps reviews), which nudges how well that
brand's ads convert. Everything else below is an ASSUMPTION.

Usage (Command Prompt):  python src\\simulation\\generate_data.py --rows 30000
(rows = total rows, split equally across the three brands)
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

# ---------------- BRANDS (from Project 1) ----------------
# Share of each brand's reviews that the XLM-R model labelled positive / negative
# in Project 1 (pk-footwear-sentiment-analysis, results_bert.csv). REAL numbers,
# from a weak model (accuracy 0.55); Servis comes from YouTube comments only.
SENTIMENT = {
    "Borjan": dict(positive=0.490, negative=0.306, reviews=147),
    "Servis": dict(positive=0.314, negative=0.165, reviews=576),
    "Ndure":  dict(positive=0.329, negative=0.380, reviews=158),
}
SENTIMENT_EFFECT = 0.5  # ASSUMPTION: +10 points net sentiment -> +5% conversion rate

# ASSUMPTIONS about each brand's positioning (not sourced from the companies):
# aov = order value multiplier vs the platform average, aff = how well the
# brand's audience responds on each platform (multiplies click-through rate).
BRAND_PROFILE = {
    "Borjan": dict(aov=1.10, aff=dict(Facebook=1.00, Instagram=1.15, Google=1.00,
                                      TikTok=0.85, YouTube=0.90)),
    "Servis": dict(aov=0.85, aff=dict(Facebook=1.15, Instagram=0.90, Google=1.05,
                                      TikTok=0.90, YouTube=1.10)),
    "Ndure":  dict(aov=1.00, aff=dict(Facebook=0.85, Instagram=1.10, Google=0.95,
                                      TikTok=1.30, YouTube=1.00)),
}
BRANDS = list(BRAND_PROFILE)


def net_sentiment(brand):
    s = SENTIMENT[brand]
    return s["positive"] - s["negative"]


def sentiment_mult(brand):
    """Conversion-rate multiplier from the brand's Project 1 sentiment."""
    return 1.0 + SENTIMENT_EFFECT * net_sentiment(brand)


DEVICES = ["Mobile", "Desktop", "Tablet"]
DEVICE_SHARE = [0.80, 0.15, 0.05]
DEVICE_CVR_MULT = [1.00, 1.25, 1.05]

# Shape of diminishing returns. "hyperbolic" is the main setting and matches
# the curve the optimizer assumes. The other two are for the "hard mode" test,
# where the TRUE curve has a different shape than the optimizer expects.
SHAPES = ["hyperbolic", "exponential", "s_curve"]


def efficiency(spend, half_sat, shape="hyperbolic"):
    """Share of full ad efficiency left at this spend (between 0 and 1)."""
    x = np.asarray(spend, dtype=float) / half_sat
    if shape == "hyperbolic":    # 1/(1+x): smooth decline, half at x=1
        return 1.0 / (1.0 + x)
    if shape == "exponential":   # saturates faster, revenue has a hard ceiling
        x = np.maximum(x, 1e-12)
        return (1.0 - np.exp(-x)) / x
    if shape == "s_curve":       # small budgets barely work, best at x=1
        return 2.0 * x / (1.0 + x ** 2)
    raise ValueError(f"unknown shape: {shape}")


def generate(n, seed=42, shape="hyperbolic", brands=None):
    """n rows in total, split equally across `brands` (default: all three)."""
    rng = np.random.default_rng(seed)
    plats = list(PLATFORMS)
    camps = list(CAMPAIGNS)
    brands = list(brands) if brands else BRANDS
    b = rng.choice(len(brands), size=n)

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
    sat = efficiency(spend, parr("half_sat"), shape)

    brand_aff = np.array([[BRAND_PROFILE[br]["aff"][pl] for pl in plats] for br in brands])[b, p]
    brand_cvr = np.array([sentiment_mult(br) for br in brands])[b]
    brand_aov = np.array([BRAND_PROFILE[br]["aov"] for br in brands])[b]

    impressions = rng.poisson(spend / parr("cpm") * 1000 * rng.lognormal(0, 0.15, n))
    ctr = np.clip(parr("ctr") * carr("ctr").astype(float)[c] * sat * brand_aff
                  * rng.lognormal(0, 0.20, n), 0, 1)
    clicks = rng.binomial(impressions, ctr)

    age_mult = np.array([AGE_MULT[x] for x in plats])[p, a]
    gen_mult = np.array([GENDER_MULT[x] for x in plats])[p, g]
    dev_mult = np.array(DEVICE_CVR_MULT)[d]
    cvr = np.clip(parr("cvr") * carr("cvr").astype(float)[c] * age_mult
                  * gen_mult * dev_mult * brand_cvr * rng.lognormal(0, 0.25, n), 0, 1)
    conversions = rng.binomial(clicks, cvr)

    revenue = np.round(conversions * parr("aov") * brand_aov * np.array(CITY_AOV_MULT)[ci]
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
        # brand goes LAST so the MapReduce/Spark column positions stay the same
        "brand": pd.Categorical.from_codes(b, brands),
    })
    return df.sort_values("date").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--shape", default="hyperbolic", choices=SHAPES)
    args = ap.parse_args()

    df = generate(args.rows, args.seed, args.shape)

    out_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"ads_{args.rows}.csv"
    df.to_csv(out, index=False, date_format="%Y-%m-%d")

    print(f"Saved {len(df):,} rows -> {out}")
    s = df.groupby(["brand", "platform"], observed=True)[["spend", "revenue"]].sum()
    s["ROAS"] = (s["revenue"] / s["spend"]).round(2)
    print(s)


if __name__ == "__main__":
    main()