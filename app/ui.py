import streamlit as st
import pandas as pd
import ITR
from ITR.data.excel import ExcelProvider
from ITR.portfolio_aggregation import PortfolioAggregationMethod
from ITR.portfolio_coverage_tvp import PortfolioCoverageTVP
from ITR.temperature_score import TemperatureScore
from ITR.interfaces import ETimeFrames, EScope
from io import BytesIO
from importlib import resources
import os
from pathlib import Path
import importlib
# --- Streamlit Page Config ---
st.set_page_config(page_title="WWF ITR Calculator", layout="wide")

# --- Hero banner: text (left) and ITR-logo.png (right) ---
banner_path = None
# Resolve icon (prefer bundled app/static/panda.jpg, fallback to emoji)
icon_path = None
try:
    res = resources.files("app").joinpath("static/panda.jpeg")
    if res.exists():
        with resources.as_file(res) as p:
            icon_path = str(p)
except Exception:
    icon_path = None

st.set_page_config(
    page_title="WWF ITR Calculator",
    page_icon=icon_path if icon_path and os.path.exists(icon_path) else "🌍",
    layout="wide"
)

# 1) Try package resources inside this UI package ("app")
try:
    banner_res = resources.files("app").joinpath("static/ITR-logo.png")
    if banner_res.exists():
        with resources.as_file(banner_res) as p:
            banner_path = str(p)
except Exception:
    banner_path = None

# 2) Fallback: local file path relative to this module (development)
if not banner_path:
    local_path = Path(__file__).resolve().parent.joinpath("static", "ITR-logo.png")
    if local_path.exists():
        banner_path = str(local_path)

col_text, col_img = st.columns([3, 1])
with col_text:
    st.markdown(
        """
        <div style="padding: 0.5rem 1rem;">
          <h1 style="margin:0; font-size:28px;">🌍 WWF ITR Temperature Score Calculator</h1>
          <p style="margin:0.35rem 0 0; color:#444; font-size:16px;">
            Easily calculate portfolio temperature scores using your data provider and portfolio files.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_img:
    if banner_path and os.path.exists(banner_path):
        st.image(banner_path, use_container_width=True)
    else:
        st.empty()

# st.title("🌍 WWF ITR Temperature Score Calculator")
# st.write("Upload your **Data Provider** Excel file and **Portfolio** CSV file to calculate temperature scores.")

# --- File uploads ---
col1, col2 = st.columns(2)
with col1:
    provider_file = st.file_uploader("📄 Data Provider file (.xlsx)", type=["xlsx"])
with col2:
    portfolio_file = st.file_uploader("📄 Portfolio file (.csv)", type=["csv"])

# --- Parameter selection ---
with st.expander("⚙️ Calculation Settings"):
    agg_method = st.selectbox(
        "Aggregation Method",
        options=list(PortfolioAggregationMethod),
        format_func=lambda x: x.name
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

# --- Run calculation ---
if provider_file and portfolio_file:
    try:
        provider = ExcelProvider(path=provider_file)
        df_portfolio = pd.read_csv(portfolio_file, encoding="iso-8859-1")

        st.subheader("Portfolio Preview")
        st.dataframe(df_portfolio.head())

        companies = ITR.utils.dataframe_to_portfolio(df_portfolio)

        temperature_score = TemperatureScore(
            time_frames=selected_timeframes,
            scopes=selected_scopes,
            aggregation_method=agg_method
        )
        amended_portfolio = temperature_score.calculate(
            data_providers=[provider],
            portfolio=companies
        )

        company_scores_df = amended_portfolio[['company_name', 'time_frame', 'scope', 'temperature_score']]

        aggregated_scores = temperature_score.aggregate_scores(amended_portfolio)
        aggregated_df = pd.DataFrame(aggregated_scores.dict()).apply(
            lambda x: x.map(
                lambda y: round(y['all']['score'], 2) if y and y['all'] and 'score' in y['all'] else None
            )
        )

        portfolio_coverage_tvp = PortfolioCoverageTVP()
        coverage = portfolio_coverage_tvp.get_portfolio_coverage(
            amended_portfolio.copy(),
            agg_method
        )

        # --- Tabs for results ---
        tab1, tab2, tab3 = st.tabs(["🏢 Company Scores", "📊 Aggregated Scores", "📈 Portfolio Coverage"])

        with tab1:
            st.dataframe(company_scores_df)

        with tab2:
            st.dataframe(aggregated_df)

        with tab3:
            st.metric(label="Portfolio Coverage (%)", value=f"{coverage:.2f}")

        # --- Download results ---
        def to_excel_bytes(df_dict):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for sheet_name, df in df_dict.items():
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
            return output.getvalue()

        excel_bytes = to_excel_bytes({
            "Company Scores": company_scores_df,
            "Aggregated Scores": aggregated_df
        })

        st.download_button(
            label="📥 Download Results as Excel",
            data=excel_bytes,
            file_name="wwf_itr_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload both the Data Provider Excel file and Portfolio CSV file to start.")


