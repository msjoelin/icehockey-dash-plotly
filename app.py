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
import base64

from table_styles import get_table_style
from chart_styles import apply_darkly_style

from google.cloud import bigquery


##### SET UP CONNECTION TO BIGQUERY ######

key_json = os.getenv("BIGQUERY_KEY")
local_key_path = 'C:/Users/marcu/Documents/servicekeys/sportresults-294318-ffcf7d3aebdf.json'

print(f"BIGQUERY_KEY: {key_json}")  # Debug

try:
    if key_json:
        decoded_key = base64.b64decode(key_json).decode('utf-8')
        key_data = json.loads(decoded_key)
        with open('temp_key.json', 'w') as f:
            json.dump(key_data, f)
        client = bigquery.Client.from_service_account_json('temp_key.json')
        os.remove('temp_key.json')  # Cleanup
    elif os.path.exists(local_key_path):
        # Local development key path
        client = bigquery.Client.from_service_account_json(local_key_path)
    else:
        # Local development path
        # key_path = 'C:/Users/marcu/Documents/servicekeys/sportresults-294318-ffcf7d3aebdf.json'
        key_path = '/app/servicekeys/sportresults-294318-ffcf7d3aebdf.json'
        client = bigquery.Client.from_service_account_json(key_path)
    print("BigQuery client successfully initialized!")

except Exception as e:
    print(f"Error initializing BigQuery client: {e}")

############################################################################################################



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

q_team_currentmetrics = """
  SELECT *
  FROM `sportresults-294318.icehockey_plotly_dashboard.team_current_metrics` 
  """



df_team_games = client.query(q_teamgames).to_dataframe()
df_team_season_metrics = client.query(q_team_season_metrics).to_dataframe()
df_matchdays = client.query(q_matchdays).to_dataframe()
df_teams = client.query(q_teams).to_dataframe()
df_team_headtohead = client.query(q_team_headtohead).to_dataframe()
df_team_currentmetrics = client.query(q_team_currentmetrics).to_dataframe()



# Function to map results to icons 
def map_results_to_icons(results):

    icon_map = {
        'win': '<span class="square-icon win">W</span>',
        'draw': '<span class="square-icon draw">T</span>',
        'lost': '<span class="square-icon loss">L</span>',
        'ot win': '<span class="square-icon ot-win">T</span>',
        'ot loss': '<span class="square-icon ot-loss">T</span>',
    }
  
    if not results:
        return ''

    icons = []
    results_list = results.split(',')

    for result in results_list[:]:
        icons.append(icon_map.get(result, ''))  # Default to empty if not found

    return ' '.join(icons)

# Apply the mapping function to the 'last_5' column
df_team_games['last_5_icons'] = df_team_games['last_5_games'].apply(map_results_to_icons)
df_team_games['result_icon'] = df_team_games['result_details'].apply(map_results_to_icons)


# INITIALIZE DASH APP 
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.DARKLY, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"], 
                title='🏒 Hockey Insights Hub', 
                suppress_callback_exceptions=True)

server = app.server

