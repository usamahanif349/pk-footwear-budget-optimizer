# 👟 Digital Advertising Budget Optimizer — Pakistani Footwear Brand

**Live dashboard:** https://pk-footwear-budget-optimizer.streamlit.app/
**Course:** Big Data Analytics (marketing focus) · Project 2
**Previous project:** [Pakistani Footwear Brand Sentiment Analysis](https://github.com/usamahanif349/pk-footwear-sentiment-analysis)
**AI assistance:** built with help from Claude (Anthropic's AI) for parts of the code, testing and dashboard design.

> ⚠️ **All data in this project is simulated** for a fictional brand, *StepUp Footwear*, using clearly stated assumptions. The project demonstrates the **method** (KPIs → response curves → optimisation → validation → Big Data benchmark), not real Pakistani ad prices.

## The business question

A footwear brand advertises on **Facebook, Instagram, Google, TikTok and YouTube**. Management asks:

> **"Where should we spend the next Rs. 1,000,000?"**

## Key results

### 1. Recommended split of Rs. 1,000,000 (one month)

| Platform | Share | Spend (Rs.) | Expected ROAS | Marginal ROAS |
|---|---|---|---|---|
| Facebook | 32.5% | 324,770 | 3.46 | 2.07 |
| TikTok | 27.4% | 274,499 | 3.12 | 2.07 |
| Instagram | 23.8% | 238,384 | 3.26 | 2.07 |
| Google | 16.2% | 162,347 | 3.58 | 2.07 |
| YouTube | 0.0% | 0 | — | 1.98 |

- **Marginal ROAS is equal (2.07) on every funded platform.** This is the textbook optimality condition: if one platform's last rupee earned more, moving money there would raise revenue.
- **YouTube gets 0%** because even its *first* rupee earns only Rs. 1.98, less than the others' last rupee. In real life YouTube builds awareness, which this data doesn't measure, so the dashboard offers a minimum-share setting.
- At a 50% gross margin, break-even ROAS is 2.0. The marginal ROAS of 2.07 is just above it, so Rs. 1M is close to the profit-maximising budget under these assumptions.

### 2. Optimizer vs simple strategies

| Strategy | Expected revenue (Rs.) | Expected profit* (Rs.) | vs equal split |
|---|---|---|---|
| **Optimizer** | **3,339,184** | **669,592** | **+5.6%** |
| Last year's split | 3,237,875 | 618,938 | +2.4% |
| Equal split | 3,160,924 | 580,462 | 0.0% |
| All on best average ROAS (Facebook) | 1,883,245 | −58,378 | −40.4% |

\*Profit = 50% margin × revenue − ad spend (margin is an assumption).

**Putting everything on the "best" platform loses money.** Because of diminishing returns, "pick the highest ROAS" is the worst strategy.

### 3. Self-check: does the optimizer find the *true* best split?

Because the data is simulated, the true optimum is known. Data was regenerated 5 times at each size, and every result was scored against the truth:

| Rows | Revenue captured (% of true best) | Avg share error (pp) |
|---|---|---|
| 10,000 | 99.88% | 1.32 ± 0.53 |
| 100,000 | 99.99% | 0.43 ± 0.18 |
| 1,000,000 | 99.998% | 0.16 ± 0.03 |

For comparison, the equal split captures 94.4% and last year's split 96.4%.

**Each 10× more data cuts the share error by about 3×** (the √n rule). More data mainly makes the split *more precise and stable*; the revenue gain from 10k to 1M rows is small.

Fitted vs true curve parameters (10k rows): the half-saturation spend was recovered closely for Facebook (7,994 vs 8,000), Instagram (6,885 vs 7,000) and YouTube (11,850 vs 10,000), less well for Google (3,696 vs 3,000) and TikTok (8,954 vs 12,000).

### 4. How sure are we? (bootstrap)

The fit and optimisation were rerun on 50 bootstrap resamples to get a 90% range per platform (shown in the dashboard). **2 of the 5 true optimal shares (Google 14.3%, TikTok 30.6%) fall just outside their ranges**, so with 10k rows the ranges are somewhat over-confident. Treat them as a guide, not a guarantee.

### 5. Big Data benchmark: Pandas vs Hadoop MapReduce vs Spark

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

**Takeaways:**
- On one machine, Pandas is fastest up to 10M rows. Hadoop has about 4.5 s of start-up per job and Spark about 1 s, and neither catches up per row on 2 cores.
- At 100M rows, plain Pandas runs out of memory, while Spark and Hadoop finish with correct results.
- Chunked Pandas was still the fastest on one machine. **The real value of Spark and Hadoop is spreading work across many machines and fault tolerance**, which a single Colab machine can't demonstrate.
- **Decision rule:** Pandas while the data fits in memory, chunked processing when it doesn't, and Spark when you need a cluster. Hadoop MapReduce is the slowest and largely replaced by Spark for this kind of job.

## Method

1. **Simulate** campaign data with the schema from the brief: `date, campaign, platform, impressions, clicks, spend, conversions, revenue, age, gender, city, device`. It covers 6 campaigns (Always-On, Eid ul Fitr, Eid ul Adha, Back to School, Winter Collection, 11.11), 8 Pakistani cities, 4 age groups, 2 genders and 3 devices, with built-in **diminishing returns**.
2. **KPIs** computed from sums: CTR, CPC, CVR (conversion rate), CPA, ROAS, revenue, and campaign performance.
3. **Response curves:** per platform, fit `revenue(s) = a·s / (1 + s/h)` with non-linear least squares (`scipy.optimize.curve_fit`). `a` = ROAS at very small spend, `h` = spend where efficiency halves.
4. **Optimise:** maximise total expected revenue subject to the budget and optional min/max shares (SLSQP). With a fixed budget, maximising revenue also maximises profit.
5. **Validate** against the known true optimum (10k / 100k / 1M rows × 5 seeds) and **bootstrap** for uncertainty.
6. **Benchmark** Pandas vs Hadoop MapReduce vs Spark from 10k to 100M rows.

## Simulation assumptions (PKR)

| Platform | CPM | Base CTR | Base CVR | Avg order value | Half-saturation spend |
|---|---|---|---|---|---|
| Facebook | 150 | 1.2% | 1.2% | 4,500 | 8,000 |
| Instagram | 180 | 1.0% | 1.4% | 4,800 | 7,000 |
| Google | 600 | 3.0% | 1.8% | 5,500 | 3,000 |
| TikTok | 90 | 1.6% | 0.5% | 3,800 | 12,000 |
| YouTube | 220 | 0.7% | 1.0% | 5,000 | 10,000 |

Campaign, age, gender, device and city multipliers, plus random noise, are defined in `src/simulation/generate_data.py`. Planning assumptions: 30 days × 2 ad sets = **60 ad slices per platform**, and a **50% gross margin**. Both can be changed in the dashboard.

## Limitations (please read)

- **Simulated data.** Results reflect the assumptions above, not real Pakistani ad prices. The numbers are plausible, not sourced from a real company.
- **Best-case validation.** The optimizer assumes the same curve shape the generator used. Real ad data would not follow this formula exactly, so real accuracy would be lower.
- **No confounding.** Simulated spend is random. In reality, brands spend more when demand is already high (Eid, 11.11), which makes ads look more effective than they are.
- **Revenue only.** Brand awareness, YouTube's main purpose, is not measured.
- **No time dynamics.** No ad fatigue, carry-over effects or seasonality inside the optimizer.
- **One curve per platform.** Segments (age, city, device) are analysed but not optimised separately.
- **Scale assumption.** Absolute revenue depends on the "slices" setting. Comparisons between strategies are more reliable than the absolute numbers.
- **Bootstrap ranges are over-confident** at 10k rows (2 of 5 true values fall outside).
- **Benchmark scope.** One 2-core machine (no real cluster), a simple group-by job, the 100M file is replicated, 1 run at 100M, Spark JVM start-up excluded, and Colab speed varies between runs.

## Repository structure

```
data/raw/ads_10000.csv              10k-row sample (larger files are generated, not stored)
data/processed/                     KPI tables, recommendation, validation and benchmark results
notebooks/benchmark_pandas_mapreduce_spark.ipynb   Colab: Hadoop + Spark benchmark
src/simulation/generate_data.py     simulated ad data generator
src/analysis/kpis.py                CTR, CPC, CVR, CPA, ROAS tables
src/optimizer/optimize.py           response curves + budget optimiser
src/optimizer/validate.py           self-check against the true optimum
src/mapreduce/mapper.py, reducer.py Hadoop Streaming job
src/dashboard/app.py                Streamlit dashboard
```

## How to run (Windows, Python 3.12)

```
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src\simulation\generate_data.py --rows 10000
python src\analysis\kpis.py --file ads_10000.csv
python src\optimizer\optimize.py --file ads_10000.csv
python src\optimizer\validate.py
streamlit run src\dashboard\app.py
```

The benchmark needs Java, Hadoop and Spark, so it runs in Google Colab: open `notebooks/benchmark_pandas_mapreduce_spark.ipynb`.

## Tools

Python · pandas · NumPy · SciPy · Plotly · Streamlit · Apache Hadoop 3.5.0 (Streaming) · Apache Spark (PySpark 4.0.5) · Google Colab