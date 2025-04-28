import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import pgeocode
import logging

# for debug purpose
logging.basicConfig(level=logging.INFO)

# Load the processed dataset
path = '../../data/processed/processed_vehicles_task02_final.csv'
df = pd.read_csv(path)

# Ensure ZIP Code is treated as a string
df['ZIP Code'] = df['ZIP Code'].astype(str).str.split('.').str[0]  # Remove decimal part if any

# Replace 'unknown' or invalid ZIP codes with None
df['ZIP Code'] = df['ZIP Code'].replace(['unknown', 'nan', 'None', '0'], None)

# Log unique ZIP codes for debugging
logging.info(f"Unique ZIP Codes: {df['ZIP Code'].nunique()} unique codes")

# Add latitude and longitude based on ZIP Code if not already present
if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
    logging.info("Adding Latitude and Longitude based on ZIP Code...")
    nomi = pgeocode.Nominatim('us')  # Use 'us' for United States ZIP Codes

    # Unique ZIP codes only
    unique_zips = df['ZIP Code'].dropna().unique()

    # Create a lookup table
    zip_location = {zip_code: nomi.query_postal_code(zip_code) for zip_code in unique_zips}
    lat_lookup = {k: v.latitude for k, v in zip_location.items()}
    lon_lookup = {k: v.longitude for k, v in zip_location.items()}

    # Map latitude and longitude
    df['Latitude'] = df['ZIP Code'].map(lat_lookup)
    df['Longitude'] = df['ZIP Code'].map(lon_lookup)

    logging.info(f"Sample Latitude and Longitude:\n{df[['ZIP Code', 'Latitude', 'Longitude']].head()}")

# Drop rows with missing latitude or longitude
logging.info(f"DataFrame shape before dropping missing lat/lon: {df.shape}")
df = df.dropna(subset=['Latitude', 'Longitude'])
logging.info(f"DataFrame shape after dropping missing lat/lon: {df.shape}")

# Precompute 'Wheelchair Accessible Label'
df['Wheelchair Accessible Label'] = df['Wheelchair Accessible'].map({'Y': 'Yes', 'N': 'No'})

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Vehicle Dashboard"