app.layout = html.Div([
    dbc.Container([

        ### HEADER ROW 
        dbc.Row(
            [
                dbc.Col(html.H1("🏒 Hockey Insights Hub"), width=6, className="d-flex align-items-center"), 
                dbc.Col(
                    dbc.Button(
                        "About this dashboard",
                        id="about-button",
                        color="info",
                        size="sm",
                        style={"rightMargin": "20px"}
                    ),
                    width=6,  
                    className="d-flex justify-content-end align-items-center"
                ),
            ],
            className="mt-2",
        ),

        # POPUP FOR INFO BUTTON
        # MODAL FOR INFO BUTTON
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("About Hockey Insights Hub")),
                dbc.ModalBody(
                    html.Div([
                        html.P("Hey there! 👋 This dashboard is all about diving into 🏒 ice hockey stats and having some fun with it."),
                        html.Br(),
                        html.P("You’ll find data from Sweden’s top two leagues, SHL and HockeyAllsvenskan, updated daily 📅 to keep things fresh."),
                        html.P("No promises that it’s perfect—so if you spot something odd, just roll with it. This is for fun, after all! 🎉"),
                        html.Br(),
                        html.P([
                            "Got questions, ideas, or just want to say hi? 💡 Shoot me an email at ",
                            html.A("marcussjolin89@gmail.com", href="mailto:marcussjolin89@gmail.com", style={"textDecoration": "none", "color": "#007bff"}),
                            " ✉️"
                        ]),
                ])
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
            centered=True,  
            is_open=False, 
          #  style={"maxWidth": "60%", "marginLeft": "auto", "marginRight": "auto"}
        ),

        ### TAB ROW
        dbc.Row([
            dbc.Col([
                dbc.Tabs(
                    id="tabs",
                    active_tab='tab-2',
                    children=[
                        dbc.Tab(label='🏆 Table', tab_id='tab-1'),
                        dbc.Tab(label='🎮 Games', tab_id='tab-2'),
                        dbc.Tab(label='📈 Matchday Table Position', tab_id='tab-3'),
                        dbc.Tab(label='📊 Point Distribution', tab_id='tab-4'),
                        dbc.Tab(label='📋 Team Statistics', tab_id='tab-5'),
                        dbc.Tab(label='⚖️ Team Comparison', tab_id='tab-6'),
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

            # Header and Info - i  
            dbc.Col(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H2("Your Title Here", id="tab-title", style={"textAlign": "left", "margin": "10px", 'marginRight': '0px', "fontSize":"28px"}), 
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.Button(
                                html.I(className="fas fa-info-circle"),
                                id="info-button",
                                className="btn-sm btn-info float-end",
                                n_clicks=0,
                                style={
                                    "font-size": "1.2rem",
                                    "color": "white",
                                    "background-color": "transparent",
                                    "border": "none",
                                    'marginRight': '0px',  
                                    'marginLeft': '5px' 
                                },
                            ),
                            width="auto"
                        ),
                    ],
                    className="g-0",  
                    ),
                    width=4  
                ),
            
            # Relevant Filter Section  
            dbc.Col(
                html.Div(
                    [
                    
                            dcc.Dropdown(
                                id='league-dropdown',
                                options=[{'label': grp, 'value': grp} for grp in df_team_games['league'].unique()],
                                value='shl',
                                className='m-1',
                                clearable=False
                            ),
                            dbc.Tooltip("Select a league",  target="league-dropdown", ),
                            dcc.Dropdown(
                                id='season-dropdown',
                                options=[{'label': grp, 'value': grp} for grp in df_team_games['season'].unique()],
                                value='2024/25',
                                className='m-1',
                                clearable=False
                            ),
                            dbc.Tooltip("Select a season", target="season-dropdown"),       
                            # Home/Away Button 
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
                                style={
                                    'marginBottom': '10px', 
                                    'marginTop': '10px',
                                    'width': 'auto',  
                                    'marginLeft': '0px',  
                                    'marginRight': 'auto'  ,                                   
                                    }
                            ),
                                 
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("All", id="btn-all", n_clicks=0, color="primary", outline=True, value='all', style={'width': '100%', 'margin': '5px'}),
                                    dbc.Button("Last 5", id="btn-last5", n_clicks=0, color="primary", outline=True, value='last5', style={'width': '100%', 'margin': '5px'}),
                                    dbc.Button("Last 10", id="btn-last10", n_clicks=0, color="primary", outline=True, value='last10', style={'width': '100%', 'margin': '5px'}),
                                ],
                                id='btn-last-games',
                                vertical=False,
                                size="md",
                                className="m-3",
                                style={
                                    'marginBottom': '10px', 
                                    'marginTop': '10px',
                                    'width': 'auto',  
                                    'marginLeft': '0px',  
                                    'marginRight': 'auto'  ,
                                    'display': 'flex', 'justify-content': 'flex-start'
                                    }  
                        ),
                    dcc.Dropdown(
                            id='matchday-dropdown',
                            options=[{'label': grp, 'value': grp} for grp in df_matchdays['matchday'].unique()],
                            value=52,
                            placeholder='Select matchday',
                            className='m-1',
                            searchable=True,
                            clearable=False
                            ),
                    dbc.Tooltip("Select matchday", target="matchday-dropdown",),

                    dcc.Dropdown(
                            id='matchdaymetric-dropdown',
                            options=[
                                {'label': 'Table Position', 'value': 'table_position'},
                                {'label': 'Average Points', 'value': 'avg_points'}
                            ],
                            value='table_position',
                            placeholder='Select metric',
                            className='m-1',
                            clearable=False
                            ),
                    dbc.Tooltip("Select metric", target="matchdaymetric-dropdown",),

                    dcc.Dropdown(
                            id='team-dropdown',
                            options=[{'label': grp, 'value': grp} for grp in df_teams['team'].unique()],
                            value='Leksands IF',
                            placeholder='Select team',
                            className='m-1',
                            searchable=True,
                            clearable=False
                        ),
                    dbc.Tooltip("Select team", target="team-dropdown"),

                            dbc.ButtonGroup(
                                [
                                    dbc.Button("Points", id="btn-points", n_clicks=0, color="primary", outline=True, value='avg_points', style={'margin': '3px'}),
                                    dbc.Button("Scored", id="btn-scored", n_clicks=0, color="primary", outline=True, value='avg_scored', style={'margin': '3px'}),
                                    dbc.Button("Goal Against", id="btn-conceded", n_clicks=0, color="primary", outline=True, value='avg_conceded', style={'margin': '3px'}),
                                    dbc.Button("Spectators (H)", id="btn-spectators-home", n_clicks=0, color="primary", outline=True, value='avg_spectators', style={'margin': '3px'}),
                                    dbc.Button("Spectators (A)", id="btn-spectators-away", n_clicks=0, color="primary", outline=True, value='avg_spectators_away', style={'margin': '3px'}),
                                    dbc.Button("Points (H)", id="btn-points-home", n_clicks=0, color="primary", outline=True, value='avg_points_home', style={'margin': '3px'}),
                                    dbc.Button("Points (A)", id="btn-points-away", n_clicks=0, color="primary", outline=True, value='avg_points_away', style={'margin': '3px'}),
                                ],
                                id='btn-group-metricselector',
                                vertical=False,
                                size="md",
                                className="m-3 mr-1",
                                style={'display': 'flex', 'width': 'auto', 'justify-content': 'flex-start'}
                            )
                            ],
                    style={'display': 'flex', 'flexDirection': 'row', 'flexWrap': 'wrap', 'justifyContent': 'flex-start', 'align-items': 'flex-start'}
                    ),
                    width=8  
                ),  
            ],
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
        Output('season-dropdown', 'className'),
        Output('league-dropdown', 'className'),
        Output('btn-standings-homeaway', 'className'),
        Output('btn-last-games', 'className'),
        Output('matchday-dropdown', 'className'),
        Output('matchdaymetric-dropdown', 'className'),
        Output('team-dropdown', 'className'), 
        Output('btn-group-metricselector', 'className'),
        Output('tab-title', 'children'), 
        Output('info-toggle-collapse', 'children')

     ],  
    [Input('tabs', 'active_tab')]
)

