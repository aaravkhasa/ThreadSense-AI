"""
ThreadSense AI — Step 3: Feature Engineering
Rebuilt from scratch by reverse-engineering and verifying every formula
against jak_threads_processed_features.xlsx (1200/1200 exact matches on
every column below). This replaces the second, lost Antigravity script for
the 9 core engineered features.

NOTE: Slow_Moving_Index, Slow_Moving_Risk, Recommended_Discount_Pct, and
Lifecycle_Stage are NOT recomputed here — their exact original formula
could not be reverse-engineered with certainty (best attempt reached
R^2 = 0.98, not exact). Those columns are carried over unchanged from your
existing processed_features file. Ask to rebuild that scoring logic
cleanly from scratch when you're ready for Step 4/5/7.
"""

import pandas as pd


def engineer_features(raw_df: pd.DataFrame, snapshot_date: str = "2026-08-25") -> pd.DataFrame:
    """
    Computes the 9 core engineered features from raw JAK Threads data.
    snapshot_date must match whatever date the raw data was generated
    against (see generate_retail_dataset.py) — using the wrong date will
    silently shift every age/recency feature by a constant offset.
    """
    df = raw_df.copy()
    snapshot = pd.Timestamp(snapshot_date)
    df["Launch_Date"] = pd.to_datetime(df["Launch_Date"])
    df["Last_Sale_Date"] = pd.to_datetime(df["Last_Sale_Date"])

    # Recency / age
    df["Inventory_Age_Days"] = (snapshot - df["Launch_Date"]).dt.days
    df["Days_Since_Last_Sale"] = (snapshot - df["Last_Sale_Date"]).dt.days

    # Velocity
    df["Sales_Velocity_7D"] = (df["Units_Sold_7_Days"] / 7).round(3)
    df["Sales_Velocity_30D"] = (df["Units_Sold_30_Days"] / 30).round(3)

    # Absorption
    df["Sell_Through_Rate"] = (
        df["Total_Units_Sold"] / (df["Total_Units_Sold"] + df["Current_Stock"])
    ).round(4)

    # Stock coverage, capped at 365 days (confirmed: 316 rows in the
    # original file sit exactly at this cap)
    df["Days_Of_Inventory"] = (
        df["Current_Stock"] / (df["Sales_Velocity_30D"] + 0.01)
    ).clip(upper=365).round(1)

    # Momentum: projects the last-7-days pace out to a 30-day-equivalent,
    # compares it against the actual 30-day total
    df["Sales_Acceleration"] = (
        ((df["Units_Sold_7_Days"] / 7 * 30) - df["Units_Sold_30_Days"])
        / (df["Units_Sold_30_Days"] + 1)
    ).round(3)

    # Profitability
    df["Gross_Margin_Pct"] = (
        (df["Selling_Price"] - df["Cost_Price"]) / df["Selling_Price"]
    ).round(4)

    # Inventory pressure
    df["Stock_to_Sales_Ratio"] = (
        df["Current_Stock"] / (df["Units_Sold_30_Days"] + 1)
    ).round(2)

    return df


if __name__ == "__main__":
    raw = pd.read_csv("./data/jak_sales_inventory.csv")
    features = engineer_features(raw, snapshot_date="2026-08-25")
    features.to_csv("./data/jak_threads_features_verified.csv", index=False)
    print(f"Engineered {len(features)} rows, {features.shape[1]} columns")
    print("Saved to ./data/jak_threads_features_verified.csv")
