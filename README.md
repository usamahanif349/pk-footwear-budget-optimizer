# 👟 Digital Advertising Budget Optimizer: Borjan, Servis and Ndure

**Live dashboard:** https://pk-footwear-budget-optimizer.streamlit.app/
**Course:** Big Data Analytics (marketing focus) · Project 2
**Builds on Project 1:** [Pakistani Footwear Brand Sentiment Analysis](https://github.com/usamahanif349/pk-footwear-sentiment-analysis) (same three brands)
**AI assistance:** built with help from Claude (Anthropic's AI) for parts of the code, testing and dashboard design.

> ⚠️ **The ad data is simulated.** We have no access to these brands' real ad accounts, so every ad record is generated from clearly stated assumptions. What is real: each brand's **customer sentiment from Project 1**, which changes how well that brand's ads convert. Results show the **method** (KPIs → response curves → optimisation → validation → Big Data benchmark), not the brands' real ad results.

## The business question

Borjan, Servis and Ndure advertise on **Facebook, Instagram, Google, TikTok and YouTube**. Each brand's management asks:

> **"Where should we spend the next Rs. 1,000,000?"**

## How Project 1 feeds in

Project 1 labelled 881 YouTube comments and Google Maps reviews with a multilingual transformer (XLM-R). Each brand's net sentiment (positive minus negative share) adjusts its ad conversion rate: **+10 points of net sentiment = +5% conversion rate** (an assumption).

| Brand | Positive | Negative | Reviews | Effect on conversion rate |
|---|---|---|---|---|
| Borjan | 49% | 31% | 147 | +9.2% |
| Servis | 31% | 17% | 576 | +7.5% |
| Ndure | 33% | 38% | 158 | −2.5% |

Each brand also has an assumed **positioning**: order value (Borjan higher, Servis lower) and how well its audience responds per platform (for example Ndure's younger audience on TikTok). These are assumptions, listed in `src/simulation/generate_data.py`.

## Key results

### 1. Recommended split of Rs. 1,000,000 per brand (one month)

| Platform | Borjan | Servis | Ndure |
|---|---|---|---|
| Facebook | **31.5%** | **35.6%** | 22.2% |
| Instagram | 28.6% | 20.3% | 22.9% |
| TikTok | 23.6% | 25.4% | **40.1%** |
| Google | 16.0% | 16.4% | 12.8% |
| YouTube | 0.4% | 2.3% | 1.9% |
| **Return on the next rupee** | Rs. 2.36 | Rs. 1.96 | Rs. 2.19 |

- **Each brand gets a different plan.** Borjan leads with Facebook and Instagram, Servis with Facebook, and Ndure puts 40% on TikTok.
- **The return on the next rupee is equal on every funded platform** within a brand. This is the textbook optimality condition: if one platform's last rupee earned more, moving money there would raise revenue.
- **Servis is slightly over-budgeted:** its next rupee returns Rs. 1.96, just below break-even (Rs. 2.00 at a 50% margin), so Rs. 1M is a bit more than its profit-maximising budget.
- **YouTube gets almost nothing** for all three brands. In real life YouTube builds awareness, which this data doesn't measure, so the dashboard offers a minimum-share setting.

### 2. Optimizer vs simple strategies

| Strategy | Borjan | Servis | Ndure |
|---|---|---|---|
| **Optimizer** (expected revenue) | **Rs. 3,979,130** | **Rs. 3,099,231** | **Rs. 3,479,996** |
| Last year's split | +3.3% | +3.2% | −0.1% |
| Equal split | 0.0% | 0.0% | 0.0% |
| **Optimizer vs equal split** | **+5.7%** | **+5.4%** | **+7.7%** |
| All on best average ROAS | −42.9% (Facebook) | −33.7% (Facebook) | −30.3% (TikTok) |

Percentages are revenue vs the equal split. **Putting everything on the "best" platform is the worst strategy** for every brand: diminishing returns punish putting all eggs in one basket. Ndure gains the most from optimising, because its historical spend ignores its strength on TikTok.

### 3. Self-check: does the optimizer find the *true* best split?

Because the data is simulated, the true optimum is known. For each brand, data was regenerated 5 times at 10k, 100k and 1M rows, and every result was scored against the truth:

| Brand | Optimizer at 10k rows | Optimizer at 1M rows | Equal split | Last year's split | Share error, 10k → 1M rows |
|---|---|---|---|---|---|
| Borjan | 99.83% | 99.999% | 93.6% | 97.1% | 1.15 → 0.13 pp |
| Servis | 99.86% | 99.999% | 94.6% | 97.3% | 1.42 → 0.12 pp |
| Ndure | 99.90% | 99.998% | 92.1% | 92.2% | 1.06 → 0.15 pp |

**Each 10× more data cuts the share error by about 3×** (the √n rule). More data mainly makes the split *more precise and stable*; the revenue gain from 10k to 1M rows is small.

### 4. Hard mode: what if the real curve has a different shape?

The test above is a best case: the data uses the same curve shape the optimizer assumes. In hard mode the data comes from two other shapes, while the optimizer still fits its usual curve (5 runs per setting, % of the true best revenue at 1M rows):

| True curve shape | Borjan | Servis | Ndure | Equal split (range) |
|---|---|---|---|---|
| Same as assumed | 99.999% | 99.999% | 99.998% | 92–95% |
| Exponential (saturates faster) | 99.89% | 99.90% | 99.96% | 90–92% |
| S-curve (small budgets barely work) | 99.98% | 96.28% | **84.49%** | 60–64% |

- **Robust to the exponential shape:** 99.6% or more of the best revenue for every brand and data size.
- **Weak spot, the S-curve:** when small budgets barely work, the true best plan **concentrates** money on fewer platforms. For Ndure the true best is 78% TikTok and 22% Google, but the assumed curve always favours spreading, so the optimizer gets only **84.5%** of the best revenue. **More data does not close the gap** (84.9% at 10k rows, 84.5% at 1M), because a wrong model can't be fixed with more rows.
- It still beats the equal split (64%) and last year's split (72%) by a wide margin. The natural next step is to fit several curve shapes and keep the best fit.

### 5. How sure are we? (bootstrap)

The fit and optimisation are rerun on 200 bootstrap resamples to get a 90% range per platform (shown in the dashboard). To check whether these ranges are honest, the whole procedure was repeated on **30 fresh simulated datasets per brand**, counting how often the true best share fell inside the range:

| Bootstrap resamples | Borjan | Servis | Ndure |
|---|---|---|---|
| 50 | 84.7% | 88.0% | 92.7% |
| 200 | 90.0% | 94.0% | 94.0% |

With 200 resamples the ranges are **well calibrated** (target 90%), so the dashboard uses 200. With only 50, Borjan's ranges were slightly too narrow. A second method (the "basic" bootstrap) was no better, so the percentile method is kept.

### 6. Brand comparison (simulated history)

| Brand | Ad spend | Revenue | ROAS | Conversion rate | Cost per order |
|---|---|---|---|---|---|
| Borjan | Rs. 56.2M | Rs. 160.3M | 2.85 | 1.37% | Rs. 1,798 |
| Servis | Rs. 54.6M | Rs. 125.1M | 2.29 | 1.35% | Rs. 1,715 |
| Ndure | Rs. 54.5M | Rs. 129.0M | 2.37 | 1.10% | Rs. 1,928 |

Borjan earns the most per rupee: it has the best sentiment and the highest order value. Ndure's weaker sentiment shows up as the lowest conversion rate.

### 7. Big Data benchmark: Pandas vs Hadoop MapReduce vs Spark

Same job on every engine: read the CSV, group by platform + campaign, and sum impressions, clicks, spend, conversions and revenue. Google Colab free tier (1 machine, 2 cores, 12 GB RAM); Hadoop 3.5.0 Streaming (local mode); PySpark 4.0.5 (`local[*]`); median of 3 runs. **All engines produced identical totals at every size.**

| Rows | File size | Pandas | Hadoop MapReduce | Spark |
|---|---|---|---|---|
| 10,000 | 0.8 MB | 0.01 s | 4.58 s | 1.07 s |
| 100,000 | 8.2 MB | 0.09 s | 4.62 s | 0.93 s |
| 1,000,000 | 82 MB | 0.71 s | 7.54 s | 2.09 s |
| 10,000,000 | 811 MB | 7.55 s | 24.83 s | 13.54 s |

**Stress test: 100,000,000 rows (8 GB, the 10M file replicated 10×, 1 run each)**

| Engine | Result |
|---|---|
| Pandas (normal) | ❌ out of memory (7.8 GB cap) |
| Pandas (chunked, 2M rows at a time) | ✅ 82.8 s, 0.49 GB peak RAM |
| Spark | ✅ 137.3 s |
| Hadoop MapReduce | ✅ 212.7 s |

*The benchmark was run before the `brand` column was added. The job reads the same columns in the same positions (`brand` is the last column), so the timings still apply.*

**Takeaways:**
- On one machine, Pandas is fastest up to 10M rows. Hadoop has about 4.5 s of start-up per job and Spark about 1 s, and neither catches up per row on 2 cores.
- At 100M rows, plain Pandas runs out of memory, while Spark and Hadoop finish with correct results.
- Chunked Pandas was still the fastest on one machine. **The real value of Spark and Hadoop is spreading work across many machines and fault tolerance**, which a single Colab machine can't demonstrate.
- **Decision rule:** Pandas while the data fits in memory, chunked processing when it doesn't, and Spark when you need a cluster. Hadoop MapReduce is the slowest and largely replaced by Spark for this kind of job.

## Method

1. **Simulate** campaign data with the schema from the brief: `date, campaign, platform, impressions, clicks, spend, conversions, revenue, age, gender, city, device`, plus a `brand` column (Borjan, Servis, Ndure). It covers 6 campaigns (Always-On, Eid ul Fitr, Eid ul Adha, Back to School, Winter Collection, 11.11), 8 Pakistani cities, 4 age groups, 2 genders and 3 devices, with built-in **diminishing returns**.
2. **Link Project 1:** each brand's real customer sentiment adjusts its conversion rate.
3. **KPIs** computed from sums: CTR, CPC, CVR (conversion rate), CPA, ROAS, revenue, and campaign performance.
4. **Response curves:** per brand and platform, fit `revenue(s) = a·s / (1 + s/h)` with non-linear least squares (`scipy.optimize.curve_fit`). `a` = ROAS at very small spend, `h` = spend where efficiency halves.
5. **Optimise:** per brand, maximise total expected revenue subject to the budget and optional min/max shares (SLSQP). With a fixed budget, maximising revenue also maximises profit.
6. **Validate** against the known true optimum (10k / 100k / 1M rows × 5 seeds per brand), then repeat in **hard mode** with data from two other curve shapes.
7. **Bootstrap** (200 resamples) for uncertainty, and check on 30 fresh datasets per brand that the 90% ranges contain the truth about 90% of the time.
8. **Benchmark** Pandas vs Hadoop MapReduce vs Spark from 10k to 100M rows.

## Simulation assumptions (PKR)

| Platform | CPM | Base CTR | Base CVR | Avg order value | Half-saturation spend |
|---|---|---|---|---|---|
| Facebook | 150 | 1.2% | 1.2% | 4,500 | 8,000 |
| Instagram | 180 | 1.0% | 1.4% | 4,800 | 7,000 |
| Google | 600 | 3.0% | 1.8% | 5,500 | 3,000 |
| TikTok | 90 | 1.6% | 0.5% | 3,800 | 12,000 |
| YouTube | 220 | 0.7% | 1.0% | 5,000 | 10,000 |

| Brand | Order value × | Facebook fit | Instagram fit | Google fit | TikTok fit | YouTube fit |
|---|---|---|---|---|---|---|
| Borjan | 1.10 | 1.00 | 1.15 | 1.00 | 0.85 | 0.90 |
| Servis | 0.85 | 1.15 | 0.90 | 1.05 | 0.90 | 1.10 |
| Ndure | 1.00 | 0.85 | 1.10 | 0.95 | 1.30 | 1.00 |

"Fit" multiplies the click-through rate. Campaign, age, gender, device and city multipliers, plus random noise, are defined in `src/simulation/generate_data.py`. Planning assumptions: 30 days × 2 ad sets = **60 ad slices per platform**, and a **50% gross margin**. Both can be changed in the dashboard.

## Limitations (please read)

- **Simulated ad data.** Results reflect the assumptions above, not these brands' real ad accounts or real Pakistani ad prices.
- **Weak sentiment input.** The Project 1 model is only moderately accurate (XLM-R accuracy 0.55), Servis's sentiment comes from YouTube comments only, and the size of the sentiment effect on conversions is an assumption.
- **Brand positioning is assumed**, not sourced from the companies.
- **Curve shape.** The main validation uses the same curve shape as the generator. With an S-curve the optimizer loses up to about 15% of the best revenue (Ndure), and more data does not fix it.
- **No confounding.** Simulated spend is random. In reality, brands spend more when demand is already high (Eid, 11.11), which makes ads look more effective than they are.
- **Revenue only.** Brand awareness, YouTube's main purpose, is not measured.
- **No time dynamics.** No ad fatigue, carry-over effects or seasonality inside the optimizer.
- **One curve per brand and platform.** Segments (age, city, device) are analysed but not optimised separately.
- **Scale assumption.** Absolute revenue depends on the "slices" setting. Comparisons between strategies are more reliable than the absolute numbers.
- **Uncertainty ranges** only cover noise from limited data, not a wrong curve shape or wrong assumptions.
- **Benchmark scope.** One 2-core machine (no real cluster), a simple group-by job, the 100M file is replicated, 1 run at 100M, Spark JVM start-up excluded, and Colab speed varies between runs.

## Repository structure

```
data/raw/ads_30000.csv              30k-row sample, 10k per brand (larger files are generated, not stored)
data/processed/                     KPI tables, recommendations, validation and benchmark results
notebooks/benchmark_pandas_mapreduce_spark.ipynb   Colab: Hadoop + Spark benchmark
src/simulation/generate_data.py     simulated ad data generator (brands, sentiment, assumptions)
src/analysis/kpis.py                CTR, CPC, CVR, CPA, ROAS tables
src/optimizer/optimize.py           response curves + budget optimiser, per brand
src/optimizer/validate.py           self-check against the true optimum
src/optimizer/hard_mode.py          self-check when the true curve has a different shape
src/optimizer/bootstrap_check.py    are the bootstrap 90% ranges honest? (30 datasets per brand)
src/mapreduce/mapper.py, reducer.py Hadoop Streaming job
src/dashboard/app.py                Streamlit dashboard
```

## How to run (Windows, Python 3.12)

```
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src\simulation\generate_data.py --rows 30000
python src\analysis\kpis.py --file ads_30000.csv
python src\optimizer\optimize.py --file ads_30000.csv
python src\optimizer\validate.py
python src\optimizer\hard_mode.py
python src\optimizer\bootstrap_check.py
streamlit run src\dashboard\app.py
```

The benchmark needs Java, Hadoop and Spark, so it runs in Google Colab: open `notebooks/benchmark_pandas_mapreduce_spark.ipynb`.

## Tools

Python · pandas · NumPy · SciPy · Plotly · Streamlit · Apache Hadoop 3.5.0 (Streaming) · Apache Spark (PySpark 4.0.5) · Google Colab