def update_dropdown_visibility(active_tab):
    if active_tab == 'tab-1':
        return 'm-1 custom-dropdown' , 'm-1 custom-dropdown',  'm-1', 'm-1', 'm-1 d-none', 'm-1 d-none','m-1 d-none', 'm-1 d-none', '🏆 Standings', 'This section contains standings, based on filter selection.'

    elif active_tab == 'tab-2':
        return 'm-1 custom-dropdown' , 'm-1 custom-dropdown',  'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none','m-1 d-none', 'm-1 d-none', '🎮 Games', 'This section contains a list of games, based on filter selection.'

    elif active_tab == 'tab-3':
        return 'm-1 custom-dropdown', 'm-1 custom-dropdown', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 custom-dropdown','m-1 d-none', 'm-1 d-none', '📈 Matchday Table Position', 'This section show the table position by team for each matchday. Each line represents one team. Double click on a team in the legend to the right to show one specific team.'

    elif active_tab == 'tab-4':
        return 'd-none', 'm-1 custom-dropdown', 'm-1 d-none', 'm-1 d-none', 'm-1 custom-dropdown','m-1 d-none', 'm-1 d-none',  'm-1 d-none', '📊 Point Distribution', 'This section visualizes boxplots for point distribution for a selected league and matchday, where points illustrates specific teams. Narrow box -> very tight, low distribution of points. Wide box -> very spread out. Horizontal line illustrates the median value Hoover for more information.'

    elif active_tab == 'tab-5':
        return 'd-none', 'd-none', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 custom-dropdown',   'm-1 d-none', '📋 Team Statistics', 'This section visualizes team statistics.'

    elif active_tab == 'tab-6':
        return 'd-none', 'm-1 custom-dropdown', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none','m-1 d-none',   'm-1 mr-1', '⚖️ Team Comparison', 'This section visualizes the selected metric by team and season Grey box means that the team did not play in the selected leauge that season.'
    # Default hide all 
    return 'm-1 d-none', 'm-1', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none', 'm-1 d-none',   'm-1 d-none', 'n/a', 'n/a'


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

    df_table_filtered['last_5_results'] = [','.join(df_table_filtered['result_details'][max(0, i-4):i+1]) for i in range(len(df_table_filtered))]

    df_table_filtered['last_5_icons'] = df_table_filtered['last_5_results'].apply(map_results_to_icons)
    df_table_filtered['result_icon'] = df_table_filtered['result_details'].apply(map_results_to_icons)
    
    # Make the aggregation 
    df_table_filtered = (
    df_table_filtered.groupby('team')
    .agg(
        points=('points', 'sum'),
        win=('win', 'sum'),
        lost=('lost', 'sum'),
        draw=('draw', 'sum'),
        ot_win=('ot_win', 'sum'),
        ot_loss=('ot_lost', 'sum'),
        scored=('score_team', 'sum'),
        conceded=('score_opponent', 'sum'),
        games=('points', 'size')  ,

        avg_points=('points', lambda x: round(x.mean(), 2)),
        avg_scored=('score_team', lambda x: round(x.mean(), 2)),
        avg_conceded=('score_opponent', lambda x: round(x.mean(), 2)),
        avg_goals_game=('goals_game', lambda x: round(x.mean(), 2)),

        last_5_icons=('last_5_icons', 'last')  
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
        Input('league-dropdown', 'value'),
        Input('matchdaymetric-dropdown','value')
        ]
)

