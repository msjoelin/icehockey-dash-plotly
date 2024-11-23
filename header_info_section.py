from dash import html, dcc
import dash_bootstrap_components as dbc

def create_header_with_info(header_text: str, info_text: str, button_id: str) -> dbc.Container:
    """
    Creates a header row with a collapsible info section.

    Args:
        header_text (str): The text for the H1 header.
        info_text (str): The content displayed in the collapsible section.
        button_id (str): The unique ID for the info button and collapse.

    Returns:
        dbc.Container: A Dash container with the header and collapsible info section.
    """
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H1(header_text, className="plotly-header"),
                        width=9
                    ),
                    dbc.Col(
                        dbc.Button(
                            #"Info",
                            html.I(className="fas fa-info-circle"),
                            id=f"{button_id}-button",
                            className="btn-sm btn-info float-end",
                            n_clicks=0,
                            style={
                            "font-size": "1.7rem",  # Adjust icon size
                            "color": "white",  # Change icon color to white
                            "background-color": "transparent", 
                            "border": "none"
                            },
                        ),
                        width=3
                    ),
                ],
                className="mb-2",
            ),
            dbc.Collapse(
                html.Div(info_text, className="p-2"),
                id=f"{button_id}-collapse",
                is_open=False,
            ),
        ]
    )