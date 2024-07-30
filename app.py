from flask import Flask, render_template, jsonify, request
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# tell the app that its behind a proxy and should use a middleware
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Correct URLs of the GeoJSON data for different years from S3 bucket
geojson_url_2021 = "https://ht-interactive-map.s3.us-west-2.amazonaws.com/kenya/cleaned-up-data-silver-layer/KENYA/2021_transformed.geojson"
geojson_url_2022 = "https://ht-interactive-map.s3.us-west-2.amazonaws.com/kenya/cleaned-up-data-silver-layer/KENYA/2022_transformed.geojson"
geojson_url_2023 = "https://ht-interactive-map.s3.us-west-2.amazonaws.com/kenya/cleaned-up-data-silver-layer/KENYA/22023_transformed.geojson"

# Function to fetch GeoJSON data
def fetch_geojson(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching GeoJSON: {response.status_code} {response.reason}")
        return None

# Fetch GeoJSON data for all years
geojson_data = {
    '2021': fetch_geojson(geojson_url_2021),
    '2022': fetch_geojson(geojson_url_2022),
    '2023': fetch_geojson(geojson_url_2023)
}

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/definition')
def definition():
    return render_template('definition.html')

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML page with the map

@app.route('/update_map', methods=['POST'])
def update_map():
    selected_year = request.json['year']  # Get selected year from JSON POST data
    selected_month = request.json['month']  # Get selected month from JSON POST data
    
    if selected_year in geojson_data and geojson_data[selected_year] is not None:
        selected_geojson_data = geojson_data[selected_year]
        filtered_features = [feature for feature in selected_geojson_data['features'] if feature['properties']['month'] == int(selected_month)]
        
        data_to_send = []
        for feature in filtered_features:
            properties = feature['properties']
            data_to_send.append({
                'latitude': properties['latitude'],
                'longitude': properties['longitude'],
                'popup_content': f"""
                    <div style='max-width: 300px;'>
                        <div data-name="County"><strong>County:</strong> {properties['County']}</div>
                        <div data-name="Subcounty"><strong>Subcounty:</strong> {properties['Subcounty']}</div>
                        <div data-name="Ward"><strong>Ward:</strong> {properties['wards']}</div>
                        <div data-name="Month"><strong>Month:</strong> {properties['month']}</div>
                        <div data-name="Year"><strong>Year:</strong> {properties['year']}</div>
                        <div data-name="Temp(mean)"><strong>Temp(mean):</strong> {properties['Temperature_mean']}</div>
                        <div data-name="NDVI-5"><strong>NDVI-5:</strong> {properties['NVDI 5 PERCENTILE']}</div>
                        <div data-name="NDVI-50"><strong>NDVI-50:</strong> {properties['NVDI 50 PERCENTILE']}</div>
                        <div data-name="NDVI-95"><strong>NDVI-95:</strong> {properties['NVDI 95 PERCENTILE']}</div>
                        <div data-name="NDVI-25"><strong>NDVI-25:</strong> {properties['NVDI 25 PERCENTILE']}</div>
                        <div data-name="NDVI (max)"><strong>NVDI (max):</strong> {properties['NVDI (max)']}</div>
                        <div data-name="NDVI (min)"><strong>NVDI (min):</strong> {properties['NVDI(min)']}</div>
                        <div data-name="NDVI (mean)"><strong>NVDI (mean):</strong> {properties['NVDI(MEAN)']}</div>
                        <div data-name="Rainfall"><strong>Rainfall:</strong> {properties['Rainfall-Precipitataion(mean)']}</div>
                        <div data-name="Landcover"><strong>Landcover:</strong> {properties['LANDCOVER(GFSAD)']}</div>
                        <div data-name="Worldcover (ESA)"><strong>Worldcover (ESA):</strong> {properties['WORLDCOVERCOVER(ESA)']}</div>
                        <div data-name="Agric-Occupation"><strong>Agric-Occupation:</strong> {properties['Agriculture_occupation']}</div>
                        <div data-name="Population"><strong>Population:</strong> {properties['Population']}</div>
                        <div data-name="Avg-Agri-Pop"><strong>Avg-Agri-Pop:</strong> {properties['Average Agriculturepopulation']}</div>
                    </div>
                """
            })
        
        return jsonify(data_to_send)
    
    else:
        return jsonify([])

@app.route('/search_wards', methods=['GET'])
def search_counties():
    query = request.args.get('query').lower()
    results = []

    for year, data in geojson_data.items():
        if data is not None:
            for feature in data['features']:
                if query in feature['properties']['wards'].lower():
                    results.append({
                        'latitude': feature['geometry']['coordinates'][1],
                        'longitude': feature['geometry']['coordinates'][0],
                        'wards': feature['properties']['wards']
                    })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