def render_content(selected_tab, table_filtered, season_league_filtered, league_matchday_filtered,  metricselector_text, selected_team, selected_league, selected_matchdaymetric):
    
    df_table_filtered = pd.DataFrame(table_filtered)

    df_season_league_filtered = pd.DataFrame(season_league_filtered)

    df_league_matchday_filtered =  pd.DataFrame(league_matchday_filtered)

    # Content rendering logic for each tab
    if selected_tab == 'tab-1':
        return tab_content_table(df_table_filtered)  
    elif selected_tab == 'tab-2':
        return tab_content_games(df_season_league_filtered)
    elif selected_tab == 'tab-3':
        return tab_content_points(df_season_league_filtered, selected_matchdaymetric)
    elif selected_tab == 'tab-4':
        return tab_content_pointdistr(df_league_matchday_filtered)
    elif selected_tab == 'tab-5':
        return tab_content_teamstat(selected_team)
    elif selected_tab == 'tab-6':
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

    tbl_position_style = get_table_style()


    table_tbl = dash_table.DataTable(
                   id='data-table',
                    columns=[
                        {"name": "", "id": "table_position"},
                        {"name": "Team", "id": "team"},
                        {"name": "GP", "id": "games"}, 
                        {"name": "Points", "id": "points"}, 
                        {"name": "GD", "id": "goal_difference_txt"}, 
                        {"name": "W", "id": "win"}, 
                        {"name": "OT W", "id": "ot_win"}, 
                        {"name": "OT L", "id": "ot_loss"}, 
                        {"name": "L", "id": "lost"},
                        {"name": "Last 5", "id": "last_5_icons", "presentation": "markdown"}, 
                        {"name": "Ø scored", "id": "avg_scored"},
                        {"name": "Ø against", "id": "avg_conceded"},
                        {"name": "Ø goals", "id": "avg_goals_game"}
                    ],
                    tooltip={
                                "games": {'value': 'Games Played', 'use_with': 'both'},
                                "goal_difference_txt": {'value': 'Goal difference', 'use_with': 'both'},
                                "win": {'value': 'Number of games with Win', 'use_with': 'both'},
                                "ot_win": {'value': 'Number of games with OverTime Win', 'use_with': 'both'},
                                "ot_loss": {'value': 'Number of games with OverTime Loss', 'use_with': 'both'},
                                "lost": {'value': 'Number of games with Loss', 'use_with': 'both'},
                                "last_5_icons": {'value': 'Last 5 game result', 'use_with': 'both'}
                            },

                    css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'background-color: grey; font-family: monospace; color: white'
                        }],
                        
                    data=df_table_filtered.to_dict('records'),
                    page_size=len(df_table_filtered),  
                    style_table={'width': '100%', 'minWidth': '100%', 'maxWidth': '100%','overflowX': 'auto'},
                    markdown_options={"html": True}, 
                    style_cell={
                        'textAlign': 'left',
                        'padding': '3px',
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'color': 'white',
                        'fontSize': '14px',
                        'height': '18px',
                        'lineHeight': '1',
                        'whiteSpace': 'normal',
                    },
                    style_header={
                        'backgroundColor': 'rgb(30, 30, 30)',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'left',
                        'whiteSpace': 'normal',
                        'wordBreak': 'break-word',
                        'padding': '3px',
                    },
                     style_cell_conditional=[
                        {'if': {'column_id': 'table_position'}, 'width': '5%', 'textAlign': 'center'},
                        {'if': {'column_id': 'team'}, 'width': '13%'},
                        {'if': {'column_id': 'games'}, 'width': '10%'},
                        {'if': {'column_id': 'points'}, 'width': '10%'},
                        {'if': {'column_id': 'goal_difference_txt'}, 'width': '10%'},
                        {'if': {'column_id': 'win'}, 'width': '6%',},
                        {'if': {'column_id': 'ot_win'}, 'width': '6%',},
                        {'if': {'column_id': 'ot_loss'}, 'width': '6%',},
                        {'if': {'column_id': 'lost'}, 'width': '6%',},
                        {'if': {'column_id': 'last_5_icons'}, 'width': '10%',},
                        {'if': {'column_id': 'avg_scored'}, 'width': '6%',},
                        {'if': {'column_id': 'avg_conceded'}, 'width': '6%',},
                        {'if': {'column_id': 'avg_goals_game'}, 'width': '6%',},                        
                    ],
                    style_data_conditional=tbl_position_style + [
                        {
                            'if': {'column_id': 'points'}, 
                            'fontWeight': 'bold'  
                        }
                    ],
                    row_selectable=False,
                    cell_selectable=False,
                    style_as_list_view=True,
                    sort_action='native',  
                    sort_mode='single', 
            )

    return dbc.Container(
        fluid=True,
        style={'height': '100%'},  
        children=[
            dbc.Row(
                style={'height': '100%'},  
                children=[
                    dbc.Col(
                        table_tbl,
                        width=12,
                        className = "my-1",
                        # style={'height': '100%', 'padding':'0'}  
                    ),
                ]
            )
        ]
)


