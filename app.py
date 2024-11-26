import dash
from dash import dcc, html, State, dash_table, callback_context
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import os
import plotly.graph_objs as go

from table_styles import get_table_style
from chart_styles import apply_darkly_style
from header_info_section import create_header_with_info
from info_section import create_info_section


from google.cloud import bigquery

key_path = 'C:/Users/marcu/Documents/servicekeys/sportresults-294318-ffcf7d3aebdf.json'

# Get data from BQ 
client = bigquery.Client.from_service_account_json(key_path)

q_tblpos = """
  SELECT *
  FROM `sportresults-294318.games_data.swehockey_team_games_dashboard` 
  where 1=1 
  """

# df_team_games = client.query(q_tblpos).to_dataframe()

# This part to read in locally 
df_team_games = pd.read_csv("C:/Users/marcu/Documents/github/icehockey-dash-plotly/data/swehockey_team_games_dashboard.csv", low_memory=False)

# Convert all object columns to strings, probably not so much needed when getting data from BQ
for col in df_team_games.select_dtypes(include=['object']).columns:
    df_team_games[col] = df_team_games[col].astype(str)

df_team_games.loc[:, 'date'] = pd.to_datetime(df_team_games['date'], format='%Y-%m-%d')



# Function to map results to icons 
def map_results_to_icons(results):
    icon_map = {
        'win': '<i class="fas fa-check-circle" style="color: green;"></i>',
        'draw': '<i class="fas fa-minus-circle" style="color: darkblue;"></i>',
        'lost': '<i class="fas fa-times-circle" style="color: red;"></i>',
    }
    
    if not results:
        return ''

    icons = []
    results_list = results.split(',')

    for result in results_list[:-1]:
        icons.append(icon_map.get(result, ''))  # Default to empty if not found
    
    last_icon = f'<span class="rounded-icon">{icon_map.get(results_list[-1], "")}</span>'
    icons.append(last_icon)

    return ' '.join(icons)

# Apply the mapping function to the 'last_5' column
df_team_games['last_5_icons'] = df_team_games['last_5_games'].apply(map_results_to_icons)
df_team_games['result_icon'] = df_team_games['result'].apply(map_results_to_icons)


style_data_conditional = get_table_style()


# INITIALIZE DASH APP 
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.DARKLY, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"], 
                title='Icehockey Data Dashboard', 
                suppress_callback_exceptions=True)


