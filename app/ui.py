import streamlit as st
import pandas as pd
import ITR
from ITR.data.excel import ExcelProvider
from ITR.portfolio_aggregation import PortfolioAggregationMethod
from ITR.portfolio_coverage_tvp import PortfolioCoverageTVP
from ITR.temperature_score import TemperatureScore
from ITR.interfaces import ETimeFrames, EScope
from io import BytesIO

# --- Streamlit Page Config ---
st.set_page_config(page_title="WWF ITR Calculator", layout="wide")

st.title("🌍 WWF ITR Temperature Score Calculator")
st.write("Upload your **Data Provider** Excel file and **Portfolio** CSV file to calculate temperature scores.")

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


