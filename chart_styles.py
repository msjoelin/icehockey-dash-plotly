# chart_styles.py

def apply_darkly_style(fig):
    """
    Apply Darkly theme styling to a Plotly figure.

    Parameters:
        fig: The Plotly figure to style.

    Returns:
        The styled Plotly figure.
    """
    fig.update_layout(
        title_font=dict(size=20, color='white'),
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent plot background
        paper_bgcolor='rgba(40, 44, 52, 1)',  # Dark background for the Darkly theme
        font=dict(color='white'),  # White font color for better contrast
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(50, 50, 50, 0.5)',  # Semi-transparent dark background for the legend
            bordercolor='white',
            borderwidth=1
        ),
        # margin=dict(l=10, r=10, t=10, b=10)
    )

    fig.update_xaxes(
        color='white',
        gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines for x-axis
        zerolinecolor='rgba(255, 255, 255, 0.3)'
    )

    fig.update_yaxes(
        color='white',
        gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines for y-axis
        zerolinecolor='rgba(255, 255, 255, 0.3)', 
    )

    return fig
