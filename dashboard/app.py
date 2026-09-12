"""
ThreadSense AI — Retail Intelligence Dashboard
Step 8: Streamlit Dashboard & Visualization (+ live pipeline for fresh uploads)

Run locally with: streamlit run dashboard/app.py
(run this command from the ThreadSense-AI project root folder)
"""

import sys
from datetime import date

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, "src")
from feature_engineering import engineer_features  # noqa: E402

st.set_page_config(page_title="ThreadSense AI Dashboard", layout="wide")

FEATURE_COLS = [
    "Inventory_Age_Days", "Days_Since_Last_Sale", "Sales_Velocity_7D",
    "Sales_Velocity_30D", "Sell_Through_Rate", "Days_Of_Inventory",
    "Sales_Acceleration", "Gross_Margin_Pct", "Stock_to_Sales_Ratio",
]

REQUIRED_RAW_COLUMNS = [
    "Product_ID", "Product_Name", "Category", "Subcategory", "Style", "Color", "Size",
    "Cost_Price", "Selling_Price", "Current_Stock", "Launch_Date", "Last_Sale_Date",
    "Units_Sold_7_Days", "Units_Sold_30_Days", "Units_Sold_60_Days", "Units_Sold_90_Days",
    "Total_Units_Sold", "Previous_Discount", "Channel", "Location", "Season",
]


def assign_lifecycle_stage(row):
    """Own documented rule (original formula was unreproducible) — see project log."""
    if row["Slow_Moving_Risk"] == "High Risk":
        return "Slow-Moving"
    elif row["Inventory_Age_Days"] <= 30:
        return "Emerging"
    elif row["Sales_Acceleration"] > 0.2:
        return "Growing"
    elif row["Sell_Through_Rate"] >= 0.65:
        return "Peak"
    else:
        return "Declining"


def assign_discount(row):
    """Custom discount rule from Step 7 — 88.4% agreement with original labels."""
    risk = row["Slow_Moving_Risk"]
    if risk == "Low Risk":
        return 0
    elif risk == "Medium Risk":
        return 10
    else:
        return 30 if row["Days_Since_Last_Sale"] > 30 else 20


@st.cache_resource
def load_model():
    return joblib.load("models/risk_classifier.pkl")


def run_pipeline(raw_df: pd.DataFrame, snapshot_date, model) -> pd.DataFrame:
    """Raw sales/stock data in -> fully enriched, dashboard-ready data out."""
    df = engineer_features(raw_df, snapshot_date=str(snapshot_date))
    df["Slow_Moving_Risk"] = model.predict(df[FEATURE_COLS])
    df["Lifecycle_Stage"] = df.apply(assign_lifecycle_stage, axis=1)
    df["Custom_Discount_Pct"] = df.apply(assign_discount, axis=1)
    df["Discounted_Price"] = (df["Selling_Price"] * (1 - df["Custom_Discount_Pct"] / 100)).round(2)
    df["Capital_At_Risk"] = (df["Current_Stock"] * df["Cost_Price"]).round(2)
    df["Recommended_Action"] = df["Custom_Discount_Pct"].apply(
        lambda d: "Hold — performing well" if d == 0
        else f"Apply {d}% discount to improve sell-through"
    )
    df["Revenue_30D_INR"] = df["Units_Sold_30_Days"] * df["Selling_Price"]
    return df


@st.cache_data
def load_default_data():
    df = pd.read_excel("data/processed/jak_threads_discount_engine.xlsx")
    df["Revenue_30D_INR"] = df["Units_Sold_30_Days"] * df["Selling_Price"]
    return df


st.title("ThreadSense AI — Retail Intelligence Dashboard")
st.caption("JAK Threads | AI-Powered Retail Intelligence System")

# ---------------------------------------------------------------
# Upload fresh data (runs the full live pipeline) or use saved data
# ---------------------------------------------------------------
st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload fresh raw sales & stock data", type=["csv", "xlsx"]
)
snapshot_date = st.sidebar.date_input("Data as of date", value=date.today())

if uploaded_file is not None:
    raw_df = (
        pd.read_csv(uploaded_file)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file)
    )
    missing_cols = set(REQUIRED_RAW_COLUMNS) - set(raw_df.columns)
    if missing_cols:
        st.error(f"Uploaded file is missing required columns: {sorted(missing_cols)}")
        st.stop()

    model = load_model()
    df = run_pipeline(raw_df, snapshot_date, model)
    st.sidebar.success(f"Processed {len(df)} products from your upload.")

    csv_out = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        "Download processed results", csv_out, "processed_results.csv", "text/csv"
    )
