import dash
from dash import dcc, html, State, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import os
import plotly.graph_objs as go
import json


from table_styles import get_table_style
from chart_styles import apply_darkly_style

from google.cloud import bigquery


key_json = os.getenv("BIGQUERY_KEY")
print(f"BIGQUERY_KEY: {key_json}")  # Debug

try:
    if key_json:
        # Decode and write temp key file
        key_data = json.loads(key_json)
        with open('temp_key.json', 'w') as f:
            json.dump(key_data, f)
        client = bigquery.Client.from_service_account_json('temp_key.json')
        os.remove('temp_key.json')  # Cleanup
    else:
        # Local development path
        # key_path = 'C:/Users/marcu/Documents/servicekeys/sportresults-294318-ffcf7d3aebdf.json'
        key_path = '/app/servicekeys/sportresults-294318-ffcf7d3aebdf.json'
        client = bigquery.Client.from_service_account_json(key_path)
    print("BigQuery client successfully initialized!")
except Exception as e:
    print(f"Error initializing BigQuery client: {e}")



q_teamgames = """
  SELECT *
  FROM `sportresults-294318.icehockey_plotly_dashboard.swehockey_team_games_dashboard` 
  where 1=1 
  """

q_team_season_metrics = """
  SELECT *
  FROM `sportresults-294318.icehockey_plotly_dashboard.swehockey_team_season_metrics` 
  where 1=1 
  """

q_matchdays = """
  SELECT *
  FROM `sportresults-294318.icehockey_plotly_dashboard.matchdays` 
  """

q_teams = """
  SELECT *
  FROM `sportresults-294318.icehockey_plotly_dashboard.teams` 
  """

q_team_headtohead = """
  SELECT *
  FROM `sportresults-294318.icehockey_plotly_dashboard.team_headtohead` 
  """


df_team_season_metrics = client.query(q_team_season_metrics).to_dataframe()
df_matchdays = client.query(q_matchdays).to_dataframe()
df_teams = client.query(q_teams).to_dataframe()
df_team_headtohead = client.query(q_team_headtohead).to_dataframe()

df_team_games = client.query(q_teamgames).to_dataframe()

# This part to read in locally 
# df_team_games = pd.read_csv("C:/Users/marcu/Documents/github/icehockey-dash-plotly/data/swehockey_team_games_dashboard.csv", low_memory=False)

# Convert all object columns to strings, probably not so much needed when getting data from BQ
#for col in df_team_games.select_dtypes(include=['object']).columns:
#    df_team_games[col] = df_team_games[col].astype(str)

# df_team_games.loc[:, 'date'] = pd.to_datetime(df_team_games['date'], format='%Y-%m-%d')



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
                title='🏒 Icehockey Data Dashboard', 
                suppress_callback_exceptions=True)

server = app.server

