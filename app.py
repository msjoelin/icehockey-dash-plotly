import dash
from dash import dcc, html, State, dash_table, callback_context
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import os
import json
import plotly.graph_objs as go



from google.cloud import bigquery

key_path = 'C:/Users/marcu/Documents/servicekeys/sportresults-294318-ffcf7d3aebdf.json'



client = bigquery.Client.from_service_account_json(key_path)

# Get the data from bigquery

q_tblpos = """
  SELECT *
  FROM `sportresults-294318.games_data.swehockey_team_games_dashboard` 
  where 1=1 
  """

df_team_games = pd.read_csv("C:/Users/marcu/Documents/github/icehockey-dash-plotly/data/swehockey_team_games_dashboard.csv", low_memory=False)



# Convert all object columns to strings
for col in df_team_games.select_dtypes(include=['object']).columns:
    df_team_games[col] = df_team_games[col].astype(str)


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
                    active_tab='tab-4',
                    children=[
                        dbc.Tab(label='Table', tab_id='tab-1'),
                        dbc.Tab(label='Table Position by Matchday', tab_id='tab-2'),
                        dbc.Tab(label='Point Distribution', tab_id='tab-3'),
                        dbc.Tab(label='Team Statistics', tab_id='tab-4'),
                        dbc.Tab(label='Team Comparison', tab_id='tab-5'),
                    ],
                    className="bg-dark text-white"  # Add Bootstrap classes for background and text colors
                )
            ])
        ]),
        dbc.Row(id='dropdown-container', className = 'dropdown-flex', children =[
            dbc.Col(
                dcc.Dropdown(
                id='league-dropdown',
                options=[{'label': cat, 'value': cat} for cat in df_team_games['league'].unique()],
                value = 'shl',
                placeholder='Select league',
            className='dash-dropdown'  
                ),width=2
            ),
            dbc.Col(
                dcc.Dropdown(
                id='season-dropdown',
                options=[{'label': grp, 'value': grp} for grp in df_team_games['season'].unique()],
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
                options=[{'label': grp, 'value': grp} for grp in df_team_games['matchday'].unique()],
                value = 52,
                placeholder='Select matchday',
                className='dash-dropdown'  
            ),width=2
            ),
             dbc.Col(
                dcc.Dropdown(
                id='team-dropdown',        
                options=[{'label': grp, 'value': grp} for grp in df_team_games['team'].unique()],
                value = 'Leksands IF',
                placeholder='Select team',
                className='dash-dropdown' , 
                searchable=True
            ),width=2
            )
            ],  style={'marginBottom': '10px', 'marginTop': '10px'}
          )

        ,dcc.Store(id='season-league-filtered', data={}),  # Hidden storage for filtered DataFrame      
        dcc.Store(id='league-matchday-filtered', data={}),  # Hidden storage for filtered DataFrame        
        dcc.Store(id='team-filtered', data={}),  # Hidden storage for filtered DataFrame    
        dcc.Store(id='league-filtered', data={}),  # Hidden storage for filtered DataFrame        
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
    elif active_tab == 'tab-5':
        # Show dropdown 2, hide dropdown 1
        return 'dash-dropdown', 'hidden-dropdown', 'hidden-dropdown','hidden-dropdown', 'hidden-dropdown'
    # Default hide all 
    return 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown', 'hidden-dropdown'




# Callback to update the DataTable based on selected tab and dropdown
@app.callback(
    [Output('season-league-filtered', 'data'),
     Output('league-matchday-filtered', 'data'), 
     Output('team-filtered', 'data'), 
     Output('league-filtered', 'data')],
    [Input('league-dropdown', 'value'),
     Input('season-dropdown', 'value'),
     Input('matchday-dropdown', 'value'),
     Input('team-dropdown', 'value')]
)

def update_table(selected_league, selected_season, selected_matchday, selected_team):
    df_season_league_filtered = df_team_games[(df_team_games['league'] == selected_league) & 
                                 (df_team_games['season'] == selected_season)]

    df_league_matchday_filtered = df_team_games[(df_team_games['league'] == selected_league) & 
                                                (df_team_games['matchday'] == selected_matchday)]
    
    df_team_filtered = df_team_games[(df_team_games['team'] == selected_team) & (df_team_games['league'] != 'preseason')]

    df_league_filtered = df_team_games[df_team_games['league'] == selected_league]

    return df_season_league_filtered.to_dict('records'), df_league_matchday_filtered.to_dict('records'), df_team_filtered.to_dict('records'), df_league_filtered.to_dict('records')


# Use the filtered data for content rendering
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('season-league-filtered', 'data'),
     Input('league-matchday-filtered', 'data'), 
     Input('team-filtered', 'data'), 
     Input('league-filtered', 'data')]
)

