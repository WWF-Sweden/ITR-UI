"""
Chart rendering functions for the ITR UI.
Adapted from utils.py to work with Streamlit.
"""
import pandas as pd
import numpy as np
import copy
import matplotlib.pyplot as plt
import matplotlib.cm
from cycler import cycler
import streamlit as st

from ITR.interfaces import ETimeFrames, EScope


def render_charts(
    company_scores_df,
    aggregated_df,
    coverage,
    chart_type="Bar Chart",
    color_scheme="Default",
    show_labels=True,
    threshold=2.0,
    grouped_aggregations=None,
    analysis_parameters=None
):
    """
    Main chart rendering function for Streamlit UI.
    
    Args:
        company_scores_df: DataFrame with company-level scores
        aggregated_df: DataFrame with aggregated scores
        coverage: Portfolio coverage percentage
        chart_type: Type of chart to render
        color_scheme: Color palette to use
        show_labels: Whether to show data labels
        threshold: Temperature threshold for filtering
        grouped_aggregations: Grouped aggregations for heatmap (optional)
        analysis_parameters: Tuple of (timeframe, scope, grouping) for heatmap (optional)
    """
    # Filter data by threshold if needed
    filtered_df = company_scores_df[company_scores_df['temperature_score'] <= threshold]
    
    if chart_type == "Bar Chart":
        render_bar_chart(filtered_df, color_scheme, show_labels)
    elif chart_type == "Scatter Plot":
        render_scatter_plot(filtered_df, color_scheme, show_labels)
    elif chart_type == "Heatmap":
        if grouped_aggregations is None or analysis_parameters is None:
            st.error("Heatmap requires grouped aggregations. Please configure grouping parameters.")
        else:
            plot_grouped_heatmap(grouped_aggregations, analysis_parameters)
    elif chart_type == "Line Chart":
        render_line_chart(filtered_df, color_scheme, show_labels)
    else:
        st.warning(f"Chart type '{chart_type}' not yet implemented.")


def get_colormap(color_scheme):
    """Get matplotlib colormap from color scheme name."""
    colormap_mapping = {
        "Default": "tab10",
        "Viridis": "viridis",
        "Plasma": "plasma",
        "Coolwarm": "coolwarm",
        "Temperature": "OrRd"
    }
    return colormap_mapping.get(color_scheme, "tab10")