app.layout = html.Div([
    dbc.Container([

        ### HEADER ROW 
        dbc.Row(
            [
                dbc.Col(html.H1("🏒 Icehockey Data Dashboard"), width=6, className="d-flex align-items-center"), 

                dbc.Col(
                    dbc.Card(
                        id="league_card",
                        children=[
                            dbc.CardBody(
                                children=[
                                    html.Div(
                                        children=[
                                            dcc.Dropdown(
                                                id='league-dropdown',
                                                options=[{'label': grp, 'value': grp} for grp in df_team_games['league'].unique()],
                                                value='shl',  
                                                className='dash-dropdown'
                                            ),
                                            dbc.Tooltip(
                                                "Select a league", 
                                                target="league-dropdown", 
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ]
                    ),
                    width=2
                ),

                dbc.Col(
                    dbc.Card(
                        id="season_card",
                        children=[
                            dbc.CardBody(
                                children=[
                                    html.Div(
                                        children=[
                                            dcc.Dropdown(
                                                id='season-dropdown',
                                                options=[{'label': grp, 'value': grp} for grp in df_team_games['season'].unique()],
                                                value='2024/25',  
                                                className='dash-dropdown'
                                            ),
                                            dbc.Tooltip(
                                                "Select a season", 
                                                target="season-dropdown", 
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ]
                    ),
                    width=2
                ),


                dbc.Col(
                    dbc.Button(
                        "About this dashboard",
                        id="about-button",
                        color="info",
                        size="sm",
                        className="float-end",
                        # style={"padding": "4px 8px", "font-size": "0.875rem"}
                    ),
                    width=2,  
                    className="d-flex justify-content-center align-items-center"
                ),
            ],
            className="mt-2",
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
                    active_tab='tab-3',
                    children=[
                        dbc.Tab(label='🏆 Table', tab_id='tab-1'),
                        dbc.Tab(label='📈 Table Position by Matchday', tab_id='tab-2'),
                        dbc.Tab(label='📊 Point Distribution', tab_id='tab-3'),
                        dbc.Tab(label='📋 Team Statistics', tab_id='tab-4'),
                        dbc.Tab(label='⚖️ Team Comparison', tab_id='tab-5'),
                    ],
                    className="bg-dark text-white" 
                )
            ])
        ]
        , className="mb-3 mt-3"
        ),
       
     ### CONTENT HEADER ROW  
     dbc.Container(
        dbc.Row(
            [

            # First column -> Header and Info - i  
            dbc.Col(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H2("Your Title Here", id="tab-title", style={"textAlign": "left", "margin": "10px"}),
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.Button(
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
                            width="auto"
                        ),
                    ],
                    className="g-0",  
                ),
                width=6  
                ),
            
                # Second column with all filters  
                dbc.Col(
                    [
                       
                    html.Div(
                        id='container_table_filters',
                        children=[
                            dbc.Row(
                                [   
                                    dbc.Col(
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("Total", id="btn-total", n_clicks=0, color="primary", outline=True, value='total', style={'width': '100%', 'margin': '5px'}),
                                                dbc.Button("Home", id="btn-home", n_clicks=0, color="primary", outline=True, value='home', style={'width': '100%', 'margin': '5px'}),
                                                dbc.Button("Away", id="btn-away", n_clicks=0, color="primary", outline=True, value='away', style={'width': '100%', 'margin': '5px'}),
                                            ],
                                            id='btn-standings-homeaway',
                                            vertical=False,
                                            size="md",
                                            className="m-3",
                                            style={'width': '100%'}  # Fill the entire column width
                                        ),
                                        width=6  # Takes up half of the row's space
                                    ),
                                    dbc.Col(
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("All", id="btn-all", n_clicks=0, color="primary", outline=True, value='all', style={'flex': '1', 'margin': '5px'}),
                                                dbc.Button("Last 5 games", id="btn-last5", n_clicks=0, color="primary", outline=True, value='last5', style={'flex': '1', 'margin': '5px'}),
                                                dbc.Button("Last 10 games", id="btn-last10", n_clicks=0, color="primary", outline=True, value='last10', style={'flex': '1', 'margin': '5px'}),
                                            ],
                                            id='btn-last-games',
                                            vertical=False,
                                            size="md",
                                            className="m-3",
                                            style={'width': '100%', 'display': 'flex'} 
                                        ),
                                        width=6  
                                    ),
                                ],
                                justify="start",  
                                align="center",
                            ),
                        ],
                        style={"display": "none"}  
                    ),

                    dcc.Dropdown(
                            id='matchday-dropdown',
                            options=[{'label': grp, 'value': grp} for grp in df_matchdays['matchday'].unique()],
                            value=52,
                            placeholder='Select matchday',
                            className='dash-dropdown',
                            searchable=True,
                            style={'marginBottom': '10px', 'marginTop': '10px'}
                        ),
                    dbc.Tooltip(
                            "Select matchday", 
                            target="matchday-dropdown", 
                        ),
                    dcc.Dropdown(
                            id='team-dropdown',
                            options=[{'label': grp, 'value': grp} for grp in df_teams['team'].unique()],
                            value='Leksands IF',
                            placeholder='Select team',
                            className='dash-dropdown',
                            searchable=True,
                            style={'marginBottom': '10px', 'marginTop': '10px'}
                        ),
                    dbc.Tooltip(
                            "Select team", 
                            target="team-dropdown", 
                        ),
                    html.Div(
                        id='btn-group-metricselectcontainer',
                        children=[

                            dbc.ButtonGroup(
                                [
                                    dbc.Button("Points", id="btn-points", n_clicks=0, color="primary", outline=True, value='avg_points', style={'margin': '5px'}),
                                    dbc.Button("Scored", id="btn-scored", n_clicks=0, color="primary", outline=True, value='avg_scored', style={'margin': '5px'}),
                                    dbc.Button("Conceded", id="btn-conceded", n_clicks=0, color="primary", outline=True, value='avg_conceded', style={'margin': '5px'}),
                                    dbc.Button("Spectators Home", id="btn-spectators-home", n_clicks=0, color="primary", outline=True, value='avg_spectators', style={'margin': '5px'}),
                                    dbc.Button("Spectators Away", id="btn-spectators-away", n_clicks=0, color="primary", outline=True, value='avg_spectators_away', style={'margin': '5px'}),
                                    dbc.Button("Points Home", id="btn-points-home", n_clicks=0, color="primary", outline=True, value='avg_points_home', style={'margin': '5px'}),
                                    dbc.Button("Points Away", id="btn-points-away", n_clicks=0, color="primary", outline=True, value='avg_points_away', style={'margin': '5px'}),
                                ],
                                id='btn-group-metricselector',
                                vertical=False,
                                size="md",
                                className="mb-3",
                                style={'display': 'flex', 'width': '100%', 'justify-content': 'space-between'}
                            )
                        ],
                        style={"display": "none"}
                    ),
                    ],
                    width=6  
                ),
                
            ],
            # justify="between", 
            align="left"  ,
            style={"paddingLeft": "0", "paddingRight": "0", 'marginLeft': '0'},
        )
        ,style={"paddingLeft": "0", "paddingRight": "0", 'marginLeft': '0'}
    ),
     
    dbc.Row([
            dbc.Collapse(
                html.Div("This is some collapsible content!", className="p-2"),
                id="info-toggle-collapse",
                is_open=False
            ),
        ]),

    ## MAIN CONTENT ROW  
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
        dcc.Store(id='team-season-aggr', data={}), 
        dcc.Store(id='metricselector-button-text', storage_type='memory'),  
        dcc.Store(id='homeaway-button-text', storage_type='memory'),  
        dcc.Store(id='lastgames-button-text', storage_type='memory'),
        dcc.Store(id='selected-tab-text', storage_type='memory'),
        dcc.Store(id='btn-group-standings_homeaway', storage_type='memory')
    ], fluid=True
    )
])



