"""
ThreadSense AI — shared logic used by every dashboard page.
Not a page itself — imported by app.py and everything in pages/.
"""

import sys

import joblib
import pandas as pd
import streamlit as st

sys.path.insert(0, "src")
from feature_engineering import engineer_features  # noqa: E402

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

DECISIONS_DB_PATH = "data/decisions.db"


def assign_lifecycle_stage(row):
    """Own documented rule — original formula was unreproducible. See project log."""
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


def get_active_data() -> pd.DataFrame:
    """The single source of truth every page reads from. Set once per session
    from saved data; Data & Products page can overwrite it with an upload."""
    if "df" not in st.session_state:
        st.session_state["df"] = load_default_data()
        st.session_state["data_source"] = "default"
    return st.session_state["df"]
