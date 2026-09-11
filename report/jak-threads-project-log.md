# ThreadSense AI — Project Log
### JAK Threads | AI-Powered Retail Intelligence System | 7th-Semester Minor Project

Living document. Update after every step — this becomes the backbone of your final report's methodology section.

---

## Project Overview

**Goal:** predict slow-moving inventory risk, classify product lifecycle stage, and recommend discounts for JAK Threads, surfaced through an interactive dashboard.

**Tech stack:** Python, Pandas, Scikit-learn, Streamlit, Plotly, SQLite

**10-step architecture** (per original diagram): Data Collection → Preprocessing → Feature Engineering → Risk Classification (ML) → Lifecycle Analysis → Channel/Location Analysis → Discount Engine → Dashboard → Business Insights → Owner Decision

---

## Status: Steps 1–3 complete and verified. Step 4 not yet started.

---

### Step 1 — Data Collection ✅

- **Source:** synthetic dataset generated via Google Antigravity (agentic coding IDE), using a script (`generate_retail_dataset.py`) that builds 3 hidden operational cohorts — Fast Movers (35%), Steady Sellers (40%), Slow Movers (25%) — each with distinct velocity/stock/recency distributions.
- **Shape:** 1,200 products × 21 raw columns.
- **Exact reproduction parameters found:** `brand_name="JAK"`, `snapshot_date=2026-08-25`, `random_state=42`, `n_samples=1200`. (The script as originally handed over had wrong defaults — `brand_name="JAK Threads"` and `snapshot_date=2026-09-01` — which would NOT have reproduced the actual data. Corrected version delivered.)

### Step 2 — Preprocessing & Cleaning ✅

- Verified directly (not just assumed): 0 missing values, 0 duplicate rows, 0 duplicate Product_IDs, 0 negative prices/stock, 0 loss-making rows, 0 violations of the monotonic sales-window rule (7d ≤ 30d ≤ 60d ≤ 90d ≤ Total).
- **Why it's this clean:** built clean by construction in the generator script, not cleaned after the fact. Documented for the report since "nothing needed fixing" still needs to be shown as a checked step, not skipped.

### Step 3 — Feature Engineering ✅

All 9 features independently re-derived and verified as an **exact match** (1,200/1,200 rows) against the original data:

| Feature | Formula |
|---|---|
| Inventory_Age_Days | snapshot_date − Launch_Date |
| Days_Since_Last_Sale | snapshot_date − Last_Sale_Date |
| Sales_Velocity_7D | Units_Sold_7_Days ÷ 7 |
| Sales_Velocity_30D | Units_Sold_30_Days ÷ 30 |
| Sell_Through_Rate | Total_Units_Sold ÷ (Total_Units_Sold + Current_Stock) |
| Days_Of_Inventory | min(Current_Stock ÷ (Sales_Velocity_30D + 0.01), 365) |
| Sales_Acceleration | ((Units_Sold_7_Days÷7×30) − Units_Sold_30_Days) ÷ (Units_Sold_30_Days + 1) |
| Gross_Margin_Pct | (Selling_Price − Cost_Price) ÷ Selling_Price |
| Stock_to_Sales_Ratio | Current_Stock ÷ (Units_Sold_30_Days + 1) |

- **Not verified / carried over as-is:** `Slow_Moving_Index` (composite score), and everything derived from it — `Slow_Moving_Risk`, `Recommended_Discount_Pct`, `Lifecycle_Stage`. The original generation script for these was lost; I tried 4 reconstruction approaches (fixed caps, min-max normalization, percentile rank, linear regression — best fit R²=0.98, not exact) and could not pin the exact formula. These values are real and internally consistent, just not independently re-derivable right now.
- **Important framing for viva/report:** `Slow_Moving_Risk` is currently a **rule-based label** (perfect threshold match against Slow_Moving_Index, zero exceptions), not a trained model's output. This is the correct *input* for Step 4, not Step 4 itself.

---

## Files delivered so far

| File | What it is |
|---|---|
| `generate_retail_dataset.py` | Corrected raw-data generator (fixed defaults) |
| `feature_engineering.py` | Rebuilt Step 3 code, all 9 formulas verified |
| `jak_threads_locked_in_verified.csv` / `.xlsx` | ⭐ Canonical working dataset — raw + verified features + original risk/discount/lifecycle columns preserved |
| `JAK_Threads_Project_Data.zip` | All 5 xlsx files, organized into folders, with README |
| `threadsense-ai-build-guide.md` | Full 10-step build guide with day-wise plan for the 2-member team |

---

## Next: Step 4 — Risk Classification Model

Not started. Will involve: train/test split on the verified features, training a Decision Tree or Random Forest against the existing `Slow_Moving_Risk` labels, evaluating with a confusion matrix — the first genuinely "ML" deliverable in the project.

---

## Open items to revisit before final submission

- [ ] Decide whether to reconstruct `Slow_Moving_Index` cleanly from scratch (documented, owned formula) instead of relying on the un-reverse-engineered original
- [ ] Confirm department's policy on disclosing AI-assisted tooling (Antigravity + this conversation) in the report
- [ ] Steps 8–10 (dashboard, business insights, owner action) not yet started