#######################################################################################################

##                                      CALLBACKS 

#######################################################################################################


## CALLBACK: Dropdown and filter visibility 

@app.callback(
    [
        Output('container_table_filters', 'style'),
        Output('matchday-dropdown', 'className'),
        Output('team-dropdown', 'className'), 
        Output('btn-group-metricselectcontainer', 'style'),
        Output('tab-title', 'children'), 
        Output('info-toggle-collapse', 'children')

     ],  
    [Input('tabs', 'active_tab')]
)
def update_dropdown_visibility(active_tab):
    if active_tab == 'tab-1':
        # Show dropdown 1, hide dropdown 2
        return {"display": "block"}, 'hidden-dropdown','hidden-dropdown', {"display": "none"}, '🏆 Standings', 'This section contains standings, based on filter selection.'
    elif active_tab == 'tab-2':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, 'hidden-dropdown','hidden-dropdown', {"display": "none"}, '📈 Table Position by Matchday', 'This section show the table position by team for each matchday. Each line represents one team. Double click on a team in the legend to the right to show one specific team.'
    elif active_tab == 'tab-3':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, 'dash-dropdown','hidden-dropdown',  {"display": "none"}, '📊 Point Distribution', 'This section visualizes boxplots for point distribution for a selected league and matchday, where points illustrates specific teams. Narrow box -> very tight, low distribution of points. Wide box -> very spread out. Horizontal line illustrates the median value Hoover for more information.'
    elif active_tab == 'tab-4':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, 'hidden-dropdown', 'dash-dropdown',   {"display": "none"}, '📋 Team Statistics', 'This section visualizes team statistics.'
    elif active_tab == 'tab-5':
        # Show dropdown 2, hide dropdown 1
        return {"display": "none"}, 'hidden-dropdown', 'hidden-dropdown',   {"display": "block"}, '⚖️ Team Comparison', 'This section visualizes the selected metric by team and season Grey box means that the team did not play in the selected leauge that season.'
    # Default hide all 
    return {"display": "none"}, 'hidden-dropdown', 'hidden-dropdown',   {"display": "none"}, 'n/a', 'n/a'


## CALLBACK: Home or Away Selector in Tab 1

@app.callback(
        [
        Output('btn-total', 'style'),
        Output('btn-home', 'style'),
        Output('btn-away', 'style'),
        Output('homeaway-button-text', 'data')
    ],
    [
        Input('btn-total', 'n_clicks'),
        Input('btn-home', 'n_clicks'),
        Input('btn-away', 'n_clicks'),
    ],
    [
        State('btn-total', 'value'),
        State('btn-home', 'value'),
        State('btn-away', 'value'),
    ]
)

def highlight_button(_, __, ___, total_value, home_value, away_value):
    ctx = dash.callback_context

    # Define active and inactive styles
    active_style = {'backgroundColor': 'blue', 'color': 'white'}
    inactive_style = {}

    # Set all styles to inactive initially
    total_style = inactive_style
    home_style = inactive_style
    away_style = inactive_style
    
     # Determine which button was clicked and apply the active style. 
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'btn-total':
            total_style = active_style
            selected_text = total_value
        elif button_id == 'btn-home':
            home_style = active_style
            selected_text = home_value
        elif button_id == 'btn-away':
            away_style = active_style
            selected_text = away_value

    # If not triggered, default to "points"
    else:
        selected_text = total_value  
        total_style = active_style 


    return total_style, home_style, away_style, selected_text

