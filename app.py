"""
CO2 Bike Calculator API - Flask Application
Main API server for calculating CO2 savings when choosing bikes over cars
Focused on MEVO - Polish bike sharing system
"""

import math
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from providers import MEVOProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CO2_PER_KM_CAR = 0.12  # kg of CO2 per km for a car
BIKE_SPEED_KPH = 15.0
CAR_SPEED_KPH = 40.0
DEFAULT_RADIUS = 2.0

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize provider
provider = MEVOProvider()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371.0  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def calculate_co2_savings(distance_km: float) -> float:
    """Calculate CO2 savings in kg based on distance."""
    return distance_km * CO2_PER_KM_CAR


def format_travel_time(hours: float) -> str:
    """Convert hours to readable time format."""
    minutes = int(hours * 60)
    
    if minutes < 60:
        return f"{minutes} minutes"
    
    hours_int = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours_int} hour" if hours_int == 1 else f"{hours_int} hours"
    
    hour_str = "1 hour" if hours_int == 1 else f"{hours_int} hours"
    return f"{hour_str} {remaining_minutes} minutes"


def validate_coordinates(lat: float, lon: float) -> tuple[bool, str]:
    """Validate latitude and longitude bounds."""
    if lat < -90 or lat > 90:
        return False, "Latitude must be between -90 and 90"
    if lon < -180 or lon > 180:
        return False, "Longitude must be between -180 and 180"
    return True, ""


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'OK',
        'provider': provider.name()
    }), 200


@app.route('/v1/calculate-co2-savings', methods=['POST'])
def calculate_co2():
    """
    Main endpoint: Calculate CO2 savings for a bike trip.
    
    Request body:
    {
        "latitude": float (required),
        "longitude": float (required),
        "destination_latitude": float (required),
        "destination_longitude": float (required),
        "radius": float (optional, default 2.0)
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['latitude', 'longitude', 'destination_latitude', 'destination_longitude']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # Extract and validate coordinates
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        dest_lat = float(data['destination_latitude'])
        dest_lon = float(data['destination_longitude'])
        radius = float(data.get('radius', DEFAULT_RADIUS))
        
        # Validate bounds
        is_valid, error_msg = validate_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        is_valid, error_msg = validate_coordinates(dest_lat, dest_lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Get vehicles from MEVO
        vehicles = provider.get_vehicles(lat, lon, radius)
        
        # Calculate distance
        distance = calculate_distance(lat, lon, dest_lat, dest_lon)
        
        # Calculate CO2 savings
        co2_savings = calculate_co2_savings(distance)
        
        # Calculate travel times
        bike_time = format_travel_time(distance / BIKE_SPEED_KPH)
        car_time = format_travel_time(distance / CAR_SPEED_KPH)
        
        # Select closest vehicle or return success without vehicle
        closest_vehicle = vehicles[0] if vehicles else None
        
        response = {
            'success': True,
            'distance_km': round(distance, 2),
            'co2_savings_kg': round(co2_savings, 3),
            'travel_times': {
                'bike_minutes': bike_time,
                'car_minutes': car_time
            },
            'environmental_impact': {
                'co2_per_km_car_grams': 120,
                'co2_saved_grams': int(co2_savings * 1000),
                'equivalent_trees': round(co2_savings / 0.021, 2)
            }
        }
        
        if closest_vehicle:
            response['closest_vehicle'] = closest_vehicle
            response['message'] = f"By choosing a {closest_vehicle['type']} instead of a car for this {distance:.2f}km trip, you save approximately {co2_savings:.2f}kg of CO2 emissions!"
        else:
            response['message'] = f"No bikes found in your area. For a {distance:.2f}km trip, you would save {co2_savings:.2f}kg of CO2 by choosing a bike instead of a car!"
        
        return jsonify(response), 200
    
    except ValueError as e:
        return jsonify({'error': 'Invalid input data', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in calculate_co2: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/v1/nearby-stations', methods=['GET'])
def nearby_stations():
    """
    Get nearby MEVO bike stations.
    
    Query parameters:
    - latitude: float (required)
    - longitude: float (required)
    - radius: float (optional, default 1.0)
    """
    try:
        # Extract query parameters
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 1.0, type=float)
        
        # Validate required parameters
        if lat is None or lon is None:
            return jsonify({'error': 'Missing latitude or longitude'}), 400
        
        # Validate bounds
        is_valid, error_msg = validate_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Get vehicles from MEVO
        vehicles = provider.get_vehicles(lat, lon, radius)
        
        return jsonify({
            'success': True,
            'count': len(vehicles),
            'stations': vehicles
        }), 200
    
    except Exception as e:
        logger.error(f"Error in nearby_stations: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Serve index page."""
    try:
        with open('index.html', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'Index file not found'}), 404


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 3000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    logger.info(f"Starting CO2 Bike Calculator API on port {port}")
    logger.info(f"Provider: {provider.name()}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
