# ThreadSense AI — Build Guide (Mentor Notes)
### For a 2-member, 7th-semester AI & DS minor project

This is your roadmap. Follow it top to bottom — each step builds on the one before it. Don't jump to the ML model before your data is clean, and don't build the dashboard before your features exist. That order in your architecture diagram is not decorative — it's the actual dependency chain.

---

## Step 0: Setup (do this first, ~1–2 hours, not in your original estimate but essential)

1. **Install tools**: Python 3.10+, VS Code (or Jupyter/Colab), Git.
2. **Create a project folder** with this structure:
   ```
   threadsense-ai/
   ├── data/
   │   ├── raw/          ← original untouched data
   │   └── processed/    ← cleaned, feature-engineered data
   ├── notebooks/        ← exploration, experiments (messy is fine here)
   ├── src/               ← clean, reusable Python functions
   ├── models/            ← saved trained model files
   ├── dashboard/         ← Streamlit app
   └── report/            ← screenshots, writeup, diagrams
   ```
3. **Set up a virtual environment** and `pip install pandas numpy scikit-learn streamlit plotly sqlite3-compatible-lib`. Freeze it into `requirements.txt` as you go — you'll need this for the report.
4. **Git init**, and commit after every step below. This alone will make your viva easier — you can show progression.
5. **Decide on your data source now** (see Step 1) — this is the one decision that changes everything downstream.

---

## Step 1: Data Collection (2–3 hrs)

**Goal:** one clean-ish raw table with these columns: `product_id, product_name, category, size, color, price, channel, location, sale_date, quantity_sold, stock_qty, stock_date`.

You have two real options:

- **Option A — Real data exists**: If JAK Threads has actual POS/Excel exports, get them in CSV form. Real messy data is actually *better* for your project — it makes Step 2 meaningful instead of trivial.
- **Option B — No real data available**: Generate a **synthetic dataset**. This is completely normal and accepted for minor projects. Use `numpy`/`pandas` (and optionally the `Faker` library for names) to simulate:
  - 100–300 unique products across 4–6 categories
  - Sales transactions over 3–6 months
  - 3–4 channels (Website, Instagram, Store, Marketplace) and 2–3 locations
  - Deliberately inject *some* missing values, duplicate rows, and inconsistent text (e.g. "Store" vs "store ") — you'll need to clean these in Step 2, and a perfectly clean synthetic dataset makes that step look fake.

**Output:** `data/raw/sales_stock_data.csv`

---

## Step 2: Data Preprocessing & Cleaning (4–6 hrs)

Work in a notebook first, then move the final logic into a `src/preprocessing.py` function.