## CALLBACK: Last Games Selector in Tab 1
@app.callback(
        [
        Output('btn-all', 'style'),
        Output('btn-last5', 'style'),
        Output('btn-last10', 'style'),
        Output('lastgames-button-text', 'data')
    ],
    [
        Input('btn-all', 'n_clicks'),
        Input('btn-last5', 'n_clicks'),
        Input('btn-last10', 'n_clicks'),
    ],
    [
        State('btn-all', 'value'),
        State('btn-last5', 'value'),
        State('btn-last10', 'value'),
    ]
)

def highlight_button(_, __, ___, all_value, last5_value, last10_value):
    ctx = dash.callback_context

    # Define active and inactive styles
    active_style = {'backgroundColor': 'blue', 'color': 'white'}
    inactive_style = {}

    # Set all styles to inactive initially
    all_style = inactive_style
    last5_style = inactive_style
    last10_style = inactive_style
    
     # Determine which button was clicked and apply the active style. 
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'btn-all':
            all_style = active_style
            selected_text = all_value
        elif button_id == 'btn-last5':
            last5_style = active_style
            selected_text = last5_value
        elif button_id == 'btn-last10':
            last10_style = active_style
            selected_text = last10_value

    # If not triggered, default to "points"
    else:
        selected_text = all_value  
        all_style = active_style 


    return all_style, last5_style, last10_style, selected_text

## CALLBACK: Metric Selector in Tab Team Comparison
@app.callback(
        [
        Output('btn-points', 'style'),
        Output('btn-scored', 'style'),
        Output('btn-conceded', 'style'),
        Output('btn-spectators-home', 'style'),
        Output('btn-spectators-away', 'style'),
        Output('btn-points-home', 'style'),
        Output('btn-points-away', 'style'),
        Output('metricselector-button-text', 'data')
    ],
    [
        Input('btn-points', 'n_clicks'),
        Input('btn-scored', 'n_clicks'),
        Input('btn-conceded', 'n_clicks'),
        Input('btn-spectators-home', 'n_clicks'),
        Input('btn-spectators-away', 'n_clicks'),
        Input('btn-points-home', 'n_clicks'),
        Input('btn-points-away', 'n_clicks'),
        
    ],
    [
        State('btn-points', 'value'),
        State('btn-scored', 'value'),
        State('btn-conceded', 'value'),
        State('btn-spectators-home', 'value'),
        State('btn-spectators-away', 'value'),
        State('btn-points-home', 'value'),
        State('btn-points-away', 'value'),
        
    ]
)

def highlight_button(_, __, ___,____,_____,______,_______,  points_value, scored_value, conceded_value, spectatorshome_value, spectatorsaway_value, pointshome_value, pointsaway_value):
    ctx = dash.callback_context

    # Define active and inactive styles
    active_style = {'backgroundColor': 'blue', 'color': 'white'}
    inactive_style = {}

    # Set all styles to inactive initially
    points_style = inactive_style
    scored_style = inactive_style
    conceded_style = inactive_style
    spectatorshome_style = inactive_style
    spectatorsaway_style = inactive_style
    pointshome_style = inactive_style
    pointsaway_style = inactive_style
    

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
        elif button_id == 'btn-spectators-home':
            spectatorshome_style = active_style
            selected_text = spectatorshome_value
        elif button_id == 'btn-spectators-away':
            spectatorsaway_style = active_style
            selected_text = spectatorsaway_value
        elif button_id == 'btn-points-home':
            pointshome_style = active_style
            selected_text = pointshome_value
        elif button_id == 'btn-points-away':
            pointsaway_style = active_style
            selected_text = pointsaway_value

    # If not triggered, default to "points"
    else:
        selected_text = points_value  
        points_style = active_style 


    return points_style, scored_style, conceded_style, spectatorshome_style, spectatorsaway_style, pointshome_style, pointsaway_style, selected_text



# CALLBACK: To update the all datatables and filter selections
@app.callback(
    [
        Output('table-filtered', 'data'),
        Output('season-league-filtered', 'data'),
        Output('league-matchday-filtered', 'data'), 
        ],
    [
        Input('league-dropdown', 'value'),
        Input('season-dropdown', 'value'),
        Input('matchday-dropdown', 'value'),
        Input('homeaway-button-text', 'data'), 
        Input('lastgames-button-text', 'data')
        ]
)