################################################################################################

#                               TAB 2 GAMES

################################################################################################

def tab_content_games(df_season_league_filtered):

    df_games_filtered = df_season_league_filtered[(df_season_league_filtered['h_a'] == 'home') & (df_season_league_filtered['game_id'].notna())]

    df_games_filtered = df_games_filtered.sort_values(by=['league', 'date', 'team'], ascending=[True, False, True])

    df_games_filtered['date_adjusted'] = df_games_filtered['date'].where(
                                            df_games_filtered['date'] != df_games_filtered['date'].shift(1), ''
                                            )
    

    games_tbl = dash_table.DataTable(
                   id='data-games-table',
                    columns=[
                        {"name": "League", "id": "league"},
                        {"name": "Date", "id": "date_adjusted"},

                        {"name": "Home", "id": "team"},
                        {"name": "", "id": "score_team"},

                        {"name": "", "id": "periodscore"},

                        {"name": "", "id": "score_opponent"},
                        {"name": "Away", "id": "opponent"},
                 
                    ],
                  #  tooltip={
                  #              "games": {'value': 'Games Played', 'use_with': 'both'},
                  #          },

                    css=[{
                            'selector': '.dash-table-tooltip',
                            'rule': 'background-color: grey; font-family: monospace; color: white'
                        }],
                        
                    data=df_games_filtered.to_dict('records'),
                    page_action="none",  
                    markdown_options={"html": True}, 
                    style_cell={
                        'textAlign': 'left',
                        'padding': '3px',
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'color': 'white',
                        'fontSize': '14px',
                        'height': '18px',
                        'lineHeight': '1',
                        'whiteSpace': 'normal',
                    },
                    style_header={
                        'backgroundColor': 'rgb(30, 30, 30)',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'left',
                        'whiteSpace': 'normal',
                        'wordBreak': 'break-word',
                        'padding': '3px',
                    },
                    style_data_conditional=[
                    {
                        "if": {"filter_query": "{result_details} contains 'win'", "column_id": "score_team"},
                        "backgroundColor": "#28a745",  # GREEN
                        "color": "#ffffff"  
                    },
                     {
                         "if": {"filter_query": "{result_details} contains 'los'", "column_id": "score_team"},
                         "backgroundColor": "#dc3545",  # RED
                         "color": "#ffffff"  
                     },
                     {
                         "if": {"filter_query": "{result_details} contains 'win'", "column_id": "score_opponent"},
                         "backgroundColor": "#dc3545",  # RED
                         "color": "#ffffff"
                     },
                    {
                        "if": {"filter_query": "{result_details} contains 'los'", "column_id": "score_opponent"},
                        "backgroundColor": "#28a745",  # GREEN
                        "color": "#ffffff"
                    },
                    ],
                     style_cell_conditional=[
                        {'if': {'column_id': 'league'}, 'width': '100px'},
                        {'if': {'column_id': 'date_adjusted'}, 'width': '100px'},
                        {'if': {'column_id': 'team'}, 'width': '200px', "paddingLeft": "40px"},
                        {'if': {'column_id': 'score_opponent'}, 'width': '50px', "textAlign": "center"},
                        {'if': {'column_id': 'score_team'}, 'width': '50px', "textAlign": "center"},    
                        {'if': {'column_id': 'periodscore'}, 'width': '90px', "textAlign": "center", 'fontSize': '12px'},    
                        {'if': {'column_id': 'opponent'}, 'width': '240px', "paddingLeft": "40px"},                        
                    ],
                    row_selectable=False,
                    cell_selectable=False,
                    style_as_list_view=True,
                   # sort_action='native',  
                   # sort_mode='single', 
            )

    return dbc.Container(
        fluid=True,
        style={'height': '100%', 'overflowX': 'auto'},
        children=[
            dbc.Row(
                style={'height': 'auto'},  
                children=[
                    dbc.Col(
                        games_tbl,
                        width=8,
                        className = "my-1",
                        style={'height': 'auto'} 
                        # style={'height': '100%', 'padding':'0'}  
                    ),
                ]
            )
        ]
)




