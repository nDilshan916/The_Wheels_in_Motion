import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import pgeocode

# for debug purpose
import logging
logging.basicConfig(level=logging.INFO)

# Load the processed dataset
path = 'data/processed/processed_vehicles_task02_final.csv'
df = pd.read_csv(path)

# Ensure ZIP Code is treated as a string
df['ZIP Code'] = df['ZIP Code'].astype(str).str.split('.').str[0]  # Remove decimal part if any

# Replace 'unknown' or invalid ZIP codes with None
df['ZIP Code'] = df['ZIP Code'].replace(['unknown', 'nan', 'None', '0'], None)

# Log unique ZIP codes for debugging
logging.info(f"Unique ZIP Codes: {df['ZIP Code'].unique()}")

# Add latitude and longitude based on ZIP Code if not already present
if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
    logging.info("Adding Latitude and Longitude based on ZIP Code. Wait...")
    nomi = pgeocode.Nominatim('us')  # Use 'us' for United States ZIP Codes

    # Apply geocoding
    df['Latitude'] = df['ZIP Code'].apply(lambda x: nomi.query_postal_code(x).latitude if pd.notna(x) else None)
    df['Longitude'] = df['ZIP Code'].apply(lambda x: nomi.query_postal_code(x).longitude if pd.notna(x) else None)

    # Log the first few rows of latitude and longitude for debugging
    logging.info(f"Sample Latitude and Longitude: {df[['ZIP Code', 'Latitude', 'Longitude']].head()}")

# Drop rows with missing latitude or longitude
logging.info(f"DataFrame shape before dropping missing lat/lon: {df.shape}")
df = df.dropna(subset=['Latitude', 'Longitude'])
logging.info(f"DataFrame shape after dropping missing lat/lon: {df.shape}")

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Vehicle Dashboard"

# Layout of the dashboard
app.layout = html.Div([
    html.H1("Vehicle Dashboard", style={'textAlign': 'center'}),

    # Filters at the top
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
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by Vehicle Type:"),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': vtype, 'value': vtype} for vtype in df['Vehicle Type'].unique()],
                value=None,
                placeholder="Select a vehicle type",
                multi=True
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by Vehicle Fuel Source:"),
            dcc.Dropdown(
                id='fuel-source-filter',
                options=[{'label': fuel, 'value': fuel} for fuel in df['Vehicle Fuel Source'].unique()],
                value=None,
                placeholder="Select a fuel source",
                multi=True
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by City:"),
            dcc.Dropdown(
                id='city-filter',
                options=[{'label': city, 'value': city} for city in df['City'].unique()],
                value=None,
                placeholder="Select a city",
                multi=True
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'})
    ], style={'display': 'flex', 'justify-content': 'space-between'}),

    # Tabs for charts
    dcc.Tabs([
        dcc.Tab(label='Vehicle Type Distribution', children=[
            dcc.Graph(id='vehicle-type-chart')
        ]),
        dcc.Tab(label='Fuel Source Distribution', children=[
            dcc.Graph(id='fuel-source-chart')
        ]),
        dcc.Tab(label='Fuel Source Requirements', children=[
            dcc.Graph(id='fuel-req-chart')
        ]),
        dcc.Tab(label='Wheelchair Accessibility', children=[
            dcc.Graph(id='wheelchair-accessibility-chart')
        ]),
        dcc.Tab(label='Vehicle Make Distribution', children=[
            dcc.Graph(id='vehicle-make-pie-chart')
        ]),
        dcc.Tab(label='Vehicle Count by Model Year', children=[
            dcc.Graph(id='model-year-line-chart')
        ]),
        dcc.Tab(label='Geographical Distribution', children=[
            dcc.Graph(id='geo-distribution-chart')  # Add the map here
        ])
    ])
])

# Callback to update charts based on filters
@app.callback(
    [Output('vehicle-type-chart', 'figure'),
     Output('fuel-source-chart', 'figure'),
     Output('wheelchair-accessibility-chart', 'figure'),
     Output('vehicle-make-pie-chart', 'figure'),
     Output('model-year-line-chart', 'figure'),
     Output('fuel-req-chart', 'figure'),
     Output('geo-distribution-chart', 'figure')],  # Add new output for the map
    [Input('make-filter', 'value'),
     Input('type-filter', 'value'),
     Input('fuel-source-filter', 'value'),
     Input('city-filter', 'value')]
)
def update_charts(selected_makes, selected_types, selected_fuel_sources, selected_cities):
    # DEBUG: Log the selected filters
    logging.info(f"Selected Makes: {selected_makes}")
    logging.info(f"Selected Types: {selected_types}")
    logging.info(f"Selected Fuel Sources: {selected_fuel_sources}")
    logging.info(f"Selected Cities: {selected_cities}")
    
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

    logging.info(f"Filtered DataFrame shape: {filtered_df.shape}")
    
    assert 'Latitude' in filtered_df.columns, "Latitude column is missing in the filtered DataFrame"
    assert 'Longitude' in filtered_df.columns, "Longitude column is missing in the filtered DataFrame"
    
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
    filtered_df['Wheelchair Accessible Label'] = filtered_df['Wheelchair Accessible'].map({'Y': 'Yes', 'N': 'No'})
    wheelchair_fig = px.pie(
        filtered_df, names='Wheelchair Accessible Label', title="Wheelchair Accessibility",
        color='Wheelchair Accessible Label',
        color_discrete_map={'Yes': 'green', 'No': 'red'}
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

    # Animated Bar chart for vehicle fuel source requirements
    fuel_req_fig = px.bar(
        data_frame=filtered_df.groupby(['Vehicle Fuel Source', 'Status', 'Vehicle Model Year'])
                              .size()
                              .reset_index(name='Count')
                              .sort_values(by='Vehicle Model Year'),
        x='Vehicle Fuel Source',
        y='Count',
        color='Status',
        animation_frame='Vehicle Model Year',
        animation_group='Vehicle Fuel Source',
        title="Vehicle Fuel Source Requirements",
        labels={'Vehicle Fuel Source': 'Fuel Source', 'Count': 'Count', 'Status': 'Status'}
    )

    # Geographical distribution chart
    geo_distribution_fig = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude',
        color='Vehicle Type',
        size='Vehicle Model Year',  # Optional: Adjust size based on a column
        hover_name='Vehicle Make',
        hover_data=['City', 'State'],
        title="Geographical Distribution of Vehicles",
        mapbox_style="carto-positron",
        zoom=6
    )

    return vehicle_type_fig, fuel_source_fig, wheelchair_fig, vehicle_make_pie_fig, model_year_fig, fuel_req_fig, geo_distribution_fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)