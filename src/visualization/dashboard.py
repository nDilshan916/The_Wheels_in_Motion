import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import pgeocode
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load dataset
path = '../../data/processed/processed_vehicles_task02_final.csv'
df = pd.read_csv(path)

# Fix ZIP Code
df['ZIP Code'] = df['ZIP Code'].astype(str).str.split('.').str[0]
df['ZIP Code'] = df['ZIP Code'].replace(['unknown', 'nan', 'None', '0'], None)

# Add lat/lon if not present
if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
    nomi = pgeocode.Nominatim('us')
    unique_zips = df['ZIP Code'].dropna().unique()
    zip_location = {zip_code: nomi.query_postal_code(zip_code) for zip_code in unique_zips}
    lat_lookup = {k: v.latitude for k, v in zip_location.items()}
    lon_lookup = {k: v.longitude for k, v in zip_location.items()}
    df['Latitude'] = df['ZIP Code'].map(lat_lookup)
    df['Longitude'] = df['ZIP Code'].map(lon_lookup)

# Drop rows without lat/lon
df = df.dropna(subset=['Latitude', 'Longitude'])

# Create wheelchair label
df['Wheelchair Accessible Label'] = df['Wheelchair Accessible'].map({'Y': 'Yes', 'N': 'No'})

# Initialize app
app = dash.Dash(__name__)
app.title = "Vehicle Dashboard"

# Define custom styles (New Color Palette)
main_background = '#e6f2ff'   # Light blueish background
card_background = '#ffffff'   # White cards
primary_color = '#0066cc'     # Strong blue (main highlight color)
secondary_color = '#ff6666'   # Coral red (for secondary accents)
accent_color = '#00cc99'      # Mint green (for action buttons or highlights)
text_color = '#333333'        # Dark gray text for better readability


# Layout
app.layout = html.Div([
    html.H1("🚗 Vehicle Insights Dashboard", style={
        'textAlign': 'center', 'color': primary_color, 'fontFamily': 'Arial', 'marginBottom': '20px'
    }),

    html.Div([
        html.Div([
            html.Label("🔍 Vehicle Make", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='make-filter',
                options=[{'label': make, 'value': make} for make in df['Vehicle Make'].dropna().unique()],
                placeholder="Select a make",
                multi=True,
                style={'backgroundColor': '#e3f2fd', 'borderRadius': '8px', 'border': '1px solid #90caf9'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("🚙 Vehicle Type", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='type-filter',
                options=[{'label': vtype, 'value': vtype} for vtype in df['Vehicle Type'].dropna().unique()],
                placeholder="Select type",
                multi=True,
                style={'backgroundColor': '#e8f5e9', 'borderRadius': '8px', 'border': '1px solid #a5d6a7'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("⛽ Fuel Source", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='fuel-source-filter',
                options=[{'label': fuel, 'value': fuel} for fuel in df['Vehicle Fuel Source'].dropna().unique()],
                placeholder="Select fuel source",
                multi=True,
                style={'backgroundColor': '#fff8e1', 'borderRadius': '8px', 'border': '1px solid #ffe082'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("🏙️ City", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='city-filter',
                options=[{'label': city, 'value': city} for city in df['City'].dropna().unique()],
                placeholder="Select city",
                multi=True,
                style={'backgroundColor': '#fce4ec', 'borderRadius': '8px', 'border': '1px solid #f48fb1'}
            )
        ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-between', 'backgroundColor': card_background, 'padding': '20px', 'borderRadius': '12px', 'boxShadow': '0px 4px 8px rgba(0,0,0,0.1)'}),

    dcc.Tabs([
        dcc.Tab(label='Vehicle Type', children=[dcc.Graph(id='vehicle-type-chart')], style={'padding': '10px'}),
        dcc.Tab(label='Fuel Sources', children=[dcc.Graph(id='fuel-source-chart')], style={'padding': '10px'}),
        dcc.Tab(label='Fuel Requirements', children=[dcc.Graph(id='fuel-req-chart')], style={'padding': '10px'}),
        dcc.Tab(label='Accessibility', children=[dcc.Graph(id='wheelchair-accessibility-chart')], style={'padding': '10px'}),
        dcc.Tab(label='Vehicle Makes', children=[dcc.Graph(id='vehicle-make-pie-chart')], style={'padding': '10px'}),
        dcc.Tab(label='Model Years', children=[dcc.Graph(id='model-year-line-chart')], style={'padding': '10px'}),
        dcc.Tab(label='Geo Distribution', children=[dcc.Graph(id='geo-distribution-chart')], style={'padding': '10px'}),
    ], colors={
        'border': secondary_color,
        'primary': primary_color,
        'background': card_background
    }, style={'fontFamily': 'Arial', 'fontSize': '16px', 'marginTop': '20px'})
], style={'backgroundColor': main_background, 'padding': '30px'})

# Callback remains unchanged
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

    vehicle_type_fig = px.histogram(filtered_df, x='Vehicle Type', color='Vehicle Type', title="Vehicle Type Distribution", template='plotly_white')
    fuel_source_fig = px.histogram(filtered_df, x='Vehicle Fuel Source', color='Vehicle Fuel Source', title="Fuel Source Distribution", template='plotly_white')
    wheelchair_fig = px.pie(filtered_df, names='Wheelchair Accessible Label', title="Wheelchair Accessibility", color_discrete_map={'Yes': primary_color, 'No': 'red'}, template='plotly_white')

    make_counts = filtered_df['Vehicle Make'].value_counts()
    threshold = 0.02 * len(filtered_df)
    filtered_df['Vehicle Make Grouped'] = filtered_df['Vehicle Make'].apply(lambda x: x if make_counts[x] > threshold else 'Other')
    vehicle_make_pie_fig = px.pie(filtered_df, names='Vehicle Make Grouped', title="Top Vehicle Makers", template='plotly_white')

    model_year_fig = px.line(filtered_df.groupby('Vehicle Model Year').size().reset_index(name='Count'), x='Vehicle Model Year', y='Count', title="Vehicle Count by Model Year", template='plotly_white')

    fuel_req_fig = px.bar(
        filtered_df.groupby(['Vehicle Fuel Source', 'Status', 'Vehicle Model Year']).size().reset_index(name='Count').sort_values(by='Vehicle Model Year'),
        x='Vehicle Fuel Source', y='Count', color='Status',
        animation_frame='Vehicle Model Year',
        animation_group='Vehicle Fuel Source',
        title="Vehicle Fuel Source Requirements", template='plotly_white'
    )

    geo_distribution_fig = px.scatter_mapbox(
        filtered_df,
        lat='Latitude', lon='Longitude',
        color='Vehicle Type', size='Vehicle Model Year',
        hover_name='Vehicle Make',
        hover_data=['City', 'State'],
        mapbox_style="carto-positron", zoom=4,
        title="Geographical Distribution", template='plotly_white'
    )

    return (vehicle_type_fig, fuel_source_fig, wheelchair_fig, vehicle_make_pie_fig, model_year_fig, fuel_req_fig, geo_distribution_fig)

# Run
if __name__ == '__main__':
    app.run(debug=True)
