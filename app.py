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
                title='Icehockey Data Dashboard')


app.layout = html.Div([
    dbc.Container([
        # Headline
        dbc.Row([
            dbc.Col(html.H1("Icehockey Data Dashboard"), className="mb-4")
        ]),

        # Tab Row
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
       
        dbc.Row([
            dbc.Col(id='dropdown-container', 
                width = 2 ,
                children =[  
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("League", className="card-title", style={'marginBottom': '5px', 'fontSize': '18px'}),
                                dcc.RadioItems(
                                    id='league-dropdown',
                                    options=[{'label': cat, 'value': cat} for cat in df_team_games['league'].unique()],
                                    value='shl',  # Default value
                                    labelStyle={'display': 'block'},  # Display each option on a new line
                                    className='dash-radio'
                                )
                            ]
                        ),
                        style={'marginBottom': '5px', 'padding': '10px'}
                    ),
                    dcc.Dropdown(
                        id='season-dropdown',
                        options=[{'label': grp, 'value': grp} for grp in df_team_games['season'].unique()],
                        value = '2024/25',
                        placeholder='Select season',
                        className='dash-dropdown',
                        style={'marginBottom': '10px'}
                    ),
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Home / Away", className="card-title", style={'marginBottom': '10px', 'fontSize': '18px'}),
                                dcc.RadioItems(
                                    id='homeaway-dropdown',        
                                    options=[
                                            {'label': 'Home', 'value': 'home'},
                                            {'label': 'Away', 'value': 'away'},
                                            {'label': 'Total', 'value': 'total'}
                                    ],
                                    value = 'total',
                                    # placeholder='Select home/away',
                                    labelStyle={'display': 'block'},  # Display each option on a new line
                                    className='dash-radio'
                                    )
                            ]
                        ),
                        style={'marginBottom': '5px', 'padding': '10px'}
                    ),
                    dbc.Card(
                        id = "lastgames_card",
                        children = [
                        dbc.CardBody(
                            [
                                html.H5("Games", className="card-title", style={'marginBottom': '10px', 'fontSize': '18px'}),
                                dcc.RadioItems(
                                    id='lastgames-radiobutton',        
                                    options=[
                                            {'label': 'All', 'value': 'all'},
                                            {'label': 'Last 5', 'value': 'last5'},
                                            {'label': 'Last 10', 'value': 'last10'}
                                    ],
                                    value = 'all',
                                    # placeholder='Select home/away',
                                    labelStyle={'display': 'block'},  # Display each option on a new line
                                    className='dash-radio'
                                    )
                            ]
                        )],
                        style={'marginBottom': '5px', 'padding': '10px'}
                        
                    ),
                    dcc.Dropdown(
                        id='matchday-dropdown',        
                        options=[{'label': grp, 'value': grp} for grp in df_team_games['matchday'].unique()],
                        value = 52,
                        placeholder='Select matchday',
                        className='dash-dropdown' ,
                        style={'marginBottom': '10px'}
                    ),
                    dcc.Dropdown(
                        id='team-dropdown',        
                        options=[{'label': grp, 'value': grp} for grp in df_team_games['team'].unique()],
                        value = 'Leksands IF',
                        placeholder='Select team',
                        className='dash-dropdown' , 
                        searchable=True,
                        style={'marginBottom': '10px'} 
                    ), 

                    html.Div(
                         id='btn-group-metricselectcontainer',
                         children = [
                            html.H5("Select Metric", style={'marginBottom': '10px', 'marginTop': '10px'}),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("Points", id="btn-points", n_clicks=0, color="primary", outline=True, value='points', style={'margin': '5px'}),
                                    dbc.Button("Scored", id="btn-scored", n_clicks=0, color="primary", outline=True, value = 'score_team', style={'margin': '5px'}),
                                    dbc.Button("Conceded", id="btn-conceded", n_clicks=0, color="primary", outline=True, value='score_opponent', style={'margin': '5px'}),
                                ],
                                id = 'btn-group-metricselector',
                                vertical=True, 
                                size="md",
                                className="mb-3",
                                style={'width': '100%'}
                            )
                        ],
                        style={"display": "none"} 
                    ),
                ]), 
            dbc.Col(
                id='main-content',
                width = 10, 
                style={'height': '100%'},  
                 children=[
                    dbc.Card(
                    dbc.CardBody(html.Div(id='tab-content')),
                    className="mt-3"  # Add margin to separate tabs from content
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
    ], fluid=True
    )
])


@app.callback(
    [
        Output('league-dropdown', 'className'),
        Output('season-dropdown', 'className'), 
        Output('homeaway-dropdown', 'className'),
        Output('matchday-dropdown', 'className'),
        Output('team-dropdown', 'className'), 
        Output('lastgames_card', 'style'), 
        Output('btn-group-metricselectcontainer', 'style')
     ],  
    [Input('tabs', 'active_tab')]
)
def update_dropdown_visibility(active_tab):
    if active_tab == 'tab-1':
        # Show dropdown 1, hide dropdown 2
        return 'dash-dropdown', 'dash-dropdown', 'dash-dropdown','hidden-dropdown','hidden-dropdown',{"display": "block"}, {"display": "none"}
    elif active_tab == 'tab-2':
        # Show dropdown 2, hide dropdown 1
        return 'dash-dropdown', 'dash-dropdown', 'hidden-dropdown','hidden-dropdown','hidden-dropdown', {"display": "none"}, {"display": "none"}
    elif active_tab == 'tab-3':
        # Show dropdown 2, hide dropdown 1
        return 'dash-dropdown', 'hidden-dropdown', 'hidden-dropdown','dash-dropdown','hidden-dropdown', {"display": "none"}, {"display": "none"}
    elif active_tab == 'tab-4':
        # Show dropdown 2, hide dropdown 1
        return 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown','hidden-dropdown', 'dash-dropdown', {"display": "none"}, {"display": "none"}
    elif active_tab == 'tab-5':
        # Show dropdown 2, hide dropdown 1
        return 'dash-dropdown', 'hidden-dropdown', 'hidden-dropdown','hidden-dropdown', 'hidden-dropdown', {"display": "none"}, {"display": "block"}
    # Default hide all 
    return 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', {"display": "none"}, {"display": "none"}


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


