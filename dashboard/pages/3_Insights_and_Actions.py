"""ThreadSense AI — Insights & Actions page: Step 9 (auto-insights) + Step 10 (owner decisions)."""

import os
import sqlite3
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.insert(0, "dashboard")
from utils import DECISIONS_DB_PATH, get_active_data  # noqa: E402

st.set_page_config(page_title="Insights & Actions - ThreadSense AI", layout="wide")

df = get_active_data()

st.title("Insights & Actions")

# =================================================================
# STEP 9 — Auto-generated business insights
# =================================================================
st.header("Business Insights")

high_risk_pct = (df["Slow_Moving_Risk"] == "High Risk").mean() * 100

cat_risk = df.groupby("Category")["Slow_Moving_Risk"].apply(lambda s: (s == "High Risk").mean() * 100)
worst_category = cat_risk.idxmax()

channel_risk = df.groupby("Channel")["Slow_Moving_Risk"].apply(lambda s: (s == "High Risk").mean() * 100)
worst_channel = channel_risk.idxmax()

capital_at_risk = df.loc[df["Slow_Moving_Risk"] == "High Risk", "Capital_At_Risk"].sum()

top_channel_rev = df.groupby("Channel")["Revenue_30D_INR"].sum()
best_channel = top_channel_rev.idxmax()

insights = [
    f"**{high_risk_pct:.0f}%** of all products are currently High Risk for slow-moving stock.",
    f"**{worst_category}** has the highest concentration of High Risk products, at **{cat_risk.max():.0f}%** of that category.",
    f"**{worst_channel}** is the weakest-performing channel by risk share, at **{channel_risk.max():.0f}%** High Risk.",
    f"**₹{capital_at_risk:,.0f}** of capital is currently locked in High Risk stock across all products.",
    f"**{best_channel}** remains the strongest revenue channel, generating **₹{top_channel_rev.max():,.0f}** in 30-day revenue.",
]

for insight in insights:
    st.markdown(f"- {insight}")

st.divider()

# =================================================================
# STEP 10 — Owner decision panel
# =================================================================
st.header("Owner Decisions")
st.caption("Review flagged products and approve, reject, or hold the recommended action. Decisions are saved permanently.")


def get_db_connection():
    os.makedirs(os.path.dirname(DECISIONS_DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DECISIONS_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            Product_ID TEXT PRIMARY KEY,
            Product_Name TEXT,
            Recommended_Discount_Pct INTEGER,
            Decision TEXT,
            Decided_At TEXT
        )
        """
    )
    conn.commit()
    return conn


conn = get_db_connection()

only_flagged = st.checkbox("Show only High/Medium Risk products", value=True)
review_pool = df[df["Slow_Moving_Risk"] != "Low Risk"] if only_flagged else df

selected_id = st.selectbox("Select a product to review", review_pool["Product_ID"].tolist())
selected_row = df[df["Product_ID"] == selected_id].iloc[0]

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Product:** {selected_row['Product_Name']}")
    st.write(f"**Category:** {selected_row['Category']}  |  **Channel:** {selected_row['Channel']}")
    st.write(f"**Risk:** {selected_row['Slow_Moving_Risk']}  |  **Lifecycle Stage:** {selected_row['Lifecycle_Stage']}")
with col2:
    st.write(f"**Recommended Discount:** {selected_row['Custom_Discount_Pct']}%")
    st.write(f"**Recommended Action:** {selected_row['Recommended_Action']}")

existing = pd.read_sql(
    "SELECT Decision, Decided_At FROM decisions WHERE Product_ID = ?", conn, params=(selected_id,)
)
if not existing.empty:
    st.info(f"Current decision: **{existing.iloc[0]['Decision']}** (on {existing.iloc[0]['Decided_At']})")

b1, b2, b3 = st.columns(3)


def record_decision(decision):
    conn.execute(
        """
        INSERT OR REPLACE INTO decisions (Product_ID, Product_Name, Recommended_Discount_Pct, Decision, Decided_At)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            selected_id,
            selected_row["Product_Name"],
            int(selected_row["Custom_Discount_Pct"]),
            decision,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    st.rerun()


if b1.button("✅ Approve", use_container_width=True):
    record_decision("Approved")
if b2.button("❌ Reject", use_container_width=True):
    record_decision("Rejected")
if b3.button("⏸️ Hold", use_container_width=True):
    record_decision("Hold")

st.divider()

# ---------------------------------------------------------------
# Decision log
# ---------------------------------------------------------------
st.subheader("Decision Log")

log_df = pd.read_sql("SELECT * FROM decisions ORDER BY Decided_At DESC", conn)

if log_df.empty:
    st.write("No decisions recorded yet.")
else:
    st.dataframe(log_df, use_container_width=True)
    csv_out = log_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download decision log", csv_out, "decision_log.csv", "text/csv")

conn.close()
