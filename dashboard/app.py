"""
ThreadSense AI — Retail Intelligence Dashboard (Home)

Run locally with: streamlit run dashboard/app.py
(run this command from the ThreadSense-AI project root folder)

This is a 3-page app. Streamlit auto-detects the pages/ folder next to this
file and builds the sidebar navigation automatically — no extra setup needed.
"""

import sys

import streamlit as st

sys.path.insert(0, "dashboard")
from utils import get_active_data  # noqa: E402

st.set_page_config(page_title="ThreadSense AI Dashboard", layout="wide")

df = get_active_data()

st.title("ThreadSense AI — Retail Intelligence Dashboard")
st.caption("JAK Threads | AI-Powered Retail Intelligence System")

st.markdown(
    """
    Use the sidebar to navigate between pages:

    - **Overview** — KPIs and distribution charts, with filters
    - **Data & Products** — upload fresh sales data, or search individual products
    - **Insights & Actions** — auto-generated business insights and the owner decision panel
    """
)

st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total SKUs", f"{len(df):,}")
col2.metric("Total Stock Value", f"₹{(df['Current_Stock'] * df['Cost_Price']).sum():,.0f}")
col3.metric("Total 30D Revenue", f"₹{df['Revenue_30D_INR'].sum():,.0f}")
high_risk_pct = (df["Slow_Moving_Risk"] == "High Risk").mean() * 100
col4.metric("% High Risk", f"{high_risk_pct:.1f}%")

source_label = "your uploaded file" if st.session_state.get("data_source") == "uploaded" else "saved data"
st.caption(f"Currently showing: {source_label} ({len(df)} products)")
