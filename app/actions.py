"""
Pure actions that run ITR calculations. Keep Streamlit-free so these functions are
unit-testable and reusable from ui.py.
"""
from io import BytesIO
from typing import Tuple, Dict
import pandas as pd

import ITR
from ITR.data.excel import ExcelProvider
from ITR.temperature_score import TemperatureScore
from ITR.portfolio_coverage_tvp import PortfolioCoverageTVP
from ITR.portfolio_aggregation import PortfolioAggregationMethod
from ITR.interfaces import ETimeFrames, EScope


def run_calculation(
    provider_file,
    portfolio_file,
    selected_timeframes: list[ETimeFrames],
    selected_scopes: list[EScope],
    agg_method: PortfolioAggregationMethod,
) -> Tuple[pd.DataFrame, pd.DataFrame, float, bytes]:
    """
    Run the temperature score calculation and return:
    (company_scores_df, aggregated_df, coverage, excel_bytes)

    - provider_file: path-like or file-like accepted by ExcelProvider
    - portfolio_file: path-like or file-like accepted by pd.read_csv
    """
    # provider (ExcelProvider accepts path or file-like)
    provider = ExcelProvider(path=provider_file)

    # read portfolio
    df_portfolio = pd.read_csv(portfolio_file, encoding="iso-8859-1")

    # preview -> convert to internal portfolio representation
    companies = ITR.utils.dataframe_to_portfolio(df_portfolio)

    # compute temperature scores
    temperature_score = TemperatureScore(
        time_frames=selected_timeframes,
        scopes=selected_scopes,
        aggregation_method=agg_method,
    )
    amended_portfolio = temperature_score.calculate(
        data_providers=[provider],
        portfolio=companies
    )

    # company-level scores
    company_scores_df = amended_portfolio[['company_name', 'time_frame', 'scope', 'temperature_score']]

    # aggregated scores (convert the nested dict to a DataFrame of rounded scores)
    aggregated_scores = temperature_score.aggregate_scores(amended_portfolio)
    aggregated_df = pd.DataFrame(aggregated_scores.dict()).apply(
        lambda x: x.map(
            lambda y: round(y['all']['score'], 2) if y and y.get('all') and 'score' in y['all'] else None
        )
    )

    # portfolio coverage
    portfolio_coverage_tvp = PortfolioCoverageTVP()
    coverage = portfolio_coverage_tvp.get_portfolio_coverage(
        amended_portfolio.copy(),
        agg_method
    )

    # prepare Excel bytes for download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        company_scores_df.to_excel(writer, index=False, sheet_name="Company Scores")
        aggregated_df.to_excel(writer, index=False, sheet_name="Aggregated Scores")
    excel_bytes = output.getvalue()

    return company_scores_df, aggregated_df, coverage, excel_bytes