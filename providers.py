import requests
import math
from typing import List, Dict, Tuple
import logging
from cachetools import TTLCache
from datetime import datetime

logger = logging.getLogger(__name__)

mevo_cache = TTLCache(maxsize=100, ttl=300)
routing_cache = TTLCache(maxsize=500, ttl=600)

def oblicz_dystans_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def oblicz_dystans_osrm(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    cache_key = f"{lon1},{lat1};{lon2},{lat2}"
    
    if cache_key in routing_cache:
        return routing_cache[cache_key]
    
    try:
        response = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 'Ok' and data.get('routes'):
            dystans_km = data['routes'][0]['distance'] / 1000
            czas_sekund = data['routes'][0]['duration']
            czas_godzin = czas_sekund / 3600
            
            routing_cache[cache_key] = (dystans_km, czas_godzin)
            return dystans_km, czas_godzin
    except Exception as e:
        logger.warning(f"OSRM API error: {e}, falling back to Haversine")
    
    dystans = oblicz_dystans_haversine(lat1, lon1, lat2, lon2)
    return dystans, None

def oblicz_dystans(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dystans, _ = oblicz_dystans_osrm(lat1, lon1, lat2, lon2)
    return dystans

class Dostawa_MEVO:
    
    def __init__(self):
        self.adres_bazowy = "https://gbfs.urbansharing.com/rowermevo.pl"
        self.limit_czasu = 5
        self.identyfikator_klienta = "hackheroes-co2calculator"
    
    def nazwa(self) -> str:
        return "MEVO"
    
    def pobierz_pojazdy(self, szerokosc: float, dlugosc: float, promien: float) -> List[Dict]:
        try:
            cache_key = "mevo_data"
            
            if cache_key in mevo_cache:
                informacje_stacji, status_stacji = mevo_cache[cache_key]
            else:
                odpowiedz_info = requests.get(
                    f"{self.adres_bazowy}/station_information.json",
                    headers={"Client-Identifier": self.identyfikator_klienta},
                    timeout=self.limit_czasu
                )
                odpowiedz_info.raise_for_status()
                informacje_stacji = odpowiedz_info.json()
                
                odpowiedz_status = requests.get(
                    f"{self.adres_bazowy}/station_status.json",
                    headers={"Client-Identifier": self.identyfikator_klienta},
                    timeout=self.limit_czasu
                )
                odpowiedz_status.raise_for_status()
                status_stacji = odpowiedz_status.json()
                
                mevo_cache[cache_key] = (informacje_stacji, status_stacji)
            
            pojazdy = []
            
            mapa_statusu = {}
            for stacja in status_stacji['data']['stations']:
                mapa_statusu[stacja['station_id']] = {
                    'bikes': stacja['num_bikes_available'],
                    'docks': stacja['num_docks_available'],
                    'renting': stacja['is_renting'] == 1
                }
            
            for stacja in informacje_stacji['data']['stations']:
                status = mapa_statusu.get(stacja['station_id'], {})
                
                if status.get('bikes', 0) == 0:
                    continue
                
                dystans = oblicz_dystans(szerokosc, dlugosc, stacja['lat'], stacja['lon'])
                if dystans > promien:
                    continue
                
                pojazdy.append({
                    'id': stacja['station_id'],
                    'type': 'bike',
                    'provider': self.nazwa(),
                    'name': stacja['name'],
                    'location': {'latitude': stacja['lat'], 'longitude': stacja['lon']},
                    'distance_km': round(dystans, 2),
                    'bikes_available': status.get('bikes', 0),
                    'docks_available': status.get('docks', 0),
                    'is_available': True
                })
            
            pojazdy.sort(key=lambda x: x['distance_km'])
            return pojazdy
        
        except Exception as e:
            logger.error(f"Błąd MEVO: {e}")
            return []
