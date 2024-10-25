import dash
from dash import dcc, html, State, dash_table, callback_context
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import os
import json


from google.cloud import bigquery

key_path = 'C:/Users/marcu/Documents/servicekeys/sportresults-294318-ffcf7d3aebdf.json'



client = bigquery.Client.from_service_account_json(key_path)

# Get the data from bigquery

q_tblpos = """
  SELECT team, matchday, 
  max(matchday) over (partition by team, schedule_id) as max_matchday, 
  scored_cum, conceded_cum, 
  points_cum as P, table_position , result, league, season, 
  STRING_AGG(result) over (partition by team, schedule_id order by date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as last_5_games, 
  concat(scored_cum, "-",conceded_cum) as GD
  FROM `sportresults-294318.games_data.swehockey_team_games` 
  where 1=1 
  and score is not null 
 order by points_cum desc, table_position asc   
"""

q_tblpos_per_season = """
SELECT team, matchday, points_cum, table_position, season, league, count(*) over (partition by matchday, season) as matchday_cnt 
FROM `sportresults-294318.games_data.swehockey_team_games` 
where 1=1 
and score is not null 
order by matchday, table_position 
"""


df_team_games = pd.read_csv("C:/Users/marcu/Documents/github/icehockey-dash-plotly/data/swehockey_team_games_dashboard.csv", low_memory=False)

# Convert all object columns to strings
for col in df_team_games.select_dtypes(include=['object']).columns:
    df_team_games[col] = df_team_games[col].astype(str)


# df_tblpos = client.query(q_tblpos).to_dataframe()
df_tblpos = df_team_games[df_team_games['game_id'].notnull()].sort_values(
    ['points_cum', 'table_position'], 
    ascending = [False, True])


# df_tblposperseason = client.query(q_tblpos_per_season).to_dataframe()
df_tblposperseason =  df_team_games[df_team_games['game_id'].notnull()]


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
df_tblpos['last_5_icons'] = df_tblpos['last_5_games'].apply(map_results_to_icons)


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
        
        # Tabs using dbc.Tabs without the card argument
        dbc.Row([
            dbc.Col([
                dbc.Tabs(
                    id="tabs",
                    active_tab='tab-1',
                    children=[
                        dbc.Tab(label='Table', tab_id='tab-1'),
                        dbc.Tab(label='Table Position by matchday', tab_id='tab-2'),
                        dbc.Tab(label='Point Distribution', tab_id='tab-3'),
                        dbc.Tab(label='Team Statistics', tab_id='tab-4'),
                        dbc.Tab(label='Season Overview', tab_id='tab-5'),
                    ],
                    className="bg-dark text-white"  # Add Bootstrap classes for background and text colors
                )
            ])
        ]),
        dbc.Row(id='dropdown-container', className = 'dropdown-flex', children =[
            dbc.Col(
                dcc.Dropdown(
                id='league-dropdown',
                options=[{'label': cat, 'value': cat} for cat in df_tblpos['league'].unique()],
                value = 'shl',
                placeholder='Select league',
            className='dash-dropdown'  
                ),width=2
            ),
            dbc.Col(
                dcc.Dropdown(
                id='season-dropdown',
                options=[{'label': grp, 'value': grp} for grp in df_tblpos['season'].unique()],
                value = '2024/25',
                placeholder='Select season',
                className='dash-dropdown'  
            ),width=2
            ),
            dbc.Col(
                dcc.Dropdown(
                id='homeaway-dropdown',        
                options=[
                         {'label': 'Home', 'value': 'home'},
                         {'label': 'Away', 'value': 'away'},
                         {'label': 'Total', 'value': 'total'}
                ],
                value = 'total',
                placeholder='Select home/away',
                className='dash-dropdown'  
            ),width=2
            ),
            dbc.Col(
                dcc.Dropdown(
                id='matchday-dropdown',        
                options=[{'label': grp, 'value': grp} for grp in df_tblpos['matchday'].unique()],
                value = 52,
                placeholder='Select matchday',
                className='dash-dropdown'  
            ),width=2
            ),
             dbc.Col(
                dcc.Dropdown(
                id='team-dropdown',        
                options=[{'label': grp, 'value': grp} for grp in df_tblpos['team'].unique()],
                value = 'Leksands IF',
                placeholder='Select team',
                className='dash-dropdown' , 
                searchable=True
            ),width=2
            )
            ],  style={'marginBottom': '10px', 'marginTop': '10px'}
          )

        ,dcc.Store(id='df-season-league', data={}),  # Hidden storage for filtered DataFrame      
        dcc.Store(id='df-pos-matchday', data={}),  # Hidden storage for filtered DataFrame        
        dcc.Store(id='df-team-filtered', data={}),  # Hidden storage for filtered DataFrame        
        # Content based on tab selection, wrapped in a card
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(html.Div(id='tab-content')),
                    className="mt-3"  # Add margin to separate tabs from content
                )
            )
        ])
    ], fluid=True)
])


@app.callback(
    [Output('league-dropdown', 'className'),
     Output('season-dropdown', 'className'), 
     Output('homeaway-dropdown', 'className'),
     Output('matchday-dropdown', 'className'),
     Output('team-dropdown', 'className')],  
    [Input('tabs', 'active_tab')]
)
def update_dropdown_visibility(active_tab):
    if active_tab == 'tab-1':
        # Show dropdown 1, hide dropdown 2
        return 'dash-dropdown', 'dash-dropdown', 'dash-dropdown','hidden-dropdown','hidden-dropdown'
    elif active_tab == 'tab-2':
        # Show dropdown 2, hide dropdown 1
        return 'dash-dropdown', 'dash-dropdown', 'dash-dropdown','hidden-dropdown','hidden-dropdown'
    elif active_tab == 'tab-3':
        # Show dropdown 2, hide dropdown 1
        return 'dash-dropdown', 'hidden-dropdown', 'hidden-dropdown','dash-dropdown','hidden-dropdown'
    elif active_tab == 'tab-4':
        # Show dropdown 2, hide dropdown 1
        return 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown','hidden-dropdown', 'dash-dropdown'
    # Default hide all 
    return 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown'