def render_content(selected_tab, season_league_filtered, league_matchday_filtered, team_filtered, league_filtered):
    df_season_league_filtered = pd.DataFrame(season_league_filtered)

    df_season_league_max = df_season_league_filtered[df_season_league_filtered['max_matchday'] == df_season_league_filtered['matchday']]

    df_league_matchday_filtered =  pd.DataFrame(league_matchday_filtered)

    df_team_filtered = pd.DataFrame(team_filtered)

    df_league_filtered = pd.DataFrame(league_filtered)

    # Content rendering logic for each tab
    if selected_tab == 'tab-1':
        return tab_content_table(df_season_league_max)
    elif selected_tab == 'tab-2':
        return tab_content_points(df_season_league_filtered)
    elif selected_tab == 'tab-3':
        return tab_content_pointdistr(df_league_matchday_filtered)
    elif selected_tab == 'tab-4':
        return tab_content_teamstat(df_team_filtered)
    elif selected_tab == 'tab-5':
        return tab_content_overview(df_league_filtered)


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
def tab_content_points(df_season_league_filtered):

    max_position = df_season_league_filtered['table_position'].max()
    middle_position = (max_position+1)//2

    fig_tblpos = px.line(df_season_league_filtered.sort_values(by=['team', 'matchday']), 
                         x='matchday', 
                         y='table_position', 
                         color='team', 
                         title='Table Position by Matchday')
    
    # Customizing the plot to fit the Darkly theme
    fig_tblpos.update_layout(
        title='Table Position by Matchday',
        title_font=dict(size=20, color='white'),
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent plot background
        paper_bgcolor='rgba(40, 44, 52, 1)',  # Dark background for the Darkly theme
        font=dict(color='white'),  # White font color for better contrast
        legend=dict(
            title='Teams',
            font=dict(color='white'),
            bgcolor='rgba(50, 50, 50, 0.5)',  # Semi-transparent dark background for the legend
            bordercolor='white',
            borderwidth=1
        ),
        xaxis=dict(
            title='Matchday',
            color='white',
            gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines for x-axis
            zerolinecolor='rgba(255, 255, 255, 0.3)'
        )
        )

    fig_tblpos.update_yaxes(
        title='Table Position',
        range=[max_position, 1],  # Reversed y-axis for table position
        color='white',
        gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines for y-axis
        zerolinecolor='rgba(255, 255, 255, 0.3)', 
        tickvals=[1, middle_position, max_position],  # Positions to show on the axis
        ticktext=['1', str(middle_position), str(max_position)],  # Labels for those positions
        tickmode='array',  # Explicitly set tickmode to array
        tickformat='d',  # No decimal places
        showgrid=True,  # Keep grid lines visible
        gridwidth=1,  # Gridline width
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
     ])

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

def tab_content_teamstat(df_team_filtered):

    df_teamstat_maxmatch = df_team_filtered[df_team_filtered['matchday'] == df_team_filtered['max_matchday']].sort_values(by='season')

    fig_scatter_team = px.scatter(
        df_teamstat_maxmatch,
        x='season',        
        y='table_position',     
        color='league',    
        title='Scatter Plot of Points vs Assists',
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

    # Update layout to fit the Darkly theme
    fig_teamstat_matches.update_layout(
        title="Match Results by Season",
        xaxis_title="Matchday",
        yaxis_title="",
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
        paper_bgcolor='rgba(40, 44, 52, 1)',  # Dark background
        font=dict(color='white'),  # White font for contrast
        xaxis=dict(
            color='white',            # X-axis color
            gridcolor='rgba(255, 255, 255, 0.1)'  # Light grid lines
        ),
        yaxis=dict(
            color='white',            # Y-axis color
            gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines
            type='category',          # Set y-axis as categorical
            categoryorder='category ascending'  # Order categories ascending
        )
    )


    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_scatter_team',
                    figure=fig_scatter_team
                ), width = 4
            ),
            dbc.Col(
                dcc.Graph(
                    id='fig_teamstat_matches',
                    figure=fig_teamstat_matches
                ), width = 8
            ),
        ])
     ])

def tab_content_overview(df_league_filtered):
    
    df_league_filtered_aggr = df_league_filtered.groupby(['team', 'season'])['points'].sum().reset_index()

    # Create a scatter plot
    fig_scatter = px.scatter(
        df_league_filtered_aggr,
        x='points',  # Teams on the x-axis
        y='team',  # Sum of points on the y-axis
        title='Total Points per Team',
        labels={'points': 'Total Points', 'team': 'Team'},
        color='season',  # Different colors for each season
    )

    fig_scatter.update_layout(
    plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
    paper_bgcolor='rgba(40, 44, 52, 1)',  # Dark background
    font=dict(color='white'),  # White font color for contrast
    title_font=dict(size=20, color='white'),
    xaxis=dict(
        title='Total Points',  # Update x-axis title
        color='white',
        gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines for x-axis
    ),
    yaxis=dict(
        title='Team',  # Update y-axis title
        color='white',
        gridcolor='rgba(255, 255, 255, 0.1)',  # Light grid lines for y-axis
    ),
    showlegend=False  # Hide legend if not needed
    )

    return dbc.Container([
        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    id='fig_scatter_teamcomparison',
                    figure=fig_scatter
                ), width = 8
            ),
        ])
     ])


if __name__ == '__main__':
    app.run_server(debug=True)