app.layout = html.Div([
    dbc.Container([

        ### HEADER ROW 
        dbc.Row(
            [
                dbc.Col(html.H1("Icehockey Data Dashboard"), width=5, className="d-flex align-items-center"), 
                dbc.Col(
                        dbc.Card(
                        id = "league_card", 
                        children = [
                        dbc.CardBody(
                            [
                                html.H5("League", className="card-title", style={'marginBottom': '5px', 'fontSize': '18px'}),
                                dcc.Dropdown(
                                    id='league-dropdown',
                                    options=[{'label': cat, 'value': cat} for cat in df_team_games['league'].unique()],
                                    value='shl',  # Default value
                                    # labelStyle={'display': 'block'},  # Display each option on a new line
                                    className='dash-dropdown'
                                )
                            ]
                        )],
                        # style={'marginBottom': '5px', 'padding': '10px'},
                    ),width=2
                ), 
                dbc.Col(
                        dbc.Card(
                        id = "season_card", 
                        children = [
                        dbc.CardBody(
                            [
                                html.H5("Season", className="card-title", style={'marginBottom': '5px', 'fontSize': '18px'}),
                                dcc.Dropdown(
                                    id='season-dropdown',
                                    options=[{'label': grp, 'value': grp} for grp in df_team_games['season'].unique()],
                                    value='2024/25',  
                                    className='dash-dropdown'
                                )
                            ]
                        )],
                        # style={'marginBottom': '5px', 'padding': '10px'},
                    ),width=2
                ),
                dbc.Col(
                    dbc.Button(
                        "About this dashboard",
                        id="about-button",
                        color="info",
                        size="sm",
                        className="float-end",
                    ),
                    width=3,  
                    className="d-flex align-items-center justify-content-end pe-3"
                ),
            ],
            className="mb-4",
        ),
        # POPUP FOR INFO BUTTON
        # MODAL FOR INFO BUTTON
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("About Icehockey Plotly Dashboard")),
                dbc.ModalBody(
                    html.P("This dashboard provides insights and statistics for ice hockey games.")
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id="close-modal",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="about-modal",
            centered=True,  # Center the modal
            is_open=False,  # Initial state is closed
        ),

        ### TAB ROW
        dbc.Row([
            dbc.Col([
                dbc.Tabs(
                    id="tabs",
                    active_tab='tab-1',
                    children=[
                        dbc.Tab(label='Table', tab_id='tab-1'),
                        dbc.Tab(label='Table Position by Matchday', tab_id='tab-2'),
                        dbc.Tab(label='Point Distribution', tab_id='tab-3'),
                        dbc.Tab(label='Team Statistics', tab_id='tab-4'),
                        dbc.Tab(label='Team Comparison', tab_id='tab-5'),
                    ],
                    className="bg-dark text-white" 
                )
            ])
        ]),
       
     ### CONTENT HEADER ROW  
     dbc.Container([
        dbc.Row(
            [
                dbc.Col(
                    html.H2("Your Title Here", id = "tab-title", style={"textAlign": "left", "margin": "20px 0"}),
                    width=4 
                ),
                dbc.Col(
                        dbc.Button(
                            #"Info",
                            html.I(className="fas fa-info-circle"),
                            id="info-button",
                            className="btn-sm btn-info float-end",
                            n_clicks=0,
                            style={
                            "font-size": "1.7rem", 
                            "color": "white",  
                            "background-color": "transparent", 
                            "border": "none"
                            },
                        ),
                        width=1
                ),
                # Second Column with Children Content
                dbc.Col(
                    [
                    dbc.Row(
                    [   
                    # First Card: Home / Away
                        dbc.Col(
                            dbc.Card(
                                id="homeaway_card",
                                children=[
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "Home / Away",
                                                className="card-title",
                                                style={'marginBottom': '10px', 'fontSize': '18px'}
                                            ),
                                            dcc.RadioItems(
                                                id='homeaway-dropdown',
                                                options=[
                                                    {'label': 'Home', 'value': 'home'},
                                                    {'label': 'Away', 'value': 'away'},
                                                    {'label': 'Total', 'value': 'total'}
                                                ],
                                                value='total',
                                                labelStyle={'display': 'block'},
                                                className='dash-radio'
                                            )
                                        ]
                                    )
                                ],
                                style={'marginBottom': '10px', 'padding': '10px'}
                            ),
                            width=6  
                        ),
                        # Second Card: Games
                        dbc.Col(
                            dbc.Card(
                                id="lastgames_card",
                                children=[
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "Games",
                                                className="card-title",
                                                style={'marginBottom': '10px', 'fontSize': '18px'}
                                            ),
                                            dcc.RadioItems(
                                                id='lastgames-radiobutton',
                                                options=[
                                                    {'label': 'All', 'value': 'all'},
                                                    {'label': 'Last 5', 'value': 'last5'},
                                                    {'label': 'Last 10', 'value': 'last10'}
                                                ],
                                                value='all',
                                                labelStyle={'display': 'block'},
                                                className='dash-radio'
                                            )
                                        ]
                                    )
                                ],
                                style={'marginBottom': '10px', 'padding': '10px'}
                            ),
                            width=6  # Adjust width to control spacing
                        )
                    ],
                    justify="start",  # Align cards to the start of the row
                    align="center",  # Vertically center the cards
                    ),
                    dcc.Dropdown(
                            id='matchday-dropdown',
                            options=[{'label': grp, 'value': grp} for grp in df_team_games['matchday'].unique()],
                            value=52,
                            placeholder='Select matchday',
                            className='dash-dropdown',
                            style={'marginBottom': '10px'}
                        ),
                    dcc.Dropdown(
                            id='team-dropdown',
                            options=[{'label': grp, 'value': grp} for grp in df_team_games['team'].unique()],
                            value='Leksands IF',
                            placeholder='Select team',
                            className='dash-dropdown',
                            searchable=True,
                            style={'marginBottom': '10px'}
                        ),
                    html.Div(
                        id='btn-group-metricselectcontainer',
                        children=[
                            html.H5(
                                "Select Metric",
                                style={'marginBottom': '10px', 'marginTop': '10px'}
                            ),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("Points", id="btn-points", n_clicks=0, color="primary", outline=True, value='points', style={'margin': '5px'}),
                                    dbc.Button("Scored", id="btn-scored", n_clicks=0, color="primary", outline=True, value='score_team', style={'margin': '5px'}),
                                    dbc.Button("Conceded", id="btn-conceded", n_clicks=0, color="primary", outline=True, value='score_opponent', style={'margin': '5px'}),
                                ],
                                id='btn-group-metricselector',
                                vertical=False,
                                size="md",
                                className="mb-3",
                                style={'width': '100%'}
                            )
                        ],
                        style={"display": "none"}
                    ),
                     #    html.Div(
                     #        id='btn-group-teamtab',
                     #        children=[
                     #            html.H5(
                     #                "Select Metric",
                     #                style={'marginBottom': '10px', 'marginTop': '10px'}
                     #            ),
                     #            dbc.ButtonGroup(
                     #                [
                     #                    dbc.Button("Overview", id="btn-overview", n_clicks=0, color="primary", outline=True, value='overview', style={'margin': '5px'}),
                     #                    dbc.Button("Season Stats", id="btn-seasonstat", n_clicks=0, color="primary", outline=True, value='seasonstat', style={'margin': '5px'}),
                     #                    dbc.Button("Table Positions", id="btn-tblpos", n_clicks=0, color="primary", outline=True, value='tableposition', style={'margin': '5px'}),
                     #                ],
                     #                id='btn-group-teamtab2',
                     #                vertical=True,
                     #                size="md",
                     #                className="mb-3",
                     #                style={'width': '100%'}
                     #            )
                     #        ],
                     #        style={"display": "none"}
                     #    )
                    ],
                    width=7  # Adjust width as needed
                ),
                
            ],
            justify="between",  # Adjust row alignment (e.g., "center", "start", "end")
            align="center"  # Adjust vertical alignment
        )
     ]),
        dbc.Row([
            dbc.Collapse(
                html.Div("This is some collapsible content!", className="p-2"),
                id="info-toggle-collapse",
                is_open=False
            ),
        ]),
       ## MAIN CONTENT  
        dbc.Row([
            dbc.Col(
                id='main-content',
                width = 12, 
                style={'height': '100%'},  
                 children=[
                    dbc.Card(
                    dbc.CardBody(html.Div(id='tab-content')),
                    className="mt-3" 
                    )
                 ]
            )
        ]), 

        # Hidden storage for filtered DataFrame  
        dcc.Store(id='table-filtered', data={}),  
        dcc.Store(id='season-league-filtered', data={}),      
        dcc.Store(id='league-matchday-filtered', data={}),         
        dcc.Store(id='team-filtered', data={}),   
        dcc.Store(id='team-season-aggr', data={}),      
        dcc.Store(id='metricselector-button-text', storage_type='memory'),  
        dcc.Store(id='selected-tab-text', storage_type='memory')

    ], fluid=True
    )
])