def update_table(selected_league, selected_season, selected_matchday, homeaway_button_text, lastgames_button_text):
    
    # Create the dataframe for the table 
    df_table_filtered = df_team_games[(df_team_games['league'] == selected_league) & 
                                 (df_team_games['season'] == selected_season) & 
                                 (df_team_games['game_id'].notna())]
    
      
    if homeaway_button_text !="total":
        df_table_filtered = df_table_filtered[df_table_filtered['h_a'] == homeaway_button_text]
    
    if lastgames_button_text =="last5":
        df_table_filtered = df_table_filtered.sort_values(by='date', ascending=False).groupby('team').head(5).reset_index(drop=True)
    if lastgames_button_text =="last10":
        df_table_filtered = df_table_filtered.sort_values(by='date', ascending=False).groupby('team').head(10).reset_index(drop=True)
    


 
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
                                                (df_team_games['matchday'] == selected_matchday) & 
                                                (df_team_games['result'].notna())]
        
    return df_table_filtered.to_dict('records'), df_season_league_filtered.to_dict('records'), df_league_matchday_filtered.to_dict('records')


# CALLBACK to send data into the different tabs 
@app.callback(
    Output('tab-content', 'children'),
    [
        Input('tabs', 'active_tab'),
        Input('table-filtered', 'data'),
        Input('season-league-filtered', 'data'),
        Input('league-matchday-filtered', 'data'), 
        Input('metricselector-button-text', 'data'),
        Input('team-dropdown', 'value'),
        Input('league-dropdown', 'value')
        ]
)

def render_content(selected_tab, table_filtered, season_league_filtered, league_matchday_filtered,  metricselector_text, selected_team, selected_league):
    
    df_table_filtered = pd.DataFrame(table_filtered)

    df_season_league_filtered = pd.DataFrame(season_league_filtered)

    df_league_matchday_filtered =  pd.DataFrame(league_matchday_filtered)

    # Content rendering logic for each tab
    if selected_tab == 'tab-1':
        return tab_content_table(df_table_filtered)  
    elif selected_tab == 'tab-2':
        return tab_content_points(df_season_league_filtered)
    elif selected_tab == 'tab-3':
        return tab_content_pointdistr(df_league_matchday_filtered)
    elif selected_tab == 'tab-4':
        return tab_content_teamstat(selected_team)
    elif selected_tab == 'tab-5':
        return tab_content_teamcomparison(metricselector_text, selected_league)


