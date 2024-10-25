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
select 
table_position, team, matchday, points_cum as P, league, season, max_matchday, 
concat(scored_cum, "-",conceded_cum) as GD, last_5_games
from (
  SELECT team, matchday, max(matchday) over (partition by team, schedule_id) as max_matchday, scored_cum, conceded_cum, points_cum, table_position , result, league, season, 
  STRING_AGG(result) over (partition by team, schedule_id order by date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as last_5_games
  FROM `sportresults-294318.games_data.swehockey_team_games` 
  where 1=1 
  and score is not null 
)
order by points_cum desc, table_position asc   
"""

q_tblpos_per_season = """
SELECT team, matchday, points_cum, table_position, season, count(*) over (partition by matchday, season) as matchday_cnt 
FROM `sportresults-294318.games_data.swehockey_team_games` 
where league = 'shl' and matchday = 11 and score is not null 
order by matchday, table_position 
"""


# Execute the query and convert the results to a pandas DataFrame
df_tblpos = client.query(q_tblpos).to_dataframe()


df_tblposperseason = client.query(q_tblpos_per_season).to_dataframe()


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
                        dbc.Tab(label='Points and table position', tab_id='tab-2'),
                        dbc.Tab(label='Number of goals', tab_id='tab-3'),
                        dbc.Tab(label='Team Statistics', tab_id='tab-4'),
                        dbc.Tab(label='Season Overview', tab_id='tab-5'),
                    ],
                    className="bg-dark text-white"  # Add Bootstrap classes for background and text colors
                )
            ])
        ]),
        dbc.Row(
            [
            dbc.Col(
            dcc.Dropdown(
            id='league-dropdown',
            options=[{'label': cat, 'value': cat} for cat in df_tblpos['league'].unique()],
            value = 'shl',
            placeholder='Select league',
           className='dash-dropdown'  
        ),width=6
            ),
              dbc.Col(
        dcc.Dropdown(
            id='season-dropdown',
            options=[{'label': grp, 'value': grp} for grp in df_tblpos['season'].unique()],
            value = '2024/25',
            placeholder='Select season',
            className='dash-dropdown'  
            ),width=6
            ),
    ], id='dropdown-container', style={'marginBottom': '10px', 'marginTop': '10px'}
          )

        ,dcc.Store(id='df-season-league', data={}),  # Hidden storage for filtered DataFrame        
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
    [Output('league-dropdown', 'style'),
     Output('season-dropdown', 'style')],
    [Input('tabs', 'active_tab')]
)
def update_dropdown_visibility(active_tab):
    if active_tab == 'tab-1':
        # Show dropdown 1, hide dropdown 2
        return {'display': 'block'}, {'display': 'block'}
    elif active_tab == 'tab-2':
        # Show dropdown 2, hide dropdown 1
        return {'display': 'block'}, {'display': 'block'}
    # Default case, hide both
    return {'display': 'none'}, {'display': 'none'}




# Callback to update the DataTable based on selected tab and dropdown
@app.callback(
    Output('df-season-league', 'data'),
    [Input('tabs', 'active_tab'),  # Changed to active_tab
     Input('league-dropdown', 'value'),
     Input('season-dropdown', 'value')]
)

def update_table(selected_tab, selected_league, selected_season):
    df_season_league = pd.DataFrame()
    df_season_league = df_tblpos[(df_tblpos['league'] == selected_league) & (df_tblpos['season'] == selected_season)]

    return df_season_league.to_dict('records')


# Use the filtered data for content rendering
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('df-season-league', 'data')]
)

def render_content(selected_tab, df_season_league):
    df_tblpos_filtered = pd.DataFrame(df_season_league)

    df_season_league_max = df_tblpos_filtered[df_tblpos_filtered['max_matchday'] == df_tblpos_filtered['matchday']]

    # Content rendering logic for each tab
    if selected_tab == 'tab-1':
        return tab_content_table(df_season_league_max)
    elif selected_tab == 'tab-2':
        return tab_content_points(df_tblpos_filtered)
    elif selected_tab == 'tab-3':
        return tab_content_goals()
    elif selected_tab == 'tab-4':
        return tab_content_statistics()
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
                        {"name": "Points", "id": "P"}, 
                        {"name": "GD", "id": "GD"}, 
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

    fig_tblpos_distr = px.box(df_tblposperseason, x='season', y='points_cum', color='season', title='Point Distribution per Season', points='all', boxmode='overlay',
                                category_orders={'season': sorted(df_tblposperseason['season'].unique())}
                                )

    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_tblpos',
                    figure=fig_tblpos
                )
            )
        ]),
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_tblpos_distr',
                    figure=fig_tblpos_distr
                )
            )
        ])
     ])

def tab_content_goals():
    return html.Div("Content for Number of goals")

def tab_content_statistics():
    return html.Div("Content for Team Statistics")

def tab_content_overview():
    return html.Div("Content for Season Overview")


if __name__ == '__main__':
    app.run_server(debug=True)