################################################################################################

#                               TAB 2 POSITION BY MATCHDAY

################################################################################################


def tab_content_points(df_season_league_filtered, selected_matchdaymetric):

    # Get min matchday where we have non played games 
    matchday_not_finished = df_season_league_filtered[df_season_league_filtered['game_id'].isnull()]["matchday"].min()

    # Set to 100 if there was no non played 
    if pd.isnull(matchday_not_finished):
        matchday_not_finished = 100


    df_season_league_filtered = df_season_league_filtered[df_season_league_filtered['game_id'].notnull()].sort_values(by=['team', 'matchday'])

    df_season_league_filtered_finished = df_season_league_filtered[df_season_league_filtered['matchday'] < matchday_not_finished].sort_values(by=['team', 'matchday'])

    df_season_league_filtered_finished['avg_points'] = df_season_league_filtered_finished['points_cum'] / df_season_league_filtered_finished['matchday'] 

    #selected_metric = 'avg_points'

    max_position = df_season_league_filtered_finished[selected_matchdaymetric].max()
    middle_position = (max_position+1)//2
    matchday_max = df_season_league_filtered_finished["matchday"].max()  # Get the maximum matchday

    if selected_matchdaymetric == 'avg_points':
        yaxis_range = [0, 3]
        headline_txt = 'Average Points'
        tick_format= '.2f'
    else:
        yaxis_range = [max_position + 0.5, 0.5]
        headline_txt = 'Table Position'
        tick_format = 'd'


    fig_tblpos = px.line(df_season_league_filtered_finished,
                         title = None ,
                         x='matchday', 
                         y=selected_matchdaymetric, 
                         color='team',
                         markers = True)

    # Add annotations for each team's last point if we have the table position metric
    if selected_matchdaymetric == 'table_position':
        for team in df_season_league_filtered_finished["team"].unique():
            team_data = df_season_league_filtered_finished[df_season_league_filtered_finished["team"] == team]
            last_row = team_data.iloc[-1]
            fig_tblpos.add_annotation(
                x=matchday_max*1.05, 
                y=last_row[selected_matchdaymetric],
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
     )

    fig_tblpos.update_yaxes(
        title=headline_txt,
        title_standoff = 25,
        side = "left",
        range = yaxis_range,
        tickvals=[1, middle_position, max_position],  # Positions to show on the axis
        ticktext=['1', str(middle_position), str(max_position)],  # Labels for those positions
        tickmode='array',  # Explicitly set tickmode to array
        tickformat=tick_format,  
        showgrid=True,  
        gridwidth=1,  
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

    # Remove rows with SHL and season 2014/15, as we here had different numbers of team and thus metrics not comparible 
    df_league_matchday_filtered = df_league_matchday_filtered[~((df_league_matchday_filtered['league'] == 'shl') & (df_league_matchday_filtered['season'] == '2014/15'))]

    # Make the headline text 
    league = df_league_matchday_filtered['league'].max()
    matchday = df_league_matchday_filtered['matchday'].max()

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
            "min": {'value': f'Number of points of last placed team at matchday {matchday}', 'use_with': 'both'},
            "max": {'value': f'Number of points of first placed team at matchday {matchday}', 'use_with': 'both'},
            "max_min_diff": {'value': f'Point difference between first and last team at matchday {matchday}', 'use_with': 'both'},
            "median": {'value': f'Median number of points at matchday {matchday}', 'use_with': 'both'},
            "std": {'value': f'Standard deviation of points - indicates how much team points are distributed at matchday {matchday}', 'use_with': 'both'},
            "top_6_limit": {'value': f'Point of position 6 (e.g. to reach playoff) at matchday {matchday}', 'use_with': 'both'},
            "top_12_limit": {'value': f'Point of position 12 (e.g. to avoid relegation) at matchday {matchday}', 'use_with': 'both'},
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
            'padding': '8px',
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'fontSize': '14px'
        },
        style_data_conditional=[
            {'if': {'column_id': c}, 'width': '150px'} for c in ['min', 'max', 'max_min_diff', 'median', 'std', 'top_6_limit', 'top_12_limit']
        ] + outlier_styles,
        style_as_list_view=True,
        page_size=12,
        markdown_options={"html": True},
        row_selectable=False,
        cell_selectable=False
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
                        [
                        html.H4(
                                [
                                    "Point Distribution Metrics for ",
                                    html.B(league.upper()),
                                    " at matchday ",
                                    html.B(matchday)
                                ],
                            style={'textAlign': 'left', 'marginBottom': '15px'}
                            ),
                        seasonstats_table,
                        ],
                        width=5,
                        className = "my-1"  
                    ),
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

    df_team_headtohead_filtered = df_team_headtohead[(df_team_headtohead['team'] == selected_team) & (df_team_headtohead['games'] >= 15)]
    df_team_headtohead_filtered = df_team_headtohead_filtered.sort_values(by = 'avg_points', ascending = False)

    df_team_filtered = df_team_games[(df_team_games['team'] == selected_team) & (df_team_games['league'] != 'preseason')]

    df_team_season_metrics_team = df_team_season_metrics[(df_team_season_metrics['team'] == selected_team) & (df_team_season_metrics['league'] != 'preseason')]
    df_team_season_metrics_team = df_team_season_metrics_team.sort_values(by='season')

    # Variables for current standings 
    df_team_currentmetrics_filtered = df_team_currentmetrics[df_team_currentmetrics['team'] == selected_team]

    current_position = df_team_currentmetrics_filtered['table_position'].astype(int).astype(str).values[0]
    current_points = df_team_currentmetrics_filtered['points'].astype(int).astype(str).values[0]
    current_league = df_team_currentmetrics_filtered['league'].values[0].upper()


    last_game = df_team_currentmetrics_filtered['game_previous'].values[0]
    last_game_date = df_team_currentmetrics_filtered['date_previous'].values[0]
    last_game_result = df_team_currentmetrics_filtered['result_previous'].values[0]
    last_game_score = df_team_currentmetrics_filtered['score_previous'].values[0]
    next_game = df_team_currentmetrics_filtered['game_next'].values[0]
    next_game_date = df_team_currentmetrics_filtered['date_next'].values[0]

     
    # INFO TABLE BOX 

    info_table = html.Div([
        # Row 1: Last game and date
        html.Div([
            html.Div(f"Last Game: ", style={'flex': '1', 'textAlign': 'center', 'color': 'white'}),
            html.Div(f"{last_game}", style={'fontSize': '18px','flex': '1', 'textAlign': 'center', 'color': 'white'}),
           #  html.Div(f"{last_game_date}", style={'flex': '1', 'textAlign': 'center', 'color': 'white'})
        ], style={'marginBottom': '10px', 'marginTop': '5px'}),
        
        # Row 2: Last game result and score (bigger size)
        html.Div([
            html.Div(f"{last_game_result}  {last_game_score}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#FFD700', 'marginBottom': '5px', 'textAlign': 'center'}),
        ], style={'textAlign': 'center', 'marginBottom': '10px'}),
        
        # Row 3: Next game and date
        html.Div([
            html.Div(f"Next Game: {next_game_date} {next_game}", style={'fontSize': '14px', 'flex': '1', 'textAlign': 'center', 'color': 'white'}),
            # html.Div(f"Next Game Date: {next_game_date}", style={'flex': '1', 'textAlign': 'center', 'color': 'white'})
        ], style={'display': 'flex', 'flexDirection': 'row'})
    ], style={
        'padding': '5px',
        'border': '1px solid #2a3f5f',
        'borderRadius': '10px',
        'backgroundColor': '#1e2130',
        'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.2)'
        }
    )

    ####### CHART FOR TABLE POSITIONS PER SEASON 

    color_map = {'shl': 'rgba(0, 0, 255, 0.8)', 'allsvenskan': 'rgba(0, 255, 0, 0.8)'}

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
        title=None,
        #title={'text': 'Table Position by Season','x': 0,'xanchor': 'left','pad': {'l': 5, 't': 5}, 'font': {'size': 14}},
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(35, 38, 45, 1)',
        plot_bgcolor='rgba(70, 70, 70, 0.5)',
        xaxis=dict(
            range=[-0.5, len(df_team_season_metrics_team['season'].unique()) - 0.5],
            type='category'
        ),
        yaxis=dict(
            range=[16, -3],
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
        text=df_team_filtered['hover_text'],  
        hoverinfo='text'
    ))

    fig_teamstat_matches = apply_darkly_style(fig_teamstat_matches)

     
    fig_teamstat_matches.update_layout(
        title={'text': 'Match Results by Season','x': 0,'xanchor': 'left','pad': {'l': 5, 't': 5}},
        xaxis_title="Matchday",
        yaxis_title=None,
        autosize=True,
        margin=dict(l=20, r=20, t=30, b=10),
    )


    df_team_season_metrics_team_selected = df_team_season_metrics_team[['season','avg_scored', 'avg_conceded', 'avg_points']]

    df_team_season_metrics_team_pivot = df_team_season_metrics_team_selected.set_index('season').transpose().reset_index()

    df_team_season_metrics_team_pivot.columns = ['Metric'] + list(df_team_season_metrics_team_selected['season'])  # Rename columns

    ################### HeadtoHead - Top 

    fig_h2h_top = go.Figure()

    fig_h2h_top = px.bar(
        df_team_headtohead_filtered.head(7),
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
        df_team_headtohead_filtered.tail(7),
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
                            className="plotly-header", 
                            style = {"fontSize": "28px"}
                            ), 
                        className="mb-1", 
                        ),
                        dbc.Row(
                            html.P(
                            f"{current_position} in {current_league} ( {current_points} points)",
                            style={
                                "fontSize": "18px",  
                                "fontWeight": "bold", 
                                "color": "white",       
                                "margin": "0"          
                            }
                            ), 
                        className="mb-1", 
                        ),
                        ],
                        width=3
                    ), 
                    dbc.Col(
                        info_table,
                        width=4
                    ) ,
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
                                        width=6,  
                                        className="m-0"
                                    ),
                                    dbc.Col(
                                        dcc.Graph(
                                            id='fig_h2h_bot',
                                            figure=fig_h2h_bot,
                                            style={'height': '100%'}
                                        ),
                                        width=6,  
                                        className="m-0"
                                    ),
                                ],
                                className="m-0 mb-2"
                            )
                        ],
                        width=5,  
                        className="mb-2"
                    ) 
                ]
                 ,className="mt-3 mb-3"
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

    # Fix format, depending on what metric is selected. If spectators, we remove decimal but make it a thousand separated 
    # Format function based on conditions
    def format_value(value, metricselector_text):
        if isinstance(value, (int, float)) and not np.isnan(value):  
            if "spectators" in metricselector_text:
                return f"{int(value):,}"  
            else:
                return f"{value:.1f}"  # One decimal
        return ""  # For non-numeric values (like 'team')


    # Apply formatting to the dataframe before passing it to the DataTable
    df_team_season_aggr_pivot_formatted = df_team_season_aggr_pivot.copy()
    for col in df_team_season_aggr_pivot_formatted.columns[1:]:  # Skip the 'team' column
        df_team_season_aggr_pivot_formatted[col] = df_team_season_aggr_pivot_formatted[col].apply(lambda x: format_value(x, metricselector_text))

   
    def discrete_background_color_bins(df, n_bins=5, columns='all'):
        import colorlover
        bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
        if columns == 'all':
            if 'id' in df:
                df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
            else:
                df_numeric_columns = df.select_dtypes('number')
        else:
            df_numeric_columns = df[columns]

        df_numeric_columns = df_numeric_columns.apply(pd.to_numeric, errors='coerce')  
        df_max = df_numeric_columns.max().max()

        if "spectators" in metricselector_text:
            df_min = 4000
        else:
            df_min = df_numeric_columns.min().min()

        ranges = [
            ((df_max - df_min) * i) + df_min
            for i in bounds
        ]

        styles = []
        for i in range(1, len(bounds)):
            min_bound = ranges[i - 1]
            max_bound = ranges[i]
            backgroundColor = colorlover.scales[str(n_bins)]['seq']['YlGn'][i - 1]
            if i <=2:
                color = 'black'
            else:
                color = 'white' if i > len(bounds) / 2. else 'inherit'

            for column in df_numeric_columns:
                styles.append({
                    'if': {
                        'filter_query': (
                            '{{{column}}} >= {min_bound}' +
                            (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                        ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                        'column_id': column
                    },
                    'backgroundColor': backgroundColor,
                    'color': color
                })

        return (styles)

    (styles) = discrete_background_color_bins(df_team_season_aggr_pivot)

    
    # Define the DataTable with your data
    seasonstats_table = dash_table.DataTable(
        id='team-season-stats',
        columns=[{"name": col, "id": col} for col in df_team_season_aggr_pivot_formatted.columns],
        data=df_team_season_aggr_pivot_formatted.to_dict('records'),

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
            'padding': '5px',
        },
        style_cell={
            'textAlign': 'center',
            'padding': '2px',
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white',
            'fontSize': '14px',
            'height': 'auto',
            'lineHeight': '1',
            'whiteSpace': 'normal',
        },
        sort_action='native',  
        sort_mode='single',    
        style_as_list_view=True,
        markdown_options={"html": True},
        style_data_conditional=styles,
        row_selectable=False,
        cell_selectable=False
    )

    return dbc.Container(
    fluid=True,
    style={'height': '100%'},  
    children=[
        dbc.Row(
            style={'height': '100%'},  
            children=[
                dbc.Col(
                    seasonstats_table,
                    width=12,
                    className = "my-1",
                    # style={'height': '100%', 'padding':'0'}  
                ),
            ]
        )
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)