@app.callback(
    [
        Output('homeaway_card', 'style'),
        Output('lastgames_card', 'style'),
        Output('matchday-dropdown', 'className'),
        Output('team-dropdown', 'className'), 
        Output('btn-group-metricselectcontainer', 'style'),
        Output('tab-title', 'children')

     ],  
    [Input('tabs', 'active_tab')]
)
def update_dropdown_visibility(active_tab):
    if active_tab == 'tab-1':
        # Show dropdown 1, hide dropdown 2
        return {"display": "block"}, {"display": "block"}, 'hidden-dropdown','hidden-dropdown', {"display": "none"}, 'Standings'
    elif active_tab == 'tab-2':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, {"display": "none"}, 'hidden-dropdown','hidden-dropdown', {"display": "none"}, 'Table Position by Matchday'
    elif active_tab == 'tab-3':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"},  {"display": "none"}, 'dash-dropdown','hidden-dropdown',  {"display": "none"}, 'Point Distribution'
    elif active_tab == 'tab-4':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, {"display": "none"}, 'hidden-dropdown', 'dash-dropdown',   {"display": "none"}, 'Team Statistics'
    elif active_tab == 'tab-5':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, {"display": "none"}, 'hidden-dropdown', 'hidden-dropdown',   {"display": "block"}, 'Team Comparison'
    # Default hide all 
    return {"display": "none"}, {"display": "none"}, 'hidden-dropdown', 'hidden-dropdown',   {"display": "none"}, 'n/a'


@app.callback(
    [Output('tabheader-content', 'children')],  
    [Input('tabs', 'active_tab')]
)
def update_tabheader(active_tab):
    if active_tab == 'tab-1':
        # Show dropdown 1, hide dropdown 2
        return {"display": "block"},'hidden-dropdown','hidden-dropdown',{"display": "block"}
    elif active_tab == 'tab-2':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"},'hidden-dropdown','hidden-dropdown', {"display": "none"}
    elif active_tab == 'tab-3':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"},'dash-dropdown','hidden-dropdown', {"display": "none"}
    elif active_tab == 'tab-4':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"},'hidden-dropdown', 'dash-dropdown', {"display": "none"}
    elif active_tab == 'tab-5':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"},'hidden-dropdown', 'hidden-dropdown', {"display": "none"}
    # Default hide all 
    return {"display": "none"}, 'hidden-dropdown', 'hidden-dropdown', {"display": "none"}




# Callback to manage button activation
@app.callback(
        [
        Output('btn-points', 'style'),
        Output('btn-scored', 'style'),
        Output('btn-conceded', 'style'),
        Output('metricselector-button-text', 'data')
    ],
    [
        Input('btn-points', 'n_clicks'),
        Input('btn-scored', 'n_clicks'),
        Input('btn-conceded', 'n_clicks'),
    ],
    [
        State('btn-points', 'value'),
        State('btn-scored', 'value'),
        State('btn-conceded', 'value'),
    ]
)

def highlight_button(_, __, ___, points_value, scored_value, conceded_value):
    ctx = dash.callback_context

    # Define active and inactive styles
    active_style = {'backgroundColor': 'blue', 'color': 'white'}
    inactive_style = {}

    # Set all styles to inactive initially
    points_style = inactive_style
    scored_style = inactive_style
    conceded_style = inactive_style
    
     # Determine which button was clicked and apply the active style. 
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'btn-points':
            points_style = active_style
            selected_text = points_value
        elif button_id == 'btn-scored':
            scored_style = active_style
            selected_text = scored_value
        elif button_id == 'btn-conceded':
            conceded_style = active_style
            selected_text = conceded_value

    # If not triggered, default to "points"
    else:
        selected_text = points_value  
        points_style = active_style 


    return points_style, scored_style, conceded_style, selected_text


# Callback to update the DataTable based on selected tab and dropdown
@app.callback(
    [
        Output('table-filtered', 'data'),
        Output('season-league-filtered', 'data'),
        Output('league-matchday-filtered', 'data'), 
        Output('team-filtered', 'data'), 
        Output('team-season-aggr', 'data')
        ],
    [
        Input('league-dropdown', 'value'),
        Input('season-dropdown', 'value'),
        Input('matchday-dropdown', 'value'),
        Input('team-dropdown', 'value'),
        Input('homeaway-dropdown', 'value'),
        Input('lastgames-radiobutton', 'value'),
        Input('metricselector-button-text', 'data')
        ]
)

