"""
ThreadSense AI — Retail Intelligence Dashboard
Step 8: Streamlit Dashboard & Visualization

Run locally with: streamlit run dashboard/app.py
(run this command from the ThreadSense-AI project root folder)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="ThreadSense AI Dashboard", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_excel("data/processed/jak_threads_discount_engine.xlsx")
    df["Revenue_30D_INR"] = df["Units_Sold_30_Days"] * df["Selling_Price"]
    return df


df = load_data()

st.title("ThreadSense AI — Retail Intelligence Dashboard")
st.caption("JAK Threads | AI-Powered Retail Intelligence System")

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