## CALLBACK for Information Toggle 
@app.callback(
    Output("info-toggle-collapse", "is_open"),
    Input("info-button", "n_clicks"),
    State("info-toggle-collapse", "is_open"),
)
def toggle_info(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


## CALLBACK "ABOUT DASHBOARD" button 
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

    return dbc.Container(
        fluid=True,
        style={'height': '65vh'},  
        children=[
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
                    page_size=len(df_table_filtered),  
                    style_table={'overflowX': 'auto', 'width': '100%','height': '100%'},
                    markdown_options={"html": True}, 
                     style_cell={
                         'backgroundColor': '#343a40',
                         'color': 'white',
                         'textAlign': 'left',
                     },
                     style_header={
                         'backgroundColor': '#495057',
                         'fontWeight': 'bold',
                         'color': 'white'
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

    # Get min matchday where we have non played games 
    matchday_not_finished = df_season_league_filtered[df_season_league_filtered['game_id'].isnull()]["matchday"].min()

    # Set to 100 if therer was no non played 
    if pd.isnull(matchday_not_finished):
        matchday_not_finished = 100


    df_season_league_filtered = df_season_league_filtered[df_season_league_filtered['game_id'].notnull()].sort_values(by=['team', 'matchday'])

    df_season_league_filtered_finished = df_season_league_filtered[df_season_league_filtered['matchday'] < matchday_not_finished].sort_values(by=['team', 'matchday'])



    max_position = df_season_league_filtered_finished['table_position'].max()
    middle_position = (max_position+1)//2
    matchday_max = df_season_league_filtered_finished["matchday"].max()  # Get the maximum matchday

    season_txt = df_season_league_filtered_finished["season"].max() 
    league_txt = df_season_league_filtered_finished["league"].max() 


    fig_tblpos = px.line(df_season_league_filtered_finished,
                         title = None ,
                         x='matchday', 
                         y='table_position', 
                         color='team',
                         markers = True)

    # Add annotations for each team's last point
    for team in df_season_league_filtered_finished["team"].unique():
        team_data = df_season_league_filtered_finished[df_season_league_filtered_finished["team"] == team]
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
        tickformat='d',  
        showgrid=True,  # Keep grid lines visible
        gridwidth=1,  # Gridline width
        tickangle=0
)


    return dbc.Container(
        fluid=True,
        style={'height': '65vh'},  
        children=[
            dbc.Row(
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

    # Custom aggregation functions
    def top_6_limit(series):
        return series.nlargest(6).min() if len(series) >= 6 else np.nan
    def top_12_limit(series):
        return series.nlargest(12).min() if len(series) >= 12 else np.nan


    df_stats = (
        df_league_matchday_filtered.groupby('season')['points_cum']
        .agg(
            min='min',
            max='max',
            max_min_diff=lambda x: x.max() - x.min(),
            median='median',
            std='std',
            top_6_limit=top_6_limit,
            top_12_limit = top_12_limit
        )
        .reset_index()
    )

    outlier_styles = []

    for column in ['min', 'max', 'max_min_diff', 'median', 'std', 'top_6_limit', 'top_12_limit']:
        min_val = df_stats[column].min()
        max_val = df_stats[column].max()

         # Apply styles for the minimum and maximum values
        outlier_styles.extend([
            {
                'if': {
                    'column_id': column,
                    'filter_query': f'{{{column}}} = {min_val}'
                },
                'backgroundColor': 'red',
                'color': 'white'
            },
            {
                'if': {
                    'column_id': column,
                    'filter_query': f'{{{column}}} = {max_val}'
                },
                'backgroundColor': 'green',
                'color': 'white'
            }
        ])


    seasonstats_table = dash_table.DataTable(
        id='stats-table',
        data=df_stats.to_dict('records'),  
        columns=[
            {"name": "Season", "id": "season"},
            {"name": "Min", "id": "min", "type": "numeric", "format": {"specifier": "d"}},
            {"name": "Max", "id": "max", "type": "numeric", "format": {"specifier": "d"}},
            {"name": "Diff Minmax", "id": "max_min_diff", "type": "numeric", "format": {"specifier": "d"}},
            {"name": "Median", "id": "median", "type": "numeric", "format": {"specifier": "d"}},
            {"name": "Std  Dev", "id": "std", "type": "numeric", "format": {"specifier": "d"}},
            {"name": "Top 6 Limit", "id": "top_6_limit", "type": "numeric", "format": {"specifier": "d"}},
            {"name": "Top 12 Limit", "id": "top_12_limit", "type": "numeric", "format": {"specifier": "d"}},
        ],
        tooltip={
            "season": {'value': 'The season (e.g., 2021/2022)', 'use_with': 'both'},
            "min": {'value': 'Number of points of last placed team', 'use_with': 'both'},
            "max": {'value': 'Number of points of first placed team', 'use_with': 'both'},
            "max_min_diff": {'value': 'Point difference between first and last team', 'use_with': 'both'},
            "median": {'value': 'Median number of points', 'use_with': 'both'},
            "std": {'value': 'Standard deviation of points - indicates how much team points are distributed', 'use_with': 'both'},
            "top_6_limit": {'value': 'Point of position 6 (e.g. to reach playoff)', 'use_with': 'both'},
            "top_12_limit": {'value': 'Point of position 12 (e.g. to avoid relegation)', 'use_with': 'both'},
        },

        css=[{
                'selector': '.dash-table-tooltip',
                'rule': 'background-color: grey; font-family: monospace; color: white'
            }],

        style_table={'width': '100%', 'minWidth': '100%', 'maxWidth': '100%','overflowX': 'auto'},
        style_header={
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'whiteSpace': 'normal',
            'wordBreak': 'break-word',
        },
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'fontSize': '14px'
        },
        style_data_conditional=[
            {'if': {'column_id': c}, 'width': '150px'} for c in ['min', 'max', 'max_min_diff', 'median', 'std', 'top_6_limit', 'top_12_limit']
        ] + outlier_styles,
        style_as_list_view=True,
        page_size=12,
        markdown_options={"html": True}
    )


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
        style={'height': '65vh'},  
        children=[
            dbc.Row(
                style={'height': '100%'},  
                children=[
                    dbc.Col(
                        seasonstats_table,
                        width=5,
                        className = "my-1"  
                    ),
                    # Tooltips for the headers
                   #  dbc.Tooltip("The season of the data", target="stats-table-0"),
                   # dbc.Tooltip("The minimum value of the metric", target="stats-table-1"),
                   # dbc.Tooltip("The maximum value of the metric", target="stats-table-2"),
                   # dbc.Tooltip("The standard deviation of the metric", target="stats-table-3"),
                    dbc.Col(
                        dcc.Graph(
                            id='fig_tblpos_distr',
                            figure=fig_tblpos_distr,
                            style={'height': '100%'}  
                        ),
                        width=7,
                        style={'height': '100%'}  
                    ),
                ]
            )
        ]
    )



################################################################################################

#                               TAB 4 TEAMSTATS

################################################################################################

def tab_content_teamstat(selected_team):

    df_team_headtohead_filtered = df_team_headtohead[df_team_headtohead['team'] == selected_team]

    df_team_headtohead_filtered = df_team_headtohead_filtered.sort_values(by = 'avg_points', ascending = False)

    df_team_filtered = df_team_games[(df_team_games['team'] == selected_team) & (df_team_games['league'] != 'preseason')]

    df_team_season_metrics_team = df_team_season_metrics[(df_team_season_metrics['team'] == selected_team) & (df_team_season_metrics['league'] != 'preseason')]
    df_team_season_metrics_team = df_team_season_metrics_team.sort_values(by='season')


    current_position = df_team_season_metrics_team[df_team_season_metrics_team['season'] == '2024/25']['table_position'].astype(int).astype(str).values[0]
    current_points = df_team_season_metrics_team[df_team_season_metrics_team['season'] == '2024/25']['points'].astype(int).astype(str).values[0]
    current_league = df_team_season_metrics_team[df_team_season_metrics_team['season'] == '2024/25']['league'].values[0]
    

    ####### CHART FOR TABLE POSITIONS PER SEASON 

    color_map = {'shl': 'rgba(0, 0, 255, 0.3)', 'allsvenskan': 'rgba(0, 255, 0, 0.3)'}

    # Prepare the figure
    fig_team_tblpos = go.Figure()

    # Define a single trace for the data with conditional formatting for the line color and area
    fig_team_tblpos.add_trace(
        go.Scatter(
            x=df_team_season_metrics_team['season'],
            y=df_team_season_metrics_team['table_position'],
            mode='lines+markers+text',
            textposition="top center",
            fill='tozeroy',  
            fillcolor='rgba(0, 0, 0, 0)',  
            line=dict(color='black'),  
            marker=dict(
                size=8,
                color=[color_map[league] for league in df_team_season_metrics_team['league']]  # Apply league color dynamically
            ),
            text=df_team_season_metrics_team['league_short'] + ': ' + df_team_season_metrics_team['table_position'].astype(int).astype(str),
            hoverinfo="text+x+y",
            showlegend=False
        )
    )

    # Apply the Darkly theme (assuming this is a custom function)
    fig_team_tblpos = apply_darkly_style(fig_team_tblpos)

    # Add manual legend entries using invisible traces (if needed)
    for league, color in color_map.items():
        fig_team_tblpos.add_trace(go.Scatter(
            x=[None], y=[None],  # Dummy points
            mode='markers',
            marker=dict(color=color, size=8),
            name=league  # Label for the legend
        ))


    # Customize layout
    fig_team_tblpos.update_layout(
        title={'text': 'Table Position by Season','x': 0,'xanchor': 'left','pad': {'l': 5, 't': 5}},
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor='rgba(35, 38, 45, 1)',
        plot_bgcolor='rgba(70, 70, 70, 0.5)',
        xaxis=dict(
            range=[-0.5, len(df_team_season_metrics_team['season'].unique()) - 0.5],
            type='category'
        ),
        yaxis=dict(
            range=[16, -1],
            tickvals=[1, 14],
            autorange=False, 
            showgrid = False , 
            showticklabels = False 
        ),
       autosize=True
    )

    ########################################################################################################################

    # MATCHDAY TABLE  

    # Mapping results to colors
    color_map = {'win': 'green', 'lost': 'red', 'draw': 'darkblue'}
    symbol_map = {'win': 'circle', 'lost': 'x', 'draw': 'diamond'}
    df_team_filtered['color'] = df_team_filtered['result'].map(color_map).fillna('gray')
    df_team_filtered['symbol'] = df_team_filtered['result'].map(symbol_map).fillna('circle-open')
    df_team_filtered['hover_text'] = (
        df_team_filtered['game'] + '<br>' +
        'Score: ' + df_team_filtered['score'] + '<br>' +
        'Date: ' + df_team_filtered['date'].astype(str) + '<br>' +
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
            size=10
        ),
        text=df_team_filtered['hover_text'],  # Display the result on hover
        hoverinfo='text'
    ))

    fig_teamstat_matches = apply_darkly_style(fig_teamstat_matches)

    # Add titles 
    fig_teamstat_matches.update_layout(
        title={'text': 'Match Results by Season','x': 0,'xanchor': 'left','pad': {'l': 5, 't': 5}},
        xaxis_title="Matchday",
        yaxis_title=None,
        autosize=True,
        margin=dict(l=20, r=20, t=30, b=10),
    )


    ################### SPARKLINE CHART FOR METRICS 

    df_team_season_metrics_team_selected = df_team_season_metrics_team[['season','avg_scored', 'avg_conceded', 'avg_points']]

    df_team_season_metrics_team_pivot = df_team_season_metrics_team_selected.set_index('season').transpose().reset_index()

    df_team_season_metrics_team_pivot.columns = ['Metric'] + list(df_team_season_metrics_team_selected['season'])  # Rename columns

    ################### HeadtoHead - Top 

    fig_h2h_top = go.Figure()

    fig_h2h_top = px.bar(
        df_team_headtohead_filtered.head(10),
        x='avg_points',
        y='opponent',
        orientation='h',  
        color='avg_points',
        color_continuous_scale='RdYlGn',
        range_color=[0.5, 2.5], 
        title="🥳 Opponents",
        labels={'opponent': 'Opponent', 'avg_points':  'Ø points'},
        text='avg_points'
    )

    fig_h2h_top = apply_darkly_style(fig_h2h_top)

    # Customize layout
    fig_h2h_top.update_layout(
        yaxis=dict(categoryorder='total ascending', title=''), 
        xaxis = dict(title=''),
        margin=dict(l=10, r=10, t=50, b=30) , 
        showlegend=False,
        coloraxis_showscale=False,
        autosize=True
    )

    fig_h2h_top.update_traces(
        texttemplate='%{x:.1f}',
        showlegend=False
    )

    

        ################### HeadtoHead - Bot 

    fig_h2h_bot = go.Figure()

    fig_h2h_bot = px.bar(
        df_team_headtohead_filtered.tail(10),
        x='avg_points',
        y='opponent',
        orientation='h',  
        color='avg_points',
        color_continuous_scale='RdYlGn',
        range_color=[0.5, 2.5], 
        title="😱 Opponents",
        labels={'opponent': 'Opponent', 'avg_points': 'Ø points'},
        text='avg_points'
    )

    fig_h2h_bot = apply_darkly_style(fig_h2h_bot)

    # Customize layout
    fig_h2h_bot.update_layout(
        yaxis=dict(categoryorder='total descending',  title=''), 
        xaxis = dict(title=''),
        margin=dict(l=10, r=10, t=50, b=30) , 
        showlegend=False,
        coloraxis_showscale=False,
        autosize=True
    )

    fig_h2h_bot.update_traces(
        texttemplate='%{x:.1f}',
        showlegend=False
    )



    return dbc.Container(
        fluid=True,  
        style={'height': '65vh'},  
        children=[ 
            dbc.Row(
                style={'height': '20vh'},
                children=[
                    dbc.Col(
                        children=[
                        dbc.Row(
                            html.H1(
                            selected_team,
                            className="plotly-header"
                            ), 
                        className="mb-1", 
                        ),
                        dbc.Row(
                            html.P(
                            f"{current_position} in {current_league} ( {current_points} points)",
                            style={
                                "fontSize": "24px",  
                                "fontWeight": "bold", 
                                "color": "white",       
                                "margin": "0"          
                            }
                            ), 
                        className="mb-1", 
                        ),
                        ],
                        width=7
                    ),  
                    dbc.Col(
                        dcc.Graph(
                            id='fig_team_tblpos',
                            figure=fig_team_tblpos,
                            style={'height': '100%',
                            'padding-left': '3px', 
                            'padding-right': '3px'
                            }
                        ),
                        width=5 ,
                        style={
                               'padding-left': '3px', 
                            'padding-right': '3px'}  
                    ),
                ], 
                className="m-1"
            ),
            dbc.Row(
                style={'height': '45vh'},
                children=[ 
                    dbc.Col(
                        dcc.Graph(
                            id='fig_teamstat_matches',
                            figure=fig_teamstat_matches,
                            style={'height': '100%'}
                        ),
                        width=7 ,
                        className="m-0 mb-2"
                    ),
                    dbc.Col(
                        children=[
                            dbc.Row(
                                style={'height': '45vh'},
                                children=[
                                    dbc.Col(
                                        dcc.Graph(
                                            id='fig_h2h_top',
                                            figure=fig_h2h_top,
                                            style={'height': '100%'}
                                        ),
                                        width=6,  # Adjust the width as needed
                                        className="m-0"
                                    ),
                                    dbc.Col(
                                        dcc.Graph(
                                            id='fig_h2h_bot',
                                            figure=fig_h2h_bot,
                                            style={'height': '100%'}
                                        ),
                                        width=6,  # Adjust the width as needed
                                        className="m-0"
                                    ),
                                ],
                                className="m-0 mb-2"
                            )
                        ],
                        width=5,  
                        className="m-0"
                    ) 
                ]
                 ,className="m-1 mt-3"
            )
        ]
)



################################################################################################

#                               TAB 5 TEAMCOMPARISON

################################################################################################


def tab_content_teamcomparison(metricselector_text, selected_league):

    df_team_season_aggr = df_team_season_metrics[df_team_season_metrics['league'] == selected_league]
    
    df_team_season_aggr = df_team_season_aggr[['team', 'season', metricselector_text]]

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
    margin=dict(l=5, r=20, t=15, b=10),  
    height=1200, 
    title = None
    )

    return dbc.Container(
    fluid=True,
    style={'height': '65vh'},  
    children=[
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