# Example tab content functions (you should replace these with your actual content)
def tab_content_table(df_table_filtered):

    df_table_filtered = df_table_filtered.sort_values(by=['points', 'goal_difference'], ascending=[False, False])

    df_table_filtered.insert(0, 'table_position', range(1, len(df_table_filtered) + 1))


    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dash_table.DataTable(
                   id='data-table',
                    columns=[
                        {"name": "Position", "id": "table_position"},
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
                     style_data_conditional=style_data_conditional,
                     row_selectable=False,
                     cell_selectable=False
                )
            ),
        ])
    ], fluid=True, style={'height': '80vh'})



# Placeholder functions for other tabs
def tab_content_points(df_season_league_filtered):

    df_season_league_filtered = df_season_league_filtered[df_season_league_filtered['game_id'].notnull()]

    max_position = df_season_league_filtered['table_position'].max()
    middle_position = (max_position+1)//2

    fig_tblpos = px.line(df_season_league_filtered.sort_values(by=['team', 'matchday']), 
                         x='matchday', 
                         y='table_position', 
                         color='team',
                         markers = True,  
                         title='Table Position by Matchday')
    
    fig_tblpos = apply_darkly_style(fig_tblpos)

    # Customizing the plot to fit the Darkly theme
    fig_tblpos.update_layout(
        title='Table Position by Matchday',
        title_font=dict(size=20, color='white'),
        legend=dict(
            title='Teams',
        ),
        xaxis=dict(
            title='Matchday',
        )
        )

    fig_tblpos.update_yaxes(
        title='Table Position',
        range=[max_position, 1],  # Reversed y-axis for table position
        tickvals=[1, middle_position, max_position],  # Positions to show on the axis
        ticktext=['1', str(middle_position), str(max_position)],  # Labels for those positions
        tickmode='array',  # Explicitly set tickmode to array
        tickformat='d',  # No decimal places
        showgrid=True,  # Keep grid lines visible
        gridwidth=1,  # Gridline width
)


    return dbc.Container(
        fluid=True,
        style={'height': '80vh'},  
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

def tab_content_pointdistr(df_league_matchday_filtered):

    fig_tblpos_distr = px.box(df_league_matchday_filtered, 
                              x='season', 
                              y='points_cum', 
                              color='season', 
                              title='Point Distribution per Season', 
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
            dbc.Row(
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


def tab_content_teamstat(df_team_filtered):

    df_teamstat_maxmatch = df_team_filtered[df_team_filtered['matchday'] == df_team_filtered['max_matchday']].sort_values(by='season')

    fig_scatter_team = px.scatter(
        df_teamstat_maxmatch,
        x='season',        
        y='table_position',     
        color='league',    
        title='Table Positions',
        # labels={'points': 'Points Scored', 'assists': 'Assists'}
    )

    fig_scatter_team.update_yaxes(autorange='reversed')


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

    # Update layout to fit the Darkly theme
    fig_teamstat_matches.update_layout(
        title="Match Results by Season",
        xaxis_title="Matchday",
        yaxis_title="",
    )

    return dbc.Container(
        fluid=True,  
        style={'height': '80vh'},  
        children=[  
            dbc.Row(
                children=[  # Define the content inside the row
                    dbc.Col(
                        dcc.Graph(
                            id='fig_scatter_team',
                            figure=fig_scatter_team
                        ),
                        width=4  
                    ),
                    dbc.Col(
                        dcc.Graph(
                            id='fig_teamstat_matches',
                            figure=fig_teamstat_matches
                        ),
                        width=8 
                    ),
                ]
            )
        ]
)

def tab_content_teamcomparison(df_team_season_aggr, metricselector_text):
    
    df_team_season_aggr = df_team_season_aggr.sort_values(by = 'season')

    # Create a scatter plot
    fig_scatter = px.scatter(
        df_team_season_aggr,
        x=metricselector_text,  
        y='team',  
        title='Average ' + metricselector_text + 'per Team',
        labels={metricselector_text: metricselector_text, 'team': 'Team'},
        color='season', 
    )

    fig_scatter = apply_darkly_style(fig_scatter)

    fig_scatter.update_traces(marker=dict(size=12, symbol='star', colorscale='Viridis'))


    fig_scatter.update_layout(
    title_font=dict(size=20, color='white'),
    xaxis=dict(
        title='Total Points',  # Update x-axis title
    ),
    yaxis=dict(
        title='',  # Update y-axis title
    ),
    )

    return dbc.Container(
    fluid=True,
    style={'height': '100vh'},  # Set the container to full viewport height
    children=[
        dbc.Row(
            style={'height': '100%'},  
            children=[
                dbc.Col(
                    dcc.Graph(
                        id='fig_scatter_teamcomparison',
                        figure=fig_scatter,
                        style={'height': '100%'}  
                    ),
                    width=12,
                    style={'height': '100%'}  
                ),
            ]
        )
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)