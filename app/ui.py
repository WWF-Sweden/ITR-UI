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
from app.actions import run_calculation, run_grouped_calculation

# ITR enums used for selectors
import ITR
from ITR.portfolio_aggregation import PortfolioAggregationMethod
from ITR.interfaces import ETimeFrames, EScope
from app.charts import render_charts


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

# Run calculation if button clicked
if st.session_state.run_now:
    if not (provider_file and portfolio_file):
        st.info("Please upload both the Data Provider Excel file and Portfolio CSV file to start.")
    else:
        try:
            with st.spinner("Calculating…"):
                results = run_calculation(
                    provider_file,
                    portfolio_file,
                    selected_timeframes,
                    selected_scopes,
                    agg_method,
                    return_intermediates=True,
                )
                company_scores_df, aggregated_df, coverage, excel_bytes, provider, companies, amended_portfolio = results
                
                # Store ALL data in session state for persistence across reruns
                st.session_state.provider = provider
                st.session_state.companies = companies
                st.session_state.amended_portfolio = amended_portfolio
                st.session_state.selected_timeframes = selected_timeframes
                st.session_state.selected_scopes = selected_scopes
                st.session_state.agg_method = agg_method
                st.session_state.company_scores_df = company_scores_df
                st.session_state.aggregated_df = aggregated_df
                st.session_state.coverage = coverage
                st.session_state.excel_bytes = excel_bytes
                st.session_state.calculation_complete = True
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            # reset flag so it doesn't auto-run on the next interaction
            st.session_state.run_now = False

# Display results if calculation has been completed
if st.session_state.get("calculation_complete", False):

            st.subheader("Portfolio Preview")
            st.dataframe(st.session_state.company_scores_df.head())

            tab1, tab2, tab3, tab4 = st.tabs(["🏢 Company Scores", "📊 Aggregated Scores", "📈 Portfolio Coverage", "📊 Charts"])
            with tab1:
                st.dataframe(st.session_state.company_scores_df)
            with tab2:
                st.dataframe(st.session_state.aggregated_df)
            with tab3:
                st.metric(label="Portfolio Coverage (%)", value=f"{st.session_state.coverage:.2f}")
            with tab4:
                # --- Chart Configuration ---
                with st.expander("📊 Chart Settings", expanded=True):
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        chart_type = st.selectbox(
                            "Chart Type",
                            options=["Bar Chart", "Scatter Plot", "Heatmap", "Line Chart"],
                            help="Select the type of chart to display"
                        )
                        show_labels = st.checkbox("Show Data Labels", value=True)
                    with chart_col2:
                        color_scheme = st.selectbox(
                            "Color Scheme",
                            options=["Default", "Viridis", "Plasma", "Coolwarm", "Temperature"],
                            help="Select color palette for the charts"
                        )
                        filter_threshold = st.slider(
                            "Temperature Threshold",
                            min_value=0.0,
                            max_value=5.0,
                            value=2.0,
                            step=0.1,
                            help="Filter companies above this temperature score"
                        )
                
                # Grouping parameters for Heatmap
                group_1 = None
                group_2 = None
                heatmap_timeframe = None
                heatmap_scope = None
                
                if chart_type == "Heatmap":
                    with st.expander("🔧 Heatmap Grouping Settings", expanded=True):
                        grouping_col1, grouping_col2 = st.columns(2)
                        with grouping_col1:
                            group_1 = st.selectbox(
                                "Primary Grouping",
                                options=["sector", "region", "industry"],
                                help="First dimension for the heatmap"
                            )
                        with grouping_col2:
                            group_2 = st.selectbox(
                                "Secondary Grouping",
                                options=["region", "sector", "industry"],
                                index=1,
                                help="Second dimension for the heatmap"
                            )
                        
                        heatmap_timeframe = st.selectbox(
                            "Time Frame for Heatmap",
                            options=st.session_state.selected_timeframes,
                            format_func=lambda x: x.name,
                            help="Select which time frame to display"
                        )
                        heatmap_scope = st.selectbox(
                            "Scope for Heatmap",
                            options=st.session_state.selected_scopes,
                            format_func=lambda x: x.name,
                            help="Select which scope to display"
                        )
                
                if st.button("Generate Charts", key="generate_charts_btn"):
                    # --- Grouped calculation for heatmap ---
                    grouped_aggregations = None
                    if chart_type == "Heatmap":
                        if group_1 == group_2:
                            st.error("Primary and Secondary grouping must be different!")
                        else:
                            with st.spinner("Calculating grouped aggregations for heatmap..."):
                                grouping = [group_1, group_2]
                                _, grouped_aggregations = run_grouped_calculation(
                                    st.session_state.provider,
                                    st.session_state.companies,
                                    [heatmap_timeframe],
                                    [heatmap_scope],
                                    st.session_state.agg_method,
                                    grouping
                                )
                    
                    # --- Diagram generation ---
                    render_charts(
                        st.session_state.company_scores_df, 
                        st.session_state.aggregated_df, 
                        st.session_state.coverage,
                        chart_type=chart_type,
                        color_scheme=color_scheme,
                        show_labels=show_labels,
                        threshold=filter_threshold,
                        grouped_aggregations=grouped_aggregations,
                        analysis_parameters=([heatmap_timeframe], [heatmap_scope], [group_1, group_2]) if chart_type == "Heatmap" else None
                    )
            st.download_button(
                label="📥 Download Results as Excel",
                data=st.session_state.excel_bytes,
                file_name="wwf_itr_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
else:
    st.info("Upload files and press 'Run calculation' to compute temperature scores.")