# Callback to update the DataTable based on selected tab and dropdown
@app.callback(
    [Output('df-season-league', 'data'),
     Output('df-pos-matchday', 'data'), 
     Output('df-team-filtered', 'data')],
    [Input('league-dropdown', 'value'),
     Input('season-dropdown', 'value'),
     Input('matchday-dropdown', 'value'),
     Input('team-dropdown', 'value')]
)

def update_table(selected_league, selected_season, selected_matchday, selected_team):
    df_season_league = pd.DataFrame()
    df_season_league = df_tblpos[(df_tblpos['league'] == selected_league) & 
                                 (df_tblpos['season'] == selected_season)]

    df_pos_matchday_league = pd.DataFrame()
    df_pos_matchday_league = df_tblposperseason[(df_tblposperseason['league'] == selected_league) & 
                                                (df_tblposperseason['matchday'] == selected_matchday)]
    
    df_team_filtered = df_tblpos[(df_tblpos['team'] == selected_team) & (df_tblpos['league'] != 'preseason')]

    return df_season_league.to_dict('records'), df_pos_matchday_league.to_dict('records'), df_team_filtered.to_dict('records')


# Use the filtered data for content rendering
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('df-season-league', 'data'),
     Input('df-pos-matchday', 'data'), 
     Input('df-team-filtered', 'data')]
)

def render_content(selected_tab, df_season_league, df_pos_matchday_league, df_team_filtered):
    df_tblpos_filtered = pd.DataFrame(df_season_league)

    df_season_league_max = df_tblpos_filtered[df_tblpos_filtered['max_matchday'] == df_tblpos_filtered['matchday']]

    df_pos_matchday_filtered =  pd.DataFrame(df_pos_matchday_league)

    df_teamstat = pd.DataFrame(df_team_filtered)

    # Content rendering logic for each tab
    if selected_tab == 'tab-1':
        return tab_content_table(df_season_league_max)
    elif selected_tab == 'tab-2':
        return tab_content_points(df_tblpos_filtered)
    elif selected_tab == 'tab-3':
        return tab_content_pointdistr(df_pos_matchday_filtered)
    elif selected_tab == 'tab-4':
        return tab_content_teamstat(df_teamstat)
    elif selected_tab == 'tab-5':
        return tab_content_overview()


# Example tab content functions (you should replace these with your actual content)
def tab_content_table(df_season_league_max):
    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dash_table.DataTable(
                   id='data-table',
                    columns=[
                        {"name": "Team", "id": "team"},
                        {"name": "GP", "id": "matchday"}, 
                        {"name": "Points", "id": "points_cum"}, 
                        {"name": "GD", "id": "goal_difference"}, 
                        {"name": "Last 5", "id": "last_5_icons", "presentation": "markdown"}, 
                    ],
                    data=df_season_league_max.to_dict('records'),
                    page_size=len(df_season_league_max),  # Display all rows
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
                     style_data_conditional=[
                         {
                             'if': {'row_index': 'odd'},
                             'backgroundColor': '#3e444a',
                         }
                    ],
                ),
                width=4
            ),
        ])
    ], fluid=True)



# Placeholder functions for other tabs
def tab_content_points(df_tblpos_filtered):
    fig_tblpos = px.line(df_tblpos_filtered.sort_values(by=['team', 'matchday']), x='matchday', y='table_position', color='team', title='Table Position by Matchday')
    fig_tblpos.update_yaxes(range=[15, 0])

    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_tblpos',
                    figure=fig_tblpos
                )
            )
        ]),
     ])

def tab_content_pointdistr(df_pos_matchday):

    fig_tblpos_distr = px.box(df_pos_matchday, 
                              x='season', 
                              y='points_cum', 
                              color='season', 
                              title='Point Distribution per Season', 
                              points='all', 
                              boxmode='overlay',
                            category_orders={'season': sorted(df_pos_matchday['season'].unique())},
                            custom_data=['team'] 
                                )
    
    fig_tblpos_distr.update_traces(
    hovertemplate="<b>Team:</b> %{customdata[0]}<br>" +
                  "<b>Points:</b> %{y}<br>" +
                  "<b>Season:</b> %{x}<extra></extra>"
                  )

    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_tblpos_distr',
                    figure=fig_tblpos_distr
                )
            )
        ])
     ])

def tab_content_teamstat(df_teamstat):

    fig_scatter_team = px.scatter(
        df_teamstat[df_teamstat['matchday'] == df_teamstat['max_matchday']].sort_values(by='season'),
        x='season',        
        y='table_position',     
        color='league',    
        title='Scatter Plot of Points vs Assists',
        # labels={'points': 'Points Scored', 'assists': 'Assists'}
    )

    fig_scatter_team.update_yaxes(autorange='reversed')

    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_scatter_team',
                    figure=fig_scatter_team
                )
            )
        ])
     ])

def tab_content_overview():
    return html.Div("Content for Season Overview")


if __name__ == '__main__':
    app.run_server(debug=True)