def update_table(selected_league, selected_season, selected_matchday, selected_team, selected_homeaway, selected_lastgames, metricselector_text):
    
    # Create the dataframe for the table 
    df_table_filtered = df_team_games[(df_team_games['league'] == selected_league) & 
                                 (df_team_games['season'] == selected_season) & 
                                 (df_team_games['game_id'].notna())]
    
      
    if selected_homeaway !="total":
        df_table_filtered = df_table_filtered[df_table_filtered['h_a'] == selected_homeaway]
    
    if selected_lastgames =="last5":
        df_table_filtered = df_table_filtered.sort_values(by='date', ascending=False).groupby('team').head(5).reset_index(drop=True)
    if selected_lastgames =="last10":
        df_table_filtered = df_table_filtered.sort_values(by='date', ascending=False).groupby('team').head(10).reset_index(drop=True)
    


    # df_table_filtered = df_table_filtered[df_table_filtered['max_matchday'] == df_table_filtered['matchday']] 

    df_table_filtered = df_table_filtered.sort_values(by=['team', 'date'])

    df_table_filtered['last_5_results'] = [','.join(df_table_filtered['result'][max(0, i-4):i+1]) for i in range(len(df_table_filtered))]

    df_table_filtered['last_5_icons'] = df_table_filtered['last_5_results'].apply(map_results_to_icons)
    df_table_filtered['result_icon'] = df_table_filtered['result'].apply(map_results_to_icons)
    
    # Make the aggregation 
    df_table_filtered = (
    df_table_filtered.groupby('team')
    .agg(
        points=('points', 'sum'),
        win=('win', 'sum'),
        lost=('lost', 'sum'),
        draw=('draw', 'sum'),
        scored=('score_team', 'sum'),
        conceded=('score_opponent', 'sum'),
        games=('points', 'size')  ,
        last_5_icons=('last_5_icons', 'last')  # Get the last value in each group
    )
    .reset_index()
    )

    df_table_filtered['goal_difference'] = df_table_filtered['scored'] - df_table_filtered['conceded'] 
    df_table_filtered['goal_difference_txt'] = (df_table_filtered['scored'].astype(int).astype(str)  
                                                + ' - '  
                                                + df_table_filtered['conceded'].astype(int).astype(str)
                                                + ' ('  
                                                + df_table_filtered['goal_difference'].astype(int).astype(str)
                                                + ')'
                                                )
    
    
    df_season_league_filtered = df_team_games[(df_team_games['league'] == selected_league) & 
                                 (df_team_games['season'] == selected_season)]

    df_league_matchday_filtered = df_team_games[(df_team_games['league'] == selected_league) & 
                                                (df_team_games['matchday'] == selected_matchday)]
    
    df_team_filtered = df_team_games[(df_team_games['team'] == selected_team) & (df_team_games['league'] != 'preseason')]

    df_league_filtered = df_team_games[df_team_games['league'] == selected_league]

    df_team_season_aggr =  df_league_filtered[df_league_filtered['game_id'].notna() & 
                                              (df_league_filtered['result'].astype(str).str.strip() != '')
                                              ]

    df_team_season_aggr = df_team_season_aggr.groupby(['team', 'season'])[metricselector_text].mean().reset_index()
    
    return df_table_filtered.to_dict('records'), df_season_league_filtered.to_dict('records'), df_league_matchday_filtered.to_dict('records'), df_team_filtered.to_dict('records'), df_team_season_aggr.to_dict('records')


# Use the filtered data for content rendering
@app.callback(
    Output('tab-content', 'children'),
    [
        Input('tabs', 'active_tab'),
        Input('table-filtered', 'data'),
        Input('season-league-filtered', 'data'),
        Input('league-matchday-filtered', 'data'), 
        Input('team-filtered', 'data'), 
        Input('team-season-aggr', 'data'),
        Input('metricselector-button-text', 'data')
        ]
)

def render_content(selected_tab, table_filtered, season_league_filtered, league_matchday_filtered, team_filtered, team_season_aggr, metricselector_text):
    
    df_table_filtered = pd.DataFrame(table_filtered)

    df_season_league_filtered = pd.DataFrame(season_league_filtered)

    # df_season_league_max = df_season_league_filtered[df_season_league_filtered['max_matchday'] == df_season_league_filtered['matchday']]

    df_league_matchday_filtered =  pd.DataFrame(league_matchday_filtered)

    df_team_filtered = pd.DataFrame(team_filtered)


    df_team_season_aggr = pd.DataFrame(team_season_aggr)


    # Content rendering logic for each tab
    if selected_tab == 'tab-1':
        return tab_content_table(df_table_filtered)  
    elif selected_tab == 'tab-2':
        return tab_content_points(df_season_league_filtered)
    elif selected_tab == 'tab-3':
        return tab_content_pointdistr(df_league_matchday_filtered)
    elif selected_tab == 'tab-4':
        return tab_content_teamstat(df_team_filtered)
    elif selected_tab == 'tab-5':
        return tab_content_teamcomparison(df_team_season_aggr, metricselector_text)



