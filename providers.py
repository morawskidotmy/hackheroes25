"""
MEVO Bike Provider - Polish bike sharing (GBFS)
"""

import requests
import math
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance using Haversine formula (in km)."""
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


class MEVOProvider:
    """MEVO - Polish bike sharing (GBFS)."""
    
    def __init__(self):
        self.base_url = "https://gbfs.urbansharing.com/rowermevo.pl"
        self.timeout = 5
        self.client_identifier = "hackheroes-co2calculator"
    
    def name(self) -> str:
        return "MEVO"
    
    def get_vehicles(self, latitude: float, longitude: float, radius: float) -> List[Dict]:
        """Get MEVO bikes within radius."""
        try:
            vehicles = []
            
            # Get station info
            info_resp = requests.get(
                f"{self.base_url}/station_information.json",
                headers={"Client-Identifier": self.client_identifier},
                timeout=self.timeout
            )
            info_resp.raise_for_status()
            station_info = info_resp.json()
            
            # Get station status
            status_resp = requests.get(
                f"{self.base_url}/station_status.json",
                headers={"Client-Identifier": self.client_identifier},
                timeout=self.timeout
            )
            status_resp.raise_for_status()
            station_status = status_resp.json()
            
            # Create status map
            status_map = {}
            for station in station_status['data']['stations']:
                status_map[station['station_id']] = {
                    'bikes': station['num_bikes_available'],
                    'docks': station['num_docks_available'],
                    'renting': station['is_renting'] == 1
                }
            
            # Process stations
            for station in station_info['data']['stations']:
                status = status_map.get(station['station_id'], {})
                
                if status.get('bikes', 0) == 0:
                    continue
                
                distance = calculate_distance(latitude, longitude, station['lat'], station['lon'])
                if distance > radius:
                    continue
                
                vehicles.append({
                    'id': station['station_id'],
                    'type': 'bike',
                    'provider': self.name(),
                    'name': station['name'],
                    'location': {'latitude': station['lat'], 'longitude': station['lon']},
                    'distance_km': round(distance, 2),
                    'bikes_available': status.get('bikes', 0),
                    'docks_available': status.get('docks', 0),
                    'is_available': True
                })
            
            return vehicles
        
        except Exception as e:
            logger.error(f"MEVO error: {e}")
            return []
