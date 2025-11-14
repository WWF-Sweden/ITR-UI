"""
Main Streamlit UI for the ITR-UI package.

Keep this file focused on layout and wiring. Heavy logic lives in app/actions.py
and layout helpers live in app/layout.py.
"""
import sys
from pathlib import Path
# Ensure project root is on sys.path so "app" can be imported when running the script directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
import base64
from pathlib import Path
from io import BytesIO

import streamlit as st
import pandas as pd

from app.layout import get_icon_path, render_hero, get_local_asset
from app.actions import run_calculation

# ITR enums used for selectors
import ITR
from ITR.portfolio_aggregation import PortfolioAggregationMethod
from ITR.interfaces import ETimeFrames, EScope


# --- Page config (must be first Streamlit call) ---
icon_path = get_icon_path()
st.set_page_config(
    page_title="WWF ITR Calculator",
    page_icon=icon_path if icon_path and os.path.exists(icon_path) else "🌍",
    layout="wide",
)

# --- Hero banner ---
banner_path = get_local_asset("app", "static/ITR-logo.png")
render_hero(
    title="WWF ITR Temperature Score Calculator",
    subtitle="Easily calculate portfolio temperature scores using your data provider and portfolio files.",
    img_path=banner_path,
)

# --- File uploads ---
col1, col2 = st.columns(2)
with col1:
    provider_file = st.file_uploader(
        "📄 Data Provider file (.xlsx)",
        type=["xlsx"],
        key="provider_uploader",
        help="Upload the Excel file from your data provider."
    )
with col2:
    portfolio_file = st.file_uploader(
        "📄 Portfolio file (.csv)",
        type=["csv"],
        key="portfolio_uploader",
        help="Upload a CSV with your portfolio (ticker/identifier + weight)."
    )

# --- Calculation settings ---
with st.expander("⚙️ Calculation Settings", expanded=False):
    agg_method = st.selectbox(
        "Aggregation Method",
        options=list(PortfolioAggregationMethod),
        format_func=lambda x: x.name,
        index=0,
    )
    selected_scopes = st.multiselect(
        "Scopes",
        options=list(EScope),
        default=[EScope.S1, EScope.S2, EScope.S1S2, EScope.S3, EScope.S1S2S3],
        format_func=lambda x: x.name
    )
    selected_timeframes = st.multiselect(
        "Time Frames",
        options=list(ETimeFrames),
        default=list(ETimeFrames),
        format_func=lambda x: x.name
    )

# --- Run control (use session_state to trigger and reset) ---
if "run_now" not in st.session_state:
    st.session_state.run_now = False

if st.button("Run calculation", key="run_btn"):
    st.session_state.run_now = True

if st.session_state.run_now:
    if not (provider_file and portfolio_file):
        st.info("Please upload both the Data Provider Excel file and Portfolio CSV file to start.")
    else:
        try:
            with st.spinner("Calculating…"):
                company_scores_df, aggregated_df, coverage, excel_bytes = run_calculation(
                    provider_file,
                    portfolio_file,
                    selected_timeframes,
                    selected_scopes,
                    agg_method,
                )

            st.subheader("Portfolio Preview")
            st.dataframe(company_scores_df.head())

            tab1, tab2, tab3 = st.tabs(["🏢 Company Scores", "📊 Aggregated Scores", "📈 Portfolio Coverage"])
            with tab1:
                st.dataframe(company_scores_df)
            with tab2:
                st.dataframe(aggregated_df)
            with tab3:
                st.metric(label="Portfolio Coverage (%)", value=f"{coverage:.2f}")

            st.download_button(
                label="📥 Download Results as Excel",
                data=excel_bytes,
                file_name="wwf_itr_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            # reset flag so it doesn't auto-run on the next interaction
            st.session_state.run_now = False
else:
    st.info("Upload files and press 'Run calculation' to compute temperature scores.")
