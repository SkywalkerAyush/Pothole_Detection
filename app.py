#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # allow cross-origin JS fetches

# In-memory store for the most recent GPS coords
latest_coords = {
    'latitude': None,
    'longitude': None
}

@app.route('/')
def index():
    # Renders templates/index.html
    return render_template('index.html')

@app.route('/location', methods=['POST'])
def post_location():
    """
    Receives JSON { latitude: float, longitude: float } from the phone
    via JavaScript fetch, and stores it in latest_coords.
    """
    data = request.get_json(force=True)
    lat = data.get('latitude')
    lon = data.get('longitude')
    if lat is None or lon is None:
        return jsonify(error="Missing latitude or longitude"), 400

    # Update the shared state
    latest_coords['latitude']  = lat
    latest_coords['longitude'] = lon
    app.logger.info(f"[GPS POST] latitude={lat}, longitude={lon}")
    return jsonify(status='ok'), 200

@app.route('/gps', methods=['GET'])
def get_location():
    """
    Returns the last-stored coords as { lat: ..., lon: ... }.
    The RPi’s MPU code should hit this endpoint.
    """
    lat = latest_coords['latitude']
    lon = latest_coords['longitude']
    app.logger.info(f"[GPS GET] returning lat={lat}, lon={lon}")
    return jsonify(lat=lat, lon=lon), 200

if __name__ == '__main__':
    # Change debug=True for hot-reloads and more verbose logs during dev
    app.run(host='0.0.0.0', port=5000, debug=True)