@app.callback(
    Output("table-section-collapse", "is_open"),
    Input("table-section-button", "n_clicks"),
    State("table-section-collapse", "is_open"),
)
def toggle_info(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("info-toggle-collapse", "is_open"),
    Input("info-button", "n_clicks"),
    State("info-toggle-collapse", "is_open"),
)
def toggle_info(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


# CALLBACKS
@app.callback(
    Output("about-modal", "is_open"),
    [Input("about-button", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("about-modal", "is_open")],
)
def toggle_modal(info_clicks, close_clicks, is_open):
    if info_clicks or close_clicks:
        return not is_open
    return is_open

################################################################################################

#                               TAB 1 TABLE

################################################################################################

def tab_content_table(df_table_filtered):

    df_table_filtered = df_table_filtered.sort_values(by=['points', 'goal_difference'], ascending=[False, False])

    df_table_filtered.insert(0, 'table_position', range(1, len(df_table_filtered) + 1))

    #season_txt = df_table_filtered["season"].max() 
    #league_txt = df_table_filtered["league"].max() 

    return dbc.Container(
        fluid=True,
        style={'height': '80vh'},  
        children=[
                create_header_with_info(
                header_text="Standings", 
                info_text="This section contains standings, based on filter selection.", 
                button_id="table-section"
            ),
        dbc.Row([
            dbc.Col(
                dash_table.DataTable(
                   id='data-table',
                    columns=[
                        {"name": "", "id": "table_position"},
                        {"name": "Team", "id": "team"},
                        {"name": "GP", "id": "games"}, 
                        {"name": "Points", "id": "points"}, 
                        {"name": "GD", "id": "goal_difference_txt"}, 
                        {"name": "W", "id": "win"}, 
                        {"name": "D", "id": "draw"}, 
                        {"name": "L", "id": "lost"},                         
                        {"name": "Last 5", "id": "last_5_icons", "presentation": "markdown"}, 
                    ],
                    data=df_table_filtered.to_dict('records'),
                    page_size=len(df_table_filtered),  # Display all rows
                    style_table={'overflowX': 'auto', 'width': '100%'},
                    markdown_options={"html": True},  # Allow HTML rendering in markdown
                     style_cell={
                         'backgroundColor': '#343a40',
                         'color': 'white',
                         'textAlign': 'left',
                     },
                     style_header={
                         'backgroundColor': '#495057',
                         'fontWeight': 'bold',
                         'color': 'white',
                     },
                     style_cell_conditional=[
                        {'if': {'column_id': 'table_position'}, 'width': '5%'},
                        {'if': {'column_id': 'team'}, 'width': '20%'},
                        {'if': {'column_id': 'games'}, 'width': '10%'},
                        {'if': {'column_id': 'points'}, 'width': '10%'},
                        {'if': {'column_id': 'goal_difference_txt'}, 'width': '15%'},
                        {'if': {'column_id': 'win'}, 'width': '10%'},
                        {'if': {'column_id': 'draw'}, 'width': '10%'},
                        {'if': {'column_id': 'lost'}, 'width': '10%'},
                        {'if': {'column_id': 'last_5_icons'}, 'width': '10%'},
                    ],
                     style_data_conditional=style_data_conditional,
                     row_selectable=False,
                     cell_selectable=False
                        )
                    ),
                ]
            )
        ]
    )


################################################################################################

#                               TAB 2 POSITION BY MATCHDAY

################################################################################################


def tab_content_points(df_season_league_filtered):

    df_season_league_filtered = df_season_league_filtered[df_season_league_filtered['game_id'].notnull()].sort_values(by=['team', 'matchday'])


    max_position = df_season_league_filtered['table_position'].max()
    middle_position = (max_position+1)//2
    matchday_max = df_season_league_filtered["matchday"].max()  # Get the maximum matchday
    season_txt = df_season_league_filtered["season"].max() 
    league_txt = df_season_league_filtered["league"].max() 


    fig_tblpos = px.line(df_season_league_filtered,
                         title = None ,
                         x='matchday', 
                         y='table_position', 
                         color='team',
                         markers = True)

    # Add annotations for each team's last point
    for team in df_season_league_filtered["team"].unique():
        team_data = df_season_league_filtered[df_season_league_filtered["team"] == team]
        last_row = team_data.iloc[-1]
        fig_tblpos.add_annotation(
            x=matchday_max*1.05, 
            y=last_row["table_position"],
            text=team,
            showarrow=False,
            font=dict(size=12),
            align="right"
        )


    fig_tblpos = apply_darkly_style(fig_tblpos)

    # Customizing the plot to fit the Darkly theme
    fig_tblpos.update_layout(
        title_font=dict(size=20, color='white'),
        showlegend=True,
        xaxis=dict(
            title='Matchday',
            )
        )

    fig_tblpos.update_traces(
        marker=dict(size=10),
        #line=dict(width=2),  # Default line width
        #selector=dict(mode='lines') 
     )

    fig_tblpos.update_yaxes(
        title='Table Position',
        title_standoff = 25,
        side = "left",
        range=[max_position+0.5, 0.5],  # Reversed y-axis for table position
        tickvals=[1, middle_position, max_position],  # Positions to show on the axis
        ticktext=['1', str(middle_position), str(max_position)],  # Labels for those positions
        tickmode='array',  # Explicitly set tickmode to array
        tickformat='d',  # No decimal places
        showgrid=True,  # Keep grid lines visible
        gridwidth=1,  # Gridline width
        tickangle=0
)


    return dbc.Container(
        fluid=True,
        style={'height': '80vh'},  
        children=[
            create_header_with_info(
                header_text="Table Position by Matchday: " + league_txt + " " + season_txt, 
                info_text=html.Div([  
                        html.P("This section show the table position by team for each matchday.", style={"margin-bottom": "0.1rem"}),
                        html.P("Each line represents one team. Double click on a team in the legend to the right to show one specific team. ", style={"margin-bottom": "0.2rem"})
                    ]), 
                button_id="table-section"
            )
            ,dbc.Row(
                style={'height': '100%'},  
                children=[
                    dbc.Col(
                        dcc.Graph(
                            id='fig-tblpos',
                            figure=fig_tblpos,
                            style={'height': '100%'}  
                        ),
                        width=12,
                        style={'height': '100%'}  
                    ),
                ]
            )
        ]
    )


##############################################################################################

#                               TAB 3 POINT DISTRIBUTION

##############################################################################################

def tab_content_pointdistr(df_league_matchday_filtered):

    fig_tblpos_distr = px.box(df_league_matchday_filtered, 
                              x='season', 
                              y='points_cum', 
                              color='season', 
                              title=None, 
                              points='all', 
                              boxmode='overlay',
                            category_orders={'season': sorted(df_league_matchday_filtered['season'].unique())},
                            custom_data=['team'] 
                                )
    fig_tblpos_distr = apply_darkly_style(fig_tblpos_distr)

    fig_tblpos_distr.update_yaxes(
        title='Points',
    )

    fig_tblpos_distr.update_traces(
    hovertemplate="<b>Team:</b> %{customdata[0]}<br>" +
                  "<b>Points:</b> %{y}<br>" +
                  "<b>Season:</b> %{x}<extra></extra>"
                  )


    return dbc.Container(
        fluid=True,
        style={'height': '80vh'},  # Set the container to full viewport height
        children=[
            create_header_with_info(
                header_text="Point Distribution per Season", 
                info_text=html.Div([  
                        html.P("This section visualizes boxplots for point distribution for a selected league and matchday, where points illustrates specific teams. ", style={"margin-bottom": "0.1rem"}),
                        html.P("Narrow box -> very tight, low distribution of points. Wide box -> very spread out. Horizontal line illustrates the median value", style={"margin-bottom": "0.2rem"}),
                        html.P("Hoover for more information. ", style={"margin-bottom": "0.2rem"})
                    ]), 
                button_id="table-section"
            )
            ,dbc.Row(
                style={'height': '100%'},  
                children=[
                    dbc.Col(
                        dcc.Graph(
                            id='fig_tblpos_distr',
                            figure=fig_tblpos_distr,
                            style={'height': '100%'}  
                        ),
                        width=12,
                        style={'height': '100%'}  
                    ),
                ]
            )
        ]
    )



################################################################################################

#                               TAB 4 TEAMSTATS

################################################################################################

def tab_content_teamstat(df_team_filtered):

    df_teamstat_maxmatch = df_team_filtered[df_team_filtered['matchday'] == df_team_filtered['max_matchday']].reset_index(drop=True)
    df_teamstat_maxmatch = df_teamstat_maxmatch.sort_values(by='season')

    # Aggregation with metrics for radar chart


    df_teamstat_seasons = (
    df_team_filtered[df_team_filtered['matchday'] <= df_team_filtered['max_matchday']]
    .groupby(['team', 'season'])
    .agg(
        avg_points=('points', 'mean'),
        avg_win=('win', 'mean'),
        avg_lost=('lost', 'mean'),
        avg_draw=('draw', 'mean'),
        avg_scored=('score_team', 'mean'),
        avg_conceded=('score_opponent', 'mean')
    )
    .reset_index()
    )

    df_teamstat_seasons['norm_avg_scored'] = (df_teamstat_seasons['avg_scored'] - df_teamstat_seasons['avg_scored'].min()) / \
                                    (df_teamstat_seasons['avg_scored'].max() - df_teamstat_seasons['avg_scored'].min())

    df_teamstat_seasons['norm_avg_conceded'] = (df_teamstat_seasons['avg_conceded'] - df_teamstat_seasons['avg_conceded'].min()) / \
                                        (df_teamstat_seasons['avg_conceded'].max() - df_teamstat_seasons['avg_conceded'].min())


    df_teamstat_seasons['norm_avg_win'] = (df_teamstat_seasons['avg_win'] - df_teamstat_seasons['avg_win'].min()) / \
                                    (df_teamstat_seasons['avg_win'].max() - df_teamstat_seasons['avg_win'].min())

    df_teamstat_seasons['norm_avg_lost'] = (df_teamstat_seasons['avg_lost'] - df_teamstat_seasons['avg_lost'].min()) / \
                                        (df_teamstat_seasons['avg_lost'].max() - df_teamstat_seasons['avg_lost'].min())

    df_teamstat_seasons['norm_avg_draw'] = (df_teamstat_seasons['avg_draw'] - df_teamstat_seasons['avg_draw'].min()) / \
                                        (df_teamstat_seasons['avg_draw'].max() - df_teamstat_seasons['avg_draw'].min())



    # RADAR CHART 
    metrics_radar = ['norm_avg_scored', 'norm_avg_conceded', 'norm_avg_win', 'norm_avg_lost', 'norm_avg_draw']
    fig_radar = go.Figure()

    for _, row in df_teamstat_seasons.iterrows():
        # Ensure the radar chart connects back to the first point
        r_values = [row[metric] for metric in metrics_radar] + [row[metrics_radar[0]]]
        theta_values = metrics_radar + [metrics_radar[0]]

        fig_radar.add_trace(go.Scatterpolar(
            r=r_values,  # Include the first value at the end
            theta=theta_values,  # Include the first metric at the end
            fill='none',  # No fill, just lines
            name=f"{row['season']}"  # Legend for the season
        ))

    # Update layout
    fig_radar.update_layout(
        polar=dict(
        radialaxis=dict(visible=True, range=[0, 1.2]),  # Adjusted range for normalized metrics
        ),
        showlegend=True,
        title="Radar Chart for One Team"
    )

    fig_radar = apply_darkly_style(fig_radar)

    # CHART FOR TABLE POSITIONS PER SEASON 
    fig_area_team = go.Figure()

    # Background area trace (independent of league)
    fig_area_team.add_trace(go.Scatter(
        x=df_teamstat_maxmatch['season'],
        y=[14] * len(df_teamstat_maxmatch),  
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(70, 70, 70, 0.5)',  
        line=dict(color='rgba(0,0,0,0)'),  
        showlegend=False
    ))

    # Define colors for each league
    color_map = {'shl': 'rgba(0, 0, 255, 0.3)', 'allsvenskan': 'rgba(0, 255, 0, 0.3)'}
    line_color_map = {'shl': 'blue', 'allsvenskan': 'green'}

    # Prepare colors based on league
    line_colors = [line_color_map[league] for league in df_teamstat_maxmatch['league']]

    # Add single trace with conditional formatting for line and area color
    fig_area_team.add_trace(go.Scatter(
        x=df_teamstat_maxmatch['season'],
        y=df_teamstat_maxmatch['table_position'],
        mode='lines+markers+text',
        # text=[f"Season: {season}<br>League: {league}" for season, league in zip(df_teamstat_maxmatch['season'], df_teamstat_maxmatch['league'])],
        textposition="top center",
        fill='tozeroy',  
        fillcolor='rgba(0, 0, 0, 0)',  
        line=dict(color='black'),  
        marker=dict(
            size=8,
            color=line_colors,  # Line color changes per league
        ),
        text=df_teamstat_maxmatch['league'],  # Tooltip will show league name
        hoverinfo="text+x+y",
        showlegend=False
    ))


    # Format y axis 
    fig_area_team.update_yaxes(
        range=[16, -1],
        tickvals=[1, 14],  
        autorange=False
    )

    # Format x axis 
    fig_area_team.update_xaxes(type='category')

    fig_area_team = apply_darkly_style(fig_area_team)

    # Add manual legend entries using invisible traces
    for league, color in color_map.items():
        fig_area_team.add_trace(go.Scatter(
            x=[None], y=[None],  # Dummy points
            mode='markers',
            marker=dict(color=color, size=8),
            name=league  # Label for the legend
        ))


    # Customize layout
    fig_area_team.update_layout(
        title='Table Position by Season',
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor='rgba(35, 38, 45, 1)',
        plot_bgcolor='rgba(70, 70, 70, 0.5)',
        xaxis=dict(
        range=[-0.5, len(df_teamstat_maxmatch['season'].unique()) - 0.5]
        )
    )

    ##############################

    # Matchday table with icons 

    # Mapping results to colors
    color_map = {'win': 'green', 'lost': 'red', 'draw': 'darkblue'}
    symbol_map = {'win': 'circle', 'lost': 'x', 'draw': 'diamond'}
    df_team_filtered['color'] = df_team_filtered['result'].map(color_map).fillna('gray')
    df_team_filtered['symbol'] = df_team_filtered['result'].map(symbol_map).fillna('circle-open')
        # Create text for hover information
    df_team_filtered['hover_text'] = (
        df_team_filtered['game'] + '<br>' +
        'Score: ' + df_team_filtered['score'] + '<br>' +
        'Date: ' + df_team_filtered['date'] + '<br>' +
        'Result: ' + df_team_filtered['result'].fillna('No Result')
    )

    df_team_filtered['season_league'] = df_team_filtered['league'] + '\t' + df_team_filtered['season']

    df_team_filtered = df_team_filtered.sort_values(by='season')

    fig_teamstat_matches = go.Figure()

    # Add scatter trace
    fig_teamstat_matches.add_trace(go.Scatter(
        x=df_team_filtered['matchday'],
        y=df_team_filtered['season_league'],
        mode='markers',
        marker=dict(
            color=df_team_filtered['color'],
            symbol=df_team_filtered['symbol'],
            size=12
        ),
        text=df_team_filtered['hover_text'],  # Display the result on hover
        hoverinfo='text'
    ))

    fig_teamstat_matches = apply_darkly_style(fig_teamstat_matches)

    # Add titles 
    fig_teamstat_matches.update_layout(
        title="Match Results by Season",
        xaxis_title="Matchday",
        yaxis_title=None,
    )





    return dbc.Container(
        fluid=True,  
        style={'height': '80vh'},  
        children=[ 
            create_header_with_info(
                header_text="Leksands IF", 
                info_text=html.Div([  
                        html.P("This section visualizes team statistics. ", style={"margin-bottom": "0.1rem"}),
                        html.P("A narrow box means that teams are close together, a wide box means that teams are spread out. ", style={"margin-bottom": "0.2rem"}),
                    ]), 
                button_id="table-section"
            ),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=[
                        dbc.Row(
                            html.H1(
                            "Show some stats about current",
                        className="plotly-header"
                            ), className="mb-4", 
                        ),
                        ],
                        width=4
                    ),  
                    dbc.Col(
                        dcc.Graph(
                            id='fig_area_team',
                            figure=fig_area_team,
                            style={'height': '100%'}
                        ),
                        width=8 ,
                        style={'height': '250px'}  
                    ),
                ], 
                style={'height': '300px'}  
            ),
            dbc.Row(
                children=[  
                    dbc.Col(
                        dcc.Graph(
                            id='fig_teamstat_matches',
                            figure=fig_teamstat_matches
                        ),
                        width=8 
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id='fig-radar',
                            figure=fig_radar
                        ),
                        width=4 
                    ),
                ]
            )
        ]
)