def render_bar_chart(df, color_scheme, show_labels):
    """Render a bar chart of temperature scores by company."""
    st.subheader("Temperature Scores by Company")
    
    # Group by company and take mean of temperature scores
    company_avg = df.groupby('company_name')['temperature_score'].mean().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(company_avg)), company_avg.values, color=plt.cm.get_cmap(get_colormap(color_scheme))(np.linspace(0, 1, len(company_avg))))
    
    ax.set_xticks(range(len(company_avg)))
    ax.set_xticklabels(company_avg.index, rotation=45, ha='right')
    ax.set_ylabel("Temperature Score (°C)")
    ax.set_title("Average Temperature Score by Company")
    ax.axhline(y=1.5, linestyle='--', color='k', label='1.5°C Target')
    ax.legend()
    
    if show_labels:
        for i, (bar, value) in enumerate(zip(bars, company_avg.values)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{value:.2f}', 
                   ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_scatter_plot(df, color_scheme, show_labels):
    """Render a scatter plot of temperature scores across time frames and scopes."""
    st.subheader("Temperature Scores Distribution")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create scatter plot with different colors for different scopes
    scopes = df['scope'].unique()
    cmap = plt.cm.get_cmap(get_colormap(color_scheme))
    colors = cmap(np.linspace(0, 1, len(scopes)))
    
    for i, scope in enumerate(scopes):
        scope_data = df[df['scope'] == scope]
        ax.scatter(scope_data.index, scope_data['temperature_score'], 
                  label=scope, alpha=0.6, s=100, color=colors[i])
    
    ax.set_xlabel("Data Point Index")
    ax.set_ylabel("Temperature Score (°C)")
    ax.set_title("Temperature Score Distribution by Scope")
    ax.axhline(y=1.5, linestyle='--', color='k', alpha=0.5, label='1.5°C Target')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_line_chart(df, color_scheme, show_labels):
    """Render a line chart showing temperature scores across time frames."""
    st.subheader("Temperature Scores by Time Frame")
    
    # Group by time_frame and scope
    grouped = df.groupby(['time_frame', 'scope'])['temperature_score'].mean().reset_index()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    scopes = grouped['scope'].unique()
    cmap = plt.cm.get_cmap(get_colormap(color_scheme))
    colors = cmap(np.linspace(0, 1, len(scopes)))
    
    for i, scope in enumerate(scopes):
        scope_data = grouped[grouped['scope'] == scope]
        ax.plot(scope_data['time_frame'], scope_data['temperature_score'], 
               marker='o', label=scope, color=colors[i], linewidth=2)
        
        if show_labels:
            for x, y in zip(scope_data['time_frame'], scope_data['temperature_score']):
                ax.text(x, y, f'{y:.2f}', fontsize=8, ha='center', va='bottom')
    
    ax.set_xlabel("Time Frame")
    ax.set_ylabel("Temperature Score (°C)")
    ax.set_title("Temperature Score Trends by Time Frame and Scope")
    ax.axhline(y=1.5, linestyle='--', color='k', alpha=0.5, label='1.5°C Target')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_heatmap_configuration(company_scores_df):
    """Render configuration UI for heatmap and generate it."""
    st.info("Heatmap visualization requires recalculating with grouping parameters. This feature will be added in the next update.")
    
    # Placeholder for future grouped heatmap implementation
    st.markdown("""
    **To generate a grouped heatmap, you'll need to:**
    1. Select grouping dimensions (e.g., sector, region)
    2. Recalculate temperature scores with grouping enabled
    3. Visualize the grouped aggregations
    
    This will be implemented to match the `plot_grouped_heatmap()` function from utils.py.
    """)


def plot_grouped_heatmap(grouped_aggregations, analysis_parameters):
    """
    Render a heatmap of grouped temperature scores.
    Adapted from utils.py to work with Streamlit.
    
    Args:
        grouped_aggregations: Aggregated scores with grouping
        analysis_parameters: Tuple of (timeframe, scope, grouping)
    """
    timeframe, scope, grouping = analysis_parameters
    scope = str(scope[0])
    timeframe = str(timeframe[0]).lower()
    group_1, group_2 = grouping

    aggregations = grouped_aggregations[timeframe][scope].grouped
    combinations = list(aggregations.keys())

    groups = {group_1: [], group_2: []}
    for combination in combinations:
        item_group_1, item_group_2 = combination.split('-')
        if item_group_1 not in groups[group_1]:
            groups[group_1].append(item_group_1)
        if item_group_2 not in groups[group_2]:
            groups[group_2].append(item_group_2)
    groups[group_1] = sorted(groups[group_1])
    groups[group_2] = sorted(groups[group_2])

    grid = np.zeros((len(groups[group_2]), len(groups[group_1])))
    for i, item_group_2 in enumerate(groups[group_2]):
        for j, item_group_1 in enumerate(groups[group_1]):
            key = item_group_1 + '-' + item_group_2
            if key in combinations:
                grid[i, j] = aggregations[item_group_1 + '-' + item_group_2].score
            else:
                grid[i, j] = np.nan

    current_cmap = copy.copy(matplotlib.cm.get_cmap('OrRd'))
    current_cmap.set_bad(color='grey', alpha=0.4)

    fig = plt.figure(figsize=(0.9 * len(groups[group_1]), 0.8 * len(groups[group_2])))
    ax = fig.add_subplot(111)
    im = ax.pcolormesh(grid, cmap=current_cmap)
    ax.set_xticks(0.5 + np.arange(0, len(groups[group_1])))
    ax.set_yticks(0.5 + np.arange(0, len(groups[group_2])))
    ax.set_yticklabels(groups[group_2])
    ax.set_xticklabels(groups[group_1])
    for label in ax.get_xticklabels():
        label.set_rotation(45)
        label.set_horizontalalignment('right')
    fig.colorbar(im, ax=ax)
    ax.set_title("Temperature score per " + group_2 + " per " + group_1)
    
    st.pyplot(fig)
    plt.close()