# Layout of the dashboard with style enhancements
app.layout = html.Div([
    html.H1("Vehicle Dashboard", style={'textAlign': 'center', 'color': '#4CAF50', 'font-family': 'Arial'}),  # Updated title style

    html.Div([
        html.Div([
            html.Label("Filter by Vehicle Make:", style={'fontWeight': 'bold', 'fontSize': '14px'}),
            dcc.Dropdown(
                id='make-filter',
                options=[{'label': make, 'value': make} for make in df['Vehicle Make'].dropna().unique()],
                placeholder="Select a vehicle make",
                multi=True,
                style={'backgroundColor': '#f4f4f4', 'border': '1px solid #ccc'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by Vehicle Type:", style={'fontWeight': 'bold', 'fontSize': '14px'}),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': vtype, 'value': vtype} for vtype in df['Vehicle Type'].dropna().unique()],
                placeholder="Select a vehicle type",
                multi=True,
                style={'backgroundColor': '#f4f4f4', 'border': '1px solid #ccc'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by Vehicle Fuel Source:", style={'fontWeight': 'bold', 'fontSize': '14px'}),
            dcc.Dropdown(
                id='fuel-source-filter',
                options=[{'label': fuel, 'value': fuel} for fuel in df['Vehicle Fuel Source'].dropna().unique()],
                placeholder="Select a fuel source",
                multi=True,
                style={'backgroundColor': '#f4f4f4', 'border': '1px solid #ccc'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Filter by City:", style={'fontWeight': 'bold', 'fontSize': '14px'}),
            dcc.Dropdown(
                id='city-filter',
                options=[{'label': city, 'value': city} for city in df['City'].dropna().unique()],
                placeholder="Select a city",
                multi=True,
                style={'backgroundColor': '#f4f4f4', 'border': '1px solid #ccc'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'})
    ], style={'display': 'flex', 'justify-content': 'space-between', 'padding': '20px'}),  # Added padding and alignment

    dcc.Tabs([
        dcc.Tab(label='Vehicle Type Distribution', children=[dcc.Graph(id='vehicle-type-chart')]),
        dcc.Tab(label='Fuel Source Distribution', children=[dcc.Graph(id='fuel-source-chart')]),
        dcc.Tab(label='Fuel Source Requirements', children=[dcc.Graph(id='fuel-req-chart')]),
        dcc.Tab(label='Wheelchair Accessibility', children=[dcc.Graph(id='wheelchair-accessibility-chart')]),
        dcc.Tab(label='Vehicle Make Distribution', children=[dcc.Graph(id='vehicle-make-pie-chart')]),
        dcc.Tab(label='Vehicle Count by Model Year', children=[dcc.Graph(id='model-year-line-chart')]),
        dcc.Tab(label='Geographical Distribution', children=[dcc.Graph(id='geo-distribution-chart')])
    ], style={'fontSize': '16px', 'fontFamily': 'Arial'})  # Adjusted font size for tabs
], style={'backgroundColor': '#fafafa', 'padding': '20px'})  # Overall background color and padding

# Callback to update charts remains unchanged
@app.callback(
    [Output('vehicle-type-chart', 'figure'),
     Output('fuel-source-chart', 'figure'),
     Output('wheelchair-accessibility-chart', 'figure'),
     Output('vehicle-make-pie-chart', 'figure'),
     Output('model-year-line-chart', 'figure'),
     Output('fuel-req-chart', 'figure'),
     Output('geo-distribution-chart', 'figure')],
    [Input('make-filter', 'value'),
     Input('type-filter', 'value'),
     Input('fuel-source-filter', 'value'),
     Input('city-filter', 'value')]
)
def update_charts(selected_makes, selected_types, selected_fuel_sources, selected_cities):
    filtered_df = df.copy()

    if selected_makes:
        filtered_df = filtered_df[filtered_df['Vehicle Make'].isin(selected_makes)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['Vehicle Type'].isin(selected_types)]
    if selected_fuel_sources:
        filtered_df = filtered_df[filtered_df['Vehicle Fuel Source'].isin(selected_fuel_sources)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df['City'].isin(selected_cities)]

    # Vehicle Type distribution
    vehicle_type_fig = px.histogram(
        filtered_df, x='Vehicle Type', color='Vehicle Type',
        title="Vehicle Type Distribution"
    )

    # Fuel Source distribution
    fuel_source_fig = px.histogram(
        filtered_df, x='Vehicle Fuel Source', color='Vehicle Fuel Source',
        title="Fuel Source Distribution"
    )

    # Wheelchair Accessibility pie
    wheelchair_fig = px.pie(
        filtered_df, names='Wheelchair Accessible Label',
        title="Wheelchair Accessibility",
        color_discrete_map={'Yes': 'green', 'No': 'red'}
    )

    # Vehicle Make Pie chart
    make_counts = filtered_df['Vehicle Make'].value_counts()
    threshold = 0.02 * len(filtered_df)
    filtered_df['Vehicle Make Grouped'] = filtered_df['Vehicle Make'].apply(
        lambda x: x if make_counts[x] > threshold else 'Other'
    )
    vehicle_make_pie_fig = px.pie(
        filtered_df, names='Vehicle Make Grouped', title="Top Vehicle Makers"
    )

    # Vehicle Model Year Line Chart
    model_year_fig = px.line(
        filtered_df.groupby('Vehicle Model Year').size().reset_index(name='Count'),
        x='Vehicle Model Year', y='Count',
        title="Vehicle Count by Model Year"
    )

    # Animated Fuel Requirements Bar
    fuel_req_fig = px.bar(
        filtered_df.groupby(['Vehicle Fuel Source', 'Status', 'Vehicle Model Year'])
                   .size()
                   .reset_index(name='Count')
                   .sort_values(by='Vehicle Model Year'),
        x='Vehicle Fuel Source', y='Count',
        color='Status',
        animation_frame='Vehicle Model Year',
        animation_group='Vehicle Fuel Source',
        title="Vehicle Fuel Source Requirements"
    )

    # Geographical Distribution Scatter Map
    geo_distribution_fig = px.scatter_mapbox(
        filtered_df,
        lat='Latitude',
        lon='Longitude',
        color='Vehicle Type',
        size='Vehicle Model Year',
        hover_name='Vehicle Make',
        hover_data=['City', 'State'],
        mapbox_style="carto-positron",
        zoom=5,
        title="Geographical Distribution of Vehicles"
    )

    return (vehicle_type_fig, fuel_source_fig, wheelchair_fig,
            vehicle_make_pie_fig, model_year_fig, fuel_req_fig, geo_distribution_fig)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
