"""
CO2 Bike Calculator API - Flask Application
Main API server for calculating CO2 savings when choosing bikes over cars
Focused on MEVO - Polish bike sharing system
"""

import math
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from providers import MEVOProvider
from io import BytesIO
from datetime import datetime
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_AVAILABLE = SUPABASE_URL and SUPABASE_KEY
    if SUPABASE_AVAILABLE:
        supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase_client = None
except ImportError:
    SUPABASE_AVAILABLE = False
    supabase_client = None

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


@app.route('/v1/search-nearest-station', methods=['GET'])
def search_nearest_station():
    """
    Search for nearest MEVO bike station.
    
    Query parameters:
    - latitude: float (required)
    - longitude: float (required)
    - radius: float (optional, default 2.0)
    """
    try:
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        radius = request.args.get('radius', 2.0, type=float)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Missing latitude or longitude'}), 400
        
        is_valid, error_msg = validate_coordinates(lat, lon)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        vehicles = provider.get_vehicles(lat, lon, radius)
        
        if not vehicles:
            return jsonify({
                'success': True,
                'found': False,
                'message': 'No stations found nearby'
            }), 200
        
        nearest = vehicles[0]
        return jsonify({
            'success': True,
            'found': True,
            'station': {
                'name': nearest.get('name', 'MEVO Station'),
                'latitude': nearest.get('latitude'),
                'longitude': nearest.get('longitude'),
                'bikes_available': nearest.get('bikes_available'),
                'distance_km': nearest.get('distance_km')
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in search_nearest_station: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


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
        "radius": float (optional, default 2.0),
        "user_id": string (optional, for tracking)
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
        user_id = data.get('user_id')
        
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
        
        # Store in Supabase if user_id provided
        calculation_id = None
        if user_id and supabase_client:
            try:
                result = supabase_client.table('co2_calculations').insert({
                    'user_id': user_id,
                    'co2_savings_kg': round(co2_savings, 3),
                    'distance_km': round(distance, 2),
                    'start_lat': lat,
                    'start_lon': lon,
                    'end_lat': dest_lat,
                    'end_lon': dest_lon,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                calculation_id = result.data[0]['id'] if result.data else None
            except Exception as e:
                logger.warning(f"Failed to store calculation: {e}")
        
        response = {
            'success': True,
            'id': calculation_id,
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


@app.route('/v1/save-journey', methods=['POST'])
def save_journey():
    """
    Save a journey with transport choice (bike or car).
    
    Request body:
    {
        "user_id": string (required),
        "latitude": float (required),
        "longitude": float (required),
        "destination_latitude": float (required),
        "destination_longitude": float (required),
        "chosen_transport": string (required, 'bike' or 'car'),
        "nearest_station_name": string (optional),
        "nearest_station_lat": float (optional),
        "nearest_station_lon": float (optional)
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'latitude', 'longitude', 'destination_latitude', 
                          'destination_longitude', 'chosen_transport']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        user_id = data['user_id']
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        dest_lat = float(data['destination_latitude'])
        dest_lon = float(data['destination_longitude'])
        chosen_transport = data['chosen_transport'].lower()
        
        if chosen_transport not in ['bike', 'car']:
            return jsonify({'error': 'chosen_transport must be "bike" or "car"'}), 400
        
        # Calculate distance and potential savings
        distance = calculate_distance(lat, lon, dest_lat, dest_lon)
        potential_co2 = calculate_co2_savings(distance)
        
        if not supabase_client:
            return jsonify({'error': 'Database not available'}), 503
        
        # Save journey
        journey_data = {
            'user_id': user_id,
            'start_lat': lat,
            'start_lon': lon,
            'end_lat': dest_lat,
            'end_lon': dest_lon,
            'distance_km': round(distance, 2),
            'chosen_transport': chosen_transport,
            'potential_co2_savings_kg': round(potential_co2, 3),
            'nearest_station_name': data.get('nearest_station_name'),
            'nearest_station_lat': data.get('nearest_station_lat'),
            'nearest_station_lon': data.get('nearest_station_lon')
        }
        
        result = supabase_client.table('journey_tracking').insert(journey_data).execute()
        
        # Update user stats
        update_user_stats(user_id, chosen_transport, potential_co2)
        
        return jsonify({
            'success': True,
            'journey_id': result.data[0]['id'] if result.data else None,
            'message': f"Journey saved: {chosen_transport.upper()} ({distance:.2f}km)"
        }), 200
    
    except Exception as e:
        logger.error(f"Error in save_journey: {e}")
        return jsonify({'error': 'Failed to save journey', 'details': str(e)}), 500


def update_user_stats(user_id: str, transport: str, co2_saved: float):
    """Update user stats in the user_stats table."""
    try:
        if not supabase_client:
            return
        
        # Get current stats
        result = supabase_client.table('user_stats').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            # Update existing
            current = result.data[0]
            new_co2 = current['total_co2_saved_kg'] + (co2_saved if transport == 'bike' else 0)
            new_bike_count = current['total_bike_journeys'] + (1 if transport == 'bike' else 0)
            new_car_count = current['total_car_journeys'] + (1 if transport == 'car' else 0)
            
            # Determine if net neutral (more CO2 saved than from car journeys)
            estimated_car_co2 = new_car_count * CO2_PER_KM_CAR * 10  # Assume ~10km average
            net_neutral = new_co2 >= estimated_car_co2
            
            supabase_client.table('user_stats').update({
                'total_co2_saved_kg': round(new_co2, 3),
                'total_bike_journeys': new_bike_count,
                'total_car_journeys': new_car_count,
                'net_neutral': net_neutral,
                'last_updated': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
        else:
            # Create new
            net_neutral = transport == 'bike'
            supabase_client.table('user_stats').insert({
                'user_id': user_id,
                'total_co2_saved_kg': round(co2_saved if transport == 'bike' else 0, 3),
                'total_bike_journeys': 1 if transport == 'bike' else 0,
                'total_car_journeys': 1 if transport == 'car' else 0,
                'net_neutral': net_neutral,
                'last_updated': datetime.utcnow().isoformat()
            }).execute()
    except Exception as e:
        logger.warning(f"Failed to update user stats: {e}")


@app.route('/v1/user-stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    """Get total CO2 savings and net neutrality status for a user."""
    try:
        if not supabase_client:
            return jsonify({'error': 'Stats not available'}), 503
        
        # Get user stats
        stats_result = supabase_client.table('user_stats').select(
            '*'
        ).eq('user_id', user_id).execute()
        
        if stats_result.data:
            user_stat = stats_result.data[0]
            total_co2 = user_stat['total_co2_saved_kg']
            bike_journeys = user_stat['total_bike_journeys']
            car_journeys = user_stat['total_car_journeys']
            net_neutral = user_stat['net_neutral']
        else:
            total_co2 = 0
            bike_journeys = 0
            car_journeys = 0
            net_neutral = False
        
        # Also get from co2_calculations for backwards compatibility
        calc_result = supabase_client.table('co2_calculations').select(
            'co2_savings_kg'
        ).eq('user_id', user_id).execute()
        
        legacy_co2 = sum(item['co2_savings_kg'] for item in calc_result.data) if calc_result.data else 0
        legacy_count = len(calc_result.data) if calc_result.data else 0
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_co2_kg': round(total_co2 + legacy_co2, 2),
            'total_co2_grams': int((total_co2 + legacy_co2) * 1000),
            'bike_journeys': bike_journeys,
            'car_journeys': car_journeys,
            'net_neutral': net_neutral,
            'trips_count': legacy_count + bike_journeys + car_journeys,
            'equivalent_trees': round((total_co2 + legacy_co2) / 0.021, 2)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Failed to get stats', 'details': str(e)}), 500


@app.route('/v1/share-graphic/<user_id>', methods=['GET'])
def generate_share_graphic(user_id):
    """Generate a shareable graphic of CO2 savings."""
    try:
        if not PIL_AVAILABLE:
            return jsonify({'error': 'Image generation not available'}), 503
        
        if not supabase_client:
            return jsonify({'error': 'Stats not available'}), 503
        
        # Get user stats
        result = supabase_client.table('co2_calculations').select(
            'co2_savings_kg'
        ).eq('user_id', user_id).execute()
        
        total_co2 = sum(item['co2_savings_kg'] for item in result.data) if result.data else 0
        count = len(result.data) if result.data else 0
        
        # Create image
        width, height = 1200, 630
        image = Image.new('RGB', (width, height), color='#000000')
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to use nice fonts, fall back to default
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            value_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        # Draw background gradient effect (black to dark gray)
        for y in range(height):
            shade = int(20 * (y / height))
            color = (shade, shade, shade)
            draw.rectangle([(0, y), (width, y+1)], fill=color)
        
        # Draw green accent bar
        draw.rectangle([(0, 0), (width, 8)], fill='#00ff00')
        
        # Draw main text
        co2_text = f"{total_co2:.2f}"
        draw.text((width//2, 200), co2_text, fill='#00ff00', font=value_font, anchor="mm")
        
        # Draw label
        draw.text((width//2, 380), "KG CO₂ SAVED", fill='#ffffff', font=label_font, anchor="mm")
        
        # Draw trips count
        trips_text = f"{count} trips"
        draw.text((width//2, 480), trips_text, fill='#888888', font=label_font, anchor="mm")
        
        # Draw branding
        draw.text((width//2, height-50), "co2.bike", fill='#666666', font=label_font, anchor="mm")
        
        # Save to bytes
        img_io = BytesIO()
        image.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
    
    except Exception as e:
        logger.error(f"Error generating graphic: {e}")
        return jsonify({'error': 'Failed to generate graphic', 'details': str(e)}), 500


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
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    logger.info(f"Starting CO2 Bike Calculator API on port {port}")
    logger.info(f"Provider: {provider.name()}")
    logger.info(f"Web interface: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
