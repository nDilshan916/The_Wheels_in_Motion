import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Load the processed dataset
path = 'data/processed/processed_vehicles_task02_final.csv'
df = pd.read_csv(path)

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Vehicle Dashboard"

# Layout of the dashboard
app.layout = html.Div([
    html.H1("Vehicle Dashboard", style={'textAlign': 'center'}),

    # Filters in one row
    html.Div([
        html.Div([
            html.Label("Filter by Vehicle Make:"),
            dcc.Dropdown(
                id='make-filter',
                options=[{'label': make, 'value': make} for make in df['Vehicle Make'].unique()],
                value=None,
                placeholder="Select a vehicle make",
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by Vehicle Type:"),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': vtype, 'value': vtype} for vtype in df['Vehicle Type'].unique()],
                value=None,
                placeholder="Select a vehicle type",
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by Vehicle Fuel Source:"),
            dcc.Dropdown(
                id='fuel-source-filter',
                options=[{'label': fuel, 'value': fuel} for fuel in df['Vehicle Fuel Source'].unique()],
                value=None,
                placeholder="Select a fuel source",
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by City:"),
            dcc.Dropdown(
                id='city-filter',
                options=[{'label': city, 'value': city} for city in df['City'].unique()],
                value=None,
                placeholder="Select a city",
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),


    html.Div([
        # Vehicle Type distribution chart
        html.Div([
            dcc.Graph(id='vehicle-type-chart')
        ], style={'width': '50%', 'display': 'inline-block'}),

        # Fuel Source distribution chart
        html.Div([
            dcc.Graph(id='fuel-source-chart')
        ], style={'width': '50%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),
    
    # Fule source requirements chart
    html.Div([
        dcc.Graph(id='fuel-req-chart')
    ]),

    # Two pie charts in one row
    html.Div([
        html.Div([
            dcc.Graph(id='wheelchair-accessibility-chart')
        ], style={'width': '40%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='vehicle-make-pie-chart')
        ], style={'width': '60%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),

    # Line chart for Vehicle Model Year
    html.Div([
        dcc.Graph(id='model-year-line-chart')
    ])
])

# Callback to update charts based on filters
@app.callback(
    [Output('vehicle-type-chart', 'figure'),
     Output('fuel-source-chart', 'figure'),
     Output('wheelchair-accessibility-chart', 'figure'),
     Output('vehicle-make-pie-chart', 'figure'),
     Output('model-year-line-chart', 'figure'),
     Output('fuel-req-chart', 'figure')],
    [Input('make-filter', 'value'),
     Input('type-filter', 'value'),
     Input('fuel-source-filter', 'value'),
     Input('city-filter', 'value')]
)
def update_charts(selected_makes, selected_types,selected_fuel_sources, selected_cities, ):
    # Filter data based on selected filters
    filtered_df = df
    if selected_makes:
        filtered_df = filtered_df[filtered_df['Vehicle Make'].isin(selected_makes)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['Vehicle Type'].isin(selected_types)]
    if selected_fuel_sources:
        filtered_df = filtered_df[filtered_df['Vehicle Fuel Source'].isin(selected_fuel_sources)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]
    

    # Vehicle Type distribution chart
    vehicle_type_fig = px.histogram(
        filtered_df, x='Vehicle Type', color='Vehicle Type',
        title="Vehicle Type Distribution",
        labels={'Vehicle Type': 'Vehicle Type'}
    )

    # Fuel Source distribution chart
    fuel_source_fig = px.histogram(
        filtered_df, x='Vehicle Fuel Source', color='Vehicle Fuel Source',
        title="Fuel Source Distribution",
        labels={'Vehicle Fuel Source': 'Fuel Source'}
    )

    # Wheelchair Accessibility chart
    wheelchair_fig = px.pie(
        filtered_df, names='Wheelchair Accessible', title="Wheelchair Accessibility",
        color='Wheelchair Accessible',
        color_discrete_map={'Y': 'green', 'N': 'red'},
        labels={'Y': 'Yes', 'N': 'No'}
    )

    # Group less frequent vehicle makes into "Other"
    make_counts = filtered_df['Vehicle Make'].value_counts()
    threshold = 0.02 * len(filtered_df)  # Set threshold as 2% of the total data
    filtered_df['Vehicle Make Grouped'] = filtered_df['Vehicle Make'].apply(
        lambda x: x if make_counts[x] > threshold else 'Other'
    )

    # Pie chart for Vehicle Make distribution
    vehicle_make_pie_fig = px.pie(
        filtered_df, names='Vehicle Make Grouped', title="Top Vehicle Makers",
        color='Vehicle Make Grouped'
    )

    # Line chart for Vehicle Model Year
    model_year_fig = px.line(
        filtered_df.groupby('Vehicle Model Year').size().reset_index(name='Count'),
        x='Vehicle Model Year', y='Count',
        title="Vehicle Count by Model Year",
        labels={'Vehicle Model Year': 'Model Year', 'Count': 'Vehicle Count'}
    )
    
    # Animated Bar chart for vehicle fule source requirements
    fuel_req_fig = px.bar(
        data_frame=filtered_df.groupby(['Vehicle Fuel Source','Status','Vehicle Model Year'])
        .size().reset_index(name='Count').sort_values(by='Vehicle Model Year'),
        x='Vehicle Fuel Source', 
        y='Count',
        color='Status',
        animation_frame='Vehicle Model Year',
        animation_group='Vehicle Fuel Source',
        # range_y=(0, 500),
        title="Vehicle Fuel Source Requirements",
        labels={'Vehicle Fuel Source': 'Fuel Source', 'Count': 'Count', 'Status': 'Status'}
    )
    
    # Customize animation settings for replay and slow motion
    fuel_req_fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [None, {"frame": {"duration": 1500, "redraw": True}, "fromcurrent": True}],
                        "label": "Play",
                        "method": "animate"
                    },
                    {
                        "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                        "label": "Pause",
                        "method": "animate"
                    }
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": True,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top"
            }
        ],
        sliders=[
            {
                "steps": [
                    {
                        "args": [[frame["name"]], {"frame": {"duration": 1000, "redraw": True}, "mode": "immediate", "transition": {"duration": 300}}],
                        "label": str(frame["name"]),
                        "method": "animate",
                    }
                    for frame in fuel_req_fig.frames
                ],
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {
                    "font": {"size": 20},
                    "prefix": "Year:",
                    "visible": True,
                    "xanchor": "right"
                },
                "transition": {"duration": 300},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
            }
        ]
    )

    return vehicle_type_fig, fuel_source_fig, wheelchair_fig, vehicle_make_pie_fig, model_year_fig, fuel_req_fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)