else:
    df = load_default_data()
    st.sidebar.info("Using saved data. Upload a file above to analyze fresh data instead.")

# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.header("Filters")

categories = st.sidebar.multiselect(
    "Category", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
)
channels = st.sidebar.multiselect(
    "Channel", sorted(df["Channel"].unique()), default=sorted(df["Channel"].unique())
)
locations = st.sidebar.multiselect(
    "Location", sorted(df["Location"].unique()), default=sorted(df["Location"].unique())
)
risk_levels = st.sidebar.multiselect(
    "Risk Level", sorted(df["Slow_Moving_Risk"].unique()), default=sorted(df["Slow_Moving_Risk"].unique())
)
lifecycle_stages = st.sidebar.multiselect(
    "Lifecycle Stage", sorted(df["Lifecycle_Stage"].unique()), default=sorted(df["Lifecycle_Stage"].unique())
)

filtered = df[
    df["Category"].isin(categories)
    & df["Channel"].isin(channels)
    & df["Location"].isin(locations)
    & df["Slow_Moving_Risk"].isin(risk_levels)
    & df["Lifecycle_Stage"].isin(lifecycle_stages)
]

if filtered.empty:
    st.warning("No products match the current filters. Adjust your selections in the sidebar.")
    st.stop()

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total SKUs", f"{len(filtered):,}")
col2.metric("Total Stock Value", f"₹{(filtered['Current_Stock'] * filtered['Cost_Price']).sum():,.0f}")
col3.metric("Total 30D Revenue", f"₹{filtered['Revenue_30D_INR'].sum():,.0f}")
high_risk_pct = (filtered["Slow_Moving_Risk"] == "High Risk").mean() * 100
col4.metric("% High Risk", f"{high_risk_pct:.1f}%")

st.divider()

# ---------------------------------------------------------------
# Charts row 1: Risk + Lifecycle distribution
# ---------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    risk_counts = filtered["Slow_Moving_Risk"].value_counts().reset_index()
    risk_counts.columns = ["Risk", "Count"]
    fig = px.bar(risk_counts, x="Risk", y="Count", title="Risk Distribution", color="Risk")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    lifecycle_counts = filtered["Lifecycle_Stage"].value_counts().reset_index()
    lifecycle_counts.columns = ["Stage", "Count"]
    fig2 = px.bar(lifecycle_counts, x="Stage", y="Count", title="Lifecycle Stage Distribution", color="Stage")
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------
# Charts row 2: Channel + Location revenue
# ---------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    channel_rev = filtered.groupby("Channel")["Revenue_30D_INR"].sum().reset_index()
    fig3 = px.bar(channel_rev, x="Channel", y="Revenue_30D_INR", title="Revenue by Channel")
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    location_rev = filtered.groupby("Location")["Revenue_30D_INR"].sum().reset_index()
    fig4 = px.bar(location_rev, x="Location", y="Revenue_30D_INR", title="Revenue by Location")
    st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------------------
# Discount tier distribution
# ---------------------------------------------------------------
discount_counts = filtered["Custom_Discount_Pct"].value_counts().sort_index().reset_index()
discount_counts.columns = ["Discount_Pct", "Count"]
fig5 = px.bar(
    discount_counts,
    x=discount_counts["Discount_Pct"].astype(str),
    y="Count",
    title="Discount Tier Distribution",
)
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ---------------------------------------------------------------
# Product-level table
# ---------------------------------------------------------------
st.subheader("Product-Level Detail")

search = st.text_input("Search by Product ID or Name")

table_df = filtered[
    [
        "Product_ID",
        "Product_Name",
        "Category",
        "Channel",
        "Location",
        "Slow_Moving_Risk",
        "Lifecycle_Stage",
        "Custom_Discount_Pct",
        "Recommended_Action",
    ]
]

if search:
    table_df = table_df[
        table_df["Product_ID"].str.contains(search, case=False, na=False)
        | table_df["Product_Name"].str.contains(search, case=False, na=False)
    ]

st.dataframe(table_df, use_container_width=True, height=400)