################################################################################################

#                               TAB 5 TEAMCOMPARISON

################################################################################################


def tab_content_teamcomparison(df_team_season_aggr, metricselector_text):
    
    df_team_season_aggr = df_team_season_aggr.sort_values(by = 'season')

    df_team_season_aggr_pivot = df_team_season_aggr.pivot(index='team', columns='season', values=metricselector_text).reset_index()
    df_team_season_aggr_pivot.columns.name = None 

    n_cols = len(df_team_season_aggr_pivot)


    # Define colors for conditional formatting
    def get_color(value, min_value, max_value):
        if pd.isna(value):  # Default gray color for NaN
            return 'rgb(230, 230, 230)'  

        # Scale value between 0 (red) and 1 (green)
        scaled_value = (value - min_value) / (max_value - min_value)
        r = int((1 - scaled_value) * 180 + 75)  # Red decreases as value increases
        g = int(100 + (scaled_value * 50))   # Keep green constant for red-to-blue transition
        b = int(scaled_value * 180 + 75)  # Blue increases as value increases

        return f'rgb({r}, {g}, {b})'


    def get_text_color(value, min_value, max_value):
        if pd.isna(value):  # Default text color for NaN
            return 'black'
            scaled_value = (value - min_value) / (max_value - min_value)
            brightness = (1 - scaled_value) * 255 + scaled_value * 255  # Approximate brightness calculation
        
            # Dark text for bright cells, white text for dark cells
            return 'black' if brightness > 128 else 'white'

    # Apply conditional formatting per season column
    color_columns = {}
    text_colors = {}
    for col in df_team_season_aggr_pivot.columns[1:]:  # Skip 'team' column
        min_val, max_val = df_team_season_aggr_pivot[col].min(), df_team_season_aggr_pivot[col].max()
        color_columns[col] = [get_color(val, min_val, max_val) for val in df_team_season_aggr_pivot[col]]
        text_colors[col] = [get_text_color(val, min_val, max_val) for val in df_team_season_aggr_pivot[col]]

    # Create the table
    fig_tbl_teamcomp = go.Figure(data=[go.Table(
        columnwidth=[100] + [50] * (n_cols - 1),  
        header=dict(
            values=list(df_team_season_aggr_pivot.columns),
            fill_color='black',
            align='left'
        ),
        cells=dict(
            values=[
            df_team_season_aggr_pivot[col] if df_team_season_aggr_pivot[col].dtype == 'O'  # Keep non-numeric columns (e.g., team) as is
            else df_team_season_aggr_pivot[col].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "")
            for col in df_team_season_aggr_pivot.columns
            ],
            fill_color=[
                ['#34495e'] * len(df_team_season_aggr_pivot) if col == 'team'  # Slightly lighter for rows
                else color_columns[col]
                for col in df_team_season_aggr_pivot.columns
            ],
            font=dict(color='white'),  # White text for readability
            align='center',
            line_color=[
            ['white'] * len(df_team_season_aggr_pivot) if col == 'team'  # White borders for the 'team' column
            else ['darkslategray'] * len(df_team_season_aggr_pivot)
            for col in df_team_season_aggr_pivot.columns
            ]
            )
    )])

    fig_tbl_teamcomp = apply_darkly_style(fig_tbl_teamcomp)

    fig_tbl_teamcomp.update_layout(
    margin=dict(l=40, r=40, t=10, b=10),  
    height=1200, 
    title = None
    )

    return dbc.Container(
    fluid=True,
    style={'height': '100vh'},  # Set the container to full viewport height
    children=[
        create_header_with_info(
                header_text="Team Comparison - Average " + metricselector_text + 'per Team', 
                info_text=html.Div([  
                        html.P("This section visualizes the selected metric by team and season", style={"margin-bottom": "0.1rem"}),
                        html.P("Grey box means that the team didn't play in the selected leauge that season. ", style={"margin-bottom": "0.2rem"}),
                    ]), 
                button_id="table-section"
            ),
        dbc.Row(
            style={'height': '100%'},  
            children=[
                dbc.Col(
                    dcc.Graph(
                        id='fig_tbl_teamcomp',
                        figure=fig_tbl_teamcomp,
                        config={'displayModeBar': False},  # Hide unnecessary controls
                        style={'height': '100%'}  
                    ),
                    width=12,
                    style={'height': '100%', 'padding':'0'}  
                ),
            ]
        )
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)