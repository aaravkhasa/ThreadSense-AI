"""ThreadSense AI — Data & Products page: upload fresh data, search products."""

import sys
from datetime import date

import pandas as pd
import streamlit as st

sys.path.insert(0, "dashboard")
from utils import REQUIRED_RAW_COLUMNS, get_active_data, load_model, run_pipeline  # noqa: E402

st.set_page_config(page_title="Data & Products - ThreadSense AI", layout="wide")

st.title("Data & Products")

# ---------------------------------------------------------------
# Upload fresh data — runs the full live pipeline
# ---------------------------------------------------------------
st.subheader("Upload Fresh Data")
st.caption("Upload raw sales & stock data (same columns as your original Step 1 file) to re-run the full pipeline live.")

uploaded_file = st.file_uploader("Upload raw sales & stock data", type=["csv", "xlsx"])
snapshot_date = st.date_input("Data as of date", value=date.today())

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
    processed_df = run_pipeline(raw_df, snapshot_date, model)
    st.session_state["df"] = processed_df
    st.session_state["data_source"] = "uploaded"
    st.success(f"Processed {len(processed_df)} products from your upload. This is now active on every page.")

    csv_out = processed_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download processed results", csv_out, "processed_results.csv", "text/csv")

st.divider()

# ---------------------------------------------------------------
# Product search table — always reflects the currently active data
# ---------------------------------------------------------------
df = get_active_data()
source_label = "your uploaded file" if st.session_state.get("data_source") == "uploaded" else "saved data"
st.caption(f"Currently showing: {source_label} ({len(df)} products)")

st.subheader("Product Search")
search = st.text_input("Search by Product ID or Name")

table_df = df[
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

st.dataframe(table_df, use_container_width=True, height=500)