1. **Load and inspect**: `df.info()`, `df.isnull().sum()`, `df.duplicated().sum()` — always start by *measuring* the mess before fixing it.
2. **Handle missing values**: decide per column — drop rows with missing `product_id` (can't use those), but fill missing `size`/`color` with `"Unknown"` rather than dropping.
3. **Remove duplicates**.
4. **Fix data types**: dates → `pd.to_datetime`, categorical columns (category, channel, location) → `category` dtype.
5. **Standardize text**: lowercase/strip whitespace on category, channel, location names so `"store"` and `"Store "` don't get treated as different groups.
6. **Handle outliers**: for `price` and `quantity_sold`, use the IQR method (values outside Q1 − 1.5×IQR to Q3 + 1.5×IQR) to flag, and decide case by case whether to cap or remove.

**Output:** `data/processed/cleaned_data.csv`

---

## Step 3: Feature Engineering (4–5 hrs)

This is where you turn raw rows into signals the model can actually learn from. For each product, calculate:

| Feature | Formula | What it tells you |
|---|---|---|
| **Inventory Age** | Today − date first stocked | How long it's been sitting in inventory |
| **Days Since Last Sale** | Today − date of most recent sale | Is it actively selling or dead stock? |
| **Sales Velocity** | Units sold ÷ days in period | How fast it moves |
| **Sell-Through Rate** | Units sold ÷ (units sold + current stock) × 100 | % of stock that's actually sold |
| **Stock Coverage** | Current stock ÷ Sales Velocity | Days of stock left at current pace |

Use `groupby('product_id')` with `.agg()` for most of these. This is the step most students rush — don't. Every downstream model (Step 4, 5, 7) depends entirely on these five numbers being correct.

**Output:** `data/processed/features_data.csv`

---

## Step 4: Slow-Moving Risk Prediction (6–8 hrs)

Here's the part students usually get confused on: **you don't have a "risk" label in your raw data — you have to create it before you can predict it.**

1. **Create labels using rules first** (this becomes your training target):
   - e.g. High risk: Sell-Through < 20% AND Days Since Last Sale > 45
   - Medium risk: Sell-Through 20–50% OR moderate stock coverage
   - Low risk: everything else
   - Decide your own thresholds based on what looks reasonable in your data's distribution — plot histograms of sell-through rate and stock coverage first to pick sensible cutoffs.
2. **Train a classifier** (Decision Tree or Random Forest from `sklearn`) using Inventory Age, Sales Velocity, Sell-Through Rate, Stock Coverage, category, channel as inputs, and your rule-based risk label as the target.
3. **Split train/test** (80/20), evaluate with a confusion matrix and classification report — accuracy alone isn't enough, check precision/recall per class since "High risk" is probably a minority class.
4. **Save the model** with `joblib.dump()` into `models/`.

Be upfront in your report that the labels started as rules and the model learns to generalize/predict them on new products — that's a completely legitimate and common approach, not a weakness, as long as you explain it in your viva.

---

## Step 5: Product Lifecycle Analysis (4–5 hrs)

1. Group sales by product and time period (weekly or monthly).
2. Calculate the **trend**: is sales volume increasing, flat, or decreasing over the last few periods? (a simple rolling average or % change between periods is enough — you don't need anything fancier).
3. Map trend + sales magnitude to a stage using rules:
   - Rising sharply, new product → **Emerging**
   - Rising steadily → **Growing**
   - High and stable → **Peak**
   - Falling → **Declining**
   - Very low sales + low velocity → **Slow-Moving**
4. Visualize a few example products' sales-over-time curves to sanity check your stage labels make sense.

---

## Step 6: Channel / Location Performance Analysis (4–6 hrs)

This one's the most straightforward — mostly `groupby` and aggregation:

1. Group by `channel` and `location`, sum `quantity_sold` and revenue (`price × quantity_sold`).
2. Compare average sell-through rate and risk distribution per channel/location.
3. Identify best and weakest performing channel/location combos — these become part of your Business Insights in Step 9.

---

## Step 7: Smart Discount Engine (4–5 hrs)

Build this as a **decision table / rule function**, not a black-box model — it needs to be explainable to a shop owner.

Example logic to adapt:
- High risk + Declining/Slow-moving + high stock coverage → **30%**
- High/Medium risk + Peak or Growing (still has demand) → **10–20%**
- Low risk → **0%**

Write it as a function `recommend_discount(risk, lifecycle_stage, stock_coverage)` that returns 0/10/20/30. Test it against several rows manually to make sure the logic feels sensible before wiring it into the dashboard.

---

## Step 8: Streamlit Dashboard (8–10 hrs — budget the most time here)

Structure it in layers, don't try to build it all at once:

1. **Load data** → get the full pipeline output (cleaned + featured + risk + lifecycle + discount) into one dataframe. Consider storing this in **SQLite** so the dashboard reads from a database rather than re-running the pipeline every time (matches your tech stack).
2. **Sidebar filters**: category, channel, location, date range (`st.sidebar.multiselect`, `st.sidebar.date_input`).
3. **KPI cards** at top: total sales, total stock value, % slow-moving products (`st.columns` + `st.metric`).
4. **Charts** (use Plotly for interactivity): risk distribution pie chart, lifecycle stage bar chart, channel/location comparison bar chart.
5. **Product-level table**: filterable table showing each product's risk, lifecycle stage, and recommended discount (`st.dataframe`).

Build and test each piece separately before combining — a dashboard that breaks silently is hard to debug.

---

## Step 9: Business Insights & Recommendations (3–4 hrs)

This is auto-generated text, not another model. Write template-based logic:
- `"X% of products in [category] are High risk — consider promotion."`
- `"[Channel] is underperforming with only Y% of total sales."`

Loop through your aggregated results and fill in these templates conditionally. Display them in the dashboard as a bullet list or a dedicated "Insights" tab.

---

## Step 10: Owner Decision & Action (1–2 hrs)

For the project demo, this can be as simple as an **"Approve" button** in Streamlit next to each recommendation (`st.button`), which just marks a row as approved in your session state or SQLite table. It doesn't need real business logic behind it — its job in the demo is to show the human-in-the-loop closing the system.

---

## Suggested day-wise plan (2-member team, ~6 working days)

| Day | Member A | Member B |
|---|---|---|
| 1 | Data collection + cleaning (Steps 1–2) | Set up SQLite schema, project structure |
| 2 | Feature engineering (Step 3) | Start risk model (Step 4) alongside A |
| 3 | Finish risk model (Step 4) | Lifecycle analysis (Step 5) |
| 4 | Channel/location analysis (Step 6) | Discount engine (Step 7) |
| 5–6 | Streamlit dashboard (Step 8) — split by section (filters/KPIs vs charts/tables) | Same |
| 6–7 | Business insights + owner action (Steps 9–10), polish, report, screenshots | Same |

---

## Before your viva

- Keep a short daily log of what you built — this becomes your project report's "methodology" section almost for free.
- Be ready to explain **why** you chose your risk thresholds and discount rules, not just what they are — examiners probe the reasoning, not just the output.
- Have 2–3 example products memorized end-to-end (raw data → features → risk → discount) that you can walk through live if asked.
- Mention the 8th-semester extensions (demand forecasting, discount optimization, real-time data) as your "future scope" slide — you already have this written on your architecture diagram.

## Final checklist (matches your diagram's "Final Output")

- [ ] Slow-moving products list
- [ ] Risk prediction (Low/Medium/High) working end-to-end
- [ ] Product lifecycle stage per product
- [ ] Channel/location performance comparison
- [ ] Discount recommendation per product
- [ ] Interactive Streamlit dashboard
- [ ] Business insights auto-generated and displayed
