import math
import os
import sys
import re
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from providers import Dostawa_MEVO, oblicz_dystans
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
import supabase
from PIL import Image, ImageDraw, ImageFont
import json

load_dotenv()

ADRES_SUPABASE = os.getenv('ADRES_SUPABASE')
KLUCZ_SUPABASE = os.getenv('KLUCZ_SUPABASE')

if not ADRES_SUPABASE or not KLUCZ_SUPABASE:
    print("ERROR: ADRES_SUPABASE and KLUCZ_SUPABASE must be set in .env")
    sys.exit(1)

SUPABASE_DOSTEPNY = True
klient_supabase = supabase.create_client(ADRES_SUPABASE, KLUCZ_SUPABASE)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CO2_NA_KM_SAMOCHOD = 0.12
PREDKOSC_ROWERU_KMH = 15.0
PREDKOSC_SAMOCHODU_KMH = 40.0
DOMYSLNY_PROMIEN = 2.0
CO2_NA_DRZEWO_KG = 21  # Average lifetime CO2 absorption per tree (kg)

app = Flask(__name__)
CORS(app, resources={r"/v1/*": {"origins": ["https://hh25.morawski.my", "http://localhost:*"]}, r"/health": {"origins": "*"}})

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

dostawca = Dostawa_MEVO()


def oblicz_oszczednosci_co2(dystans_km: float) -> float:
    return dystans_km * CO2_NA_KM_SAMOCHOD


def formatuj_czas_podrozy(godziny: float) -> str:
    minuty = int(godziny * 60)
    
    if minuty < 60:
        return f"{minuty} minut"
    
    godziny_int = minuty // 60
    pozostale_minuty = minuty % 60
    
    if pozostale_minuty == 0:
        return f"{godziny_int} godzina" if godziny_int == 1 else f"{godziny_int} godzin"
    
    godzina_tekst = "1 godzina" if godziny_int == 1 else f"{godziny_int} godzin"
    return f"{godzina_tekst} {pozostale_minuty} minut"


def waliduj_wspolrzedne(lat: float, lon: float) -> tuple[bool, str]:
    if lat < -90 or lat > 90:
        return False, "Szerokość geograficzna musi być między -90 a 90"
    if lon < -180 or lon > 180:
        return False, "Długość geograficzna musi być między -180 a 180"
    return True, ""


def waliduj_uzytkownik_id(user_id: str) -> tuple[bool, str]:
    """Validates user_id format to prevent injection attacks."""
    if not user_id or len(user_id) > 255:
        return False, "Niepoprawny format identyfikatora użytkownika"
    
    # Allow UUID format or alphanumeric with common separators (-, _)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', user_id):
        return False, "Identyfikator użytkownika zawiera niedozwolone znaki"
    
    return True, ""


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'OK',
        'provider': dostawca.nazwa()
    }), 200


@app.route('/v1/search-nearest-station', methods=['GET'])
@limiter.limit("30/hour")
def szukaj_najblizszej_stacji():
    try:
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        promien = request.args.get('radius', 2.0, type=float)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Brak szerokości lub długości geograficznej'}), 400
        
        if promien < 0 or promien > 50:
            return jsonify({'error': 'Promień musi być między 0 a 50 km'}), 400
        
        jest_poprawne, komunikat_bledu = waliduj_wspolrzedne(lat, lon)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        pojazdy = dostawca.pobierz_pojazdy(lat, lon, promien)
        
        if not pojazdy:
            return jsonify({
                'success': True,
                'found': False,
                'message': 'Brak stacji w pobliżu'
            }), 200
        
        najblizszy = pojazdy[0]
        return jsonify({
            'success': True,
            'found': True,
            'station': {
                'name': najblizszy.get('name', 'Stacja MEVO'),
                'latitude': najblizszy.get('latitude'),
                'longitude': najblizszy.get('longitude'),
                'bikes_available': najblizszy.get('bikes_available'),
                'distance_km': najblizszy.get('distance_km')
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Błąd: {e}")
        return jsonify({'error': 'Błąd wewnętrzny serwera', 'details': str(e)}), 500


@app.route('/v1/calculate-co2-savings', methods=['POST'])
@limiter.limit("60/hour")
def oblicz_co2():
    try:
        dane = request.get_json()
        
        if not dane:
            return jsonify({'error': 'Brakuje danych JSON'}), 400
        
        wymagane_pola = ['latitude', 'longitude', 'destination_latitude', 'destination_longitude']
        if not all(pole in dane for pole in wymagane_pola):
            return jsonify({
                'error': 'Brakujące wymagane pola',
                'required': wymagane_pola
            }), 400
        
        lat = float(dane['latitude'])
        lon = float(dane['longitude'])
        dest_lat = float(dane['destination_latitude'])
        dest_lon = float(dane['destination_longitude'])
        promien = float(dane.get('radius', DOMYSLNY_PROMIEN))
        uzytkownik_id = dane.get('user_id')
        
        jest_poprawne, komunikat_bledu = waliduj_wspolrzedne(lat, lon)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        jest_poprawne, komunikat_bledu = waliduj_wspolrzedne(dest_lat, dest_lon)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        pojazdy = dostawca.pobierz_pojazdy(lat, lon, promien)
        
        dystans = oblicz_dystans(lat, lon, dest_lat, dest_lon)
        
        oszczednosci_co2 = oblicz_oszczednosci_co2(dystans)
        
        czas_rower = formatuj_czas_podrozy(dystans / PREDKOSC_ROWERU_KMH)
        czas_samochod = formatuj_czas_podrozy(dystans / PREDKOSC_SAMOCHODU_KMH)
        
        czas_rower_minuty = int((dystans / PREDKOSC_ROWERU_KMH) * 60)
        czas_samochod_minuty = int((dystans / PREDKOSC_SAMOCHODU_KMH) * 60)
        
        najblizszy_pojazd = pojazdy[0] if pojazdy else None
        
        id_obliczenia = None
        
        odpowiedz = {
            'success': True,
            'id': id_obliczenia,
            'distance_km': round(dystans, 2),
            'co2_savings_kg': round(oszczednosci_co2, 3),
            'travel_times': {
                'bike_minutes': czas_rower,
                'car_minutes': czas_samochod,
                'bike_minutes_raw': czas_rower_minuty,
                'car_minutes_raw': czas_samochod_minuty
            },
            'environmental_impact': {
                'co2_per_km_car_grams': 120,
                'co2_saved_grams': int(oszczednosci_co2 * 1000),
                'equivalent_trees': round(oszczednosci_co2 / CO2_NA_DRZEWO_KG, 2)
            }
        }
        
        if najblizszy_pojazd:
            odpowiedz['closest_vehicle'] = najblizszy_pojazd
            odpowiedz['message'] = f"Wybierając {najblizszy_pojazd['type']} zamiast samochodu na trasę {dystans:.2f}km oszczędzasz około {oszczednosci_co2:.2f}kg CO₂!"
        else:
            odpowiedz['message'] = f"Brak rowerów w Twojej okolicy. Na trasę {dystans:.2f}km oszczędziłbyś {oszczednosci_co2:.2f}kg CO₂ wybierając rower zamiast samochodu!"
        
        return jsonify(odpowiedz), 200
    
    except ValueError as e:
        return jsonify({'error': 'Niepoprawne dane wejściowe', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Błąd: {e}")
        return jsonify({'error': 'Błąd wewnętrzny serwera', 'details': str(e)}), 500


@app.route('/v1/nearby-stations', methods=['GET'])
@limiter.limit("30/hour")
def pobliskie_stacje():
    try:
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        promien = request.args.get('radius', 1.0, type=float)
        
        if promien < 0 or promien > 50:
            return jsonify({'error': 'Promień musi być między 0 a 50 km'}), 400
        
        if lat is None or lon is None:
            return jsonify({'error': 'Brak szerokości lub długości geograficznej'}), 400
        
        jest_poprawne, komunikat_bledu = waliduj_wspolrzedne(lat, lon)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        pojazdy = dostawca.pobierz_pojazdy(lat, lon, promien)
        
        return jsonify({
            'success': True,
            'count': len(pojazdy),
            'stations': pojazdy
        }), 200
    
    except Exception as e:
        logger.error(f"Błąd: {e}")
        return jsonify({'error': 'Błąd wewnętrzny serwera', 'details': str(e)}), 500


def weryfikuj_token_uzytkownika(auth_header: str, uzytkownik_id: str) -> tuple[bool, str]:
    if not auth_header:
        return False, "Brak nagłówka autoryzacji"
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            return False, "Niepoprawny schemat autoryzacji"
        
        if not klient_supabase:
            return False, "Weryfikacja niedostępna"
        
        user = klient_supabase.auth.get_user(token)
        if not user or not user.user:
            return False, "Niepoprawny token"
        
        if user.user.id != uzytkownik_id:
            return False, "Token nie pasuje do user_id"
        
        return True, ""
    except Exception as e:
        logger.warning(f"Błąd weryfikacji tokenu: {e}")
        return False, "Błąd weryfikacji tokenu"


@app.route('/v1/save-journey', methods=['POST'])
@limiter.limit("100/hour")
def zapisz_podroze():
    try:
        dane = request.get_json()
        
        if not dane:
            return jsonify({'error': 'Brakuje danych JSON'}), 400
        
        wymagane_pola = ['user_id', 'latitude', 'longitude', 'destination_latitude', 
                          'destination_longitude', 'chosen_transport']
        if not all(pole in dane for pole in wymagane_pola):
            return jsonify({
                'error': 'Brakujące wymagane pola',
                'required': wymagane_pola
            }), 400
        
        uzytkownik_id = dane['user_id']
        jest_poprawne, komunikat_bledu = waliduj_uzytkownik_id(uzytkownik_id)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        auth_header = request.headers.get('Authorization')
        if auth_header:
            jest_autoryzowany, komunikat_bledu_auth = weryfikuj_token_uzytkownika(auth_header, uzytkownik_id)
            if not jest_autoryzowany:
                return jsonify({'error': komunikat_bledu_auth}), 401
        lat = float(dane['latitude'])
        lon = float(dane['longitude'])
        dest_lat = float(dane['destination_latitude'])
        dest_lon = float(dane['destination_longitude'])
        wybrany_transport = dane['chosen_transport'].lower()
        
        if wybrany_transport not in ['bike', 'car']:
            return jsonify({'error': 'chosen_transport musi być "bike" lub "car"'}), 400
        
        dystans = oblicz_dystans(lat, lon, dest_lat, dest_lon)
        potencjalny_co2 = oblicz_oszczednosci_co2(dystans)
        
        if not klient_supabase:
            return jsonify({'error': 'Baza danych niedostępna'}), 503
        
        dane_podrozy = {
            'user_id': uzytkownik_id,
            'start_lat': lat,
            'start_lon': lon,
            'end_lat': dest_lat,
            'end_lon': dest_lon,
            'distance_km': round(dystans, 2),
            'chosen_transport': wybrany_transport,
            'potential_co2_savings_kg': round(potencjalny_co2, 3),
            'nearest_station_name': dane.get('nearest_station_name'),
            'nearest_station_lat': dane.get('nearest_station_lat'),
            'nearest_station_lon': dane.get('nearest_station_lon'),
            'bike_type': dane.get('bike_type')
        }
        
        wynik = klient_supabase.table('journey_tracking').insert(dane_podrozy).execute()
        
        if wybrany_transport == 'bike':
            try:
                klient_supabase.table('co2_calculations').insert({
                    'user_id': uzytkownik_id,
                    'co2_savings_kg': round(potencjalny_co2, 3),
                    'distance_km': round(dystans, 2),
                    'start_lat': lat,
                    'start_lon': lon,
                    'end_lat': dest_lat,
                    'end_lon': dest_lon,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
            except Exception as e:
                logger.warning(f"Nie udało się zapisać obliczenia: {e}")
        
        aktualizuj_statystyki_uzytkownika(uzytkownik_id, wybrany_transport, potencjalny_co2, dystans)
        
        return jsonify({
            'success': True,
            'journey_id': wynik.data[0]['id'] if wynik.data else None,
            'message': f"Podróż zapisana: {wybrany_transport.upper()} ({dystans:.2f}km)"
        }), 200
    
    except Exception as e:
        logger.error(f"Błąd: {e}")
        return jsonify({'error': 'Nie udało się zapisać podróży', 'details': str(e)}), 500


def aktualizuj_statystyki_uzytkownika(uzytkownik_id: str, transport: str, co2_oszczedzony: float, dystans: float = 0):
    try:
        if not klient_supabase:
            return
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                wynik = klient_supabase.table('user_stats').select('*').eq('user_id', uzytkownik_id).execute()
                
                if wynik.data:
                    obecny = wynik.data[0]
                    nowy_co2_oszczedzony = obecny['total_co2_saved_kg'] + (co2_oszczedzony if transport == 'bike' else 0)
                    nowy_co2_emitowany = obecny.get('total_co2_emitted_kg', 0) + (dystans * CO2_NA_KM_SAMOCHOD if transport == 'car' else 0)
                    nowa_liczba_rowerow = obecny['total_bike_journeys'] + (1 if transport == 'bike' else 0)
                    nowa_liczba_samochodow = obecny['total_car_journeys'] + (1 if transport == 'car' else 0)
                    
                    neutralny_net = (nowy_co2_oszczedzony - nowy_co2_emitowany) >= 0
                    
                    klient_supabase.table('user_stats').update({
                        'total_co2_saved_kg': round(nowy_co2_oszczedzony, 3),
                        'total_co2_emitted_kg': round(nowy_co2_emitowany, 3),
                        'total_bike_journeys': nowa_liczba_rowerow,
                        'total_car_journeys': nowa_liczba_samochodow,
                        'net_neutral': neutralny_net,
                        'last_updated': datetime.utcnow().isoformat()
                    }).eq('user_id', uzytkownik_id).execute()
                    return
                else:
                    co2_oszczedzony_init = co2_oszczedzony if transport == 'bike' else 0
                    co2_emitowany = dystans * CO2_NA_KM_SAMOCHOD if transport == 'car' else 0
                    neutralny_net = (co2_oszczedzony_init - co2_emitowany) >= 0
                    
                    klient_supabase.table('user_stats').insert({
                        'user_id': uzytkownik_id,
                        'total_co2_saved_kg': round(co2_oszczedzony_init, 3),
                        'total_co2_emitted_kg': round(co2_emitowany, 3),
                        'total_bike_journeys': 1 if transport == 'bike' else 0,
                        'total_car_journeys': 1 if transport == 'car' else 0,
                        'net_neutral': neutralny_net,
                        'last_updated': datetime.utcnow().isoformat()
                    }).execute()
                    return
            except Exception as retry_e:
                if attempt == max_retries - 1:
                    raise retry_e
                import time
                time.sleep(0.1 * (attempt + 1))
    except Exception as e:
        logger.warning(f"Nie udało się zaktualizować statystyk użytkownika: {e}")


@app.route('/v1/user-stats/<user_id>', methods=['GET'])
def pobierz_statystyki_uzytkownika(user_id):
    try:
        jest_poprawne, komunikat_bledu = waliduj_uzytkownik_id(user_id)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        if not klient_supabase:
            return jsonify({'error': 'Statystyki niedostępne'}), 503
        
        wynik_statystyk = klient_supabase.table('user_stats').select(
            '*'
        ).eq('user_id', user_id).execute()
        
        if wynik_statystyk.data:
            stat_uzytkownika = wynik_statystyk.data[0]
            laczsny_co2 = stat_uzytkownika['total_co2_saved_kg']
            co2_emitowany = stat_uzytkownika.get('total_co2_emitted_kg', 0)
            podroze_rowerem = stat_uzytkownika['total_bike_journeys']
            podroze_samochodem = stat_uzytkownika['total_car_journeys']
            neutralny_net = stat_uzytkownika['net_neutral']
        else:
            laczsny_co2 = 0
            co2_emitowany = 0
            podroze_rowerem = 0
            podroze_samochodem = 0
            neutralny_net = False
        
        wynik_obliczen = klient_supabase.table('co2_calculations').select(
            'co2_savings_kg'
        ).eq('user_id', user_id).execute()
        
        stary_co2 = sum(item['co2_savings_kg'] for item in wynik_obliczen.data) if wynik_obliczen.data else 0
        liczba_starych = len(wynik_obliczen.data) if wynik_obliczen.data else 0
        
        total_co2 = laczsny_co2 + stary_co2
        total_emitted = co2_emitowany
        saldo_netto = total_co2 - total_emitted
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_co2_saved_kg': round(total_co2, 2),
            'total_co2_emitted_kg': round(total_emitted, 2),
            'total_co2_grams': int(total_co2 * 1000),
            'bike_journeys': podroze_rowerem,
            'car_journeys': podroze_samochodem,
            'net_balance_kg': round(saldo_netto, 2),
            'net_neutral': neutralny_net,
            'is_negative': saldo_netto < 0,
            'trips_count': liczba_starych + podroze_rowerem + podroze_samochodem,
            'equivalent_trees': round(total_co2 / CO2_NA_DRZEWO_KG, 2)
        }), 200
    
    except Exception as e:
        logger.error(f"Błąd przy pobieraniu statystyk: {e}")
        return jsonify({'error': 'Nie udało się pobrać statystyk', 'details': str(e)}), 500


@app.route('/v1/share-graphic/<user_id>', methods=['GET'])
def wygeneruj_grafike_dzielenia(user_id):
    try:
        jest_poprawne, komunikat_bledu = waliduj_uzytkownik_id(user_id)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        if not klient_supabase:
            return jsonify({'error': 'Statystyki niedostępne'}), 503
        
        wynik_statystyk = klient_supabase.table('user_stats').select('*').eq('user_id', user_id).execute()
        wynik_obliczen = klient_supabase.table('co2_calculations').select('co2_savings_kg').eq('user_id', user_id).execute()
        wynik_podrozy = klient_supabase.table('journey_tracking').select('id').eq('user_id', user_id).execute()
        
        laczsny_co2_saved = 0
        laczsny_co2_emitted = 0
        liczba = 0
        
        if wynik_statystyk.data:
            stat = wynik_statystyk.data[0]
            laczsny_co2_saved = stat.get('total_co2_saved_kg', 0)
            laczsny_co2_emitted = stat.get('total_co2_emitted_kg', 0)
        
        stary_co2 = sum(item['co2_savings_kg'] for item in wynik_obliczen.data) if wynik_obliczen.data else 0
        laczsny_co2_saved += stary_co2
        liczba_starych = len(wynik_obliczen.data) if wynik_obliczen.data else 0
        liczba_wszystkich_podrozy = len(wynik_podrozy.data) if wynik_podrozy.data else 0
        liczba = liczba_wszystkich_podrozy
        
        netto = laczsny_co2_saved - laczsny_co2_emitted
        jest_negatywny = netto < 0
        
        szerokosc, wysokosc = 1200, 630
        obraz = Image.new('RGB', (szerokosc, wysokosc), color='#000000')
        rysowanie = ImageDraw.Draw(obraz)
        
        try:
            czcionka_tytul = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            czcionka_wartosc = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            czcionka_etykieta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except Exception:
            czcionka_tytul = ImageFont.load_default()
            czcionka_wartosc = ImageFont.load_default()
            czcionka_etykieta = ImageFont.load_default()
        
        if jest_negatywny:
            for y in range(wysokosc):
                odcien = int(30 * (y / wysokosc))
                kolor = (odcien, 0, 0)
                rysowanie.rectangle([(0, y), (szerokosc, y+1)], fill=kolor)
            
            rysowanie.rectangle([(0, 0), (szerokosc, 8)], fill='#ff4444')
            kolor_tekstu = '#ff4444'
            wartosc_do_wyswietlenia = abs(netto)
            etykieta = "KG CO₂ EMISJI"
        else:
            for y in range(wysokosc):
                odcien = int(20 * (y / wysokosc))
                kolor = (odcien, odcien, odcien)
                rysowanie.rectangle([(0, y), (szerokosc, y+1)], fill=kolor)
            
            rysowanie.rectangle([(0, 0), (szerokosc, 8)], fill='#00ff00')
            kolor_tekstu = '#00ff00'
            wartosc_do_wyswietlenia = netto
            etykieta = "KG CO₂ OSZCZĘDZONO"
        
        tekst_co2 = f"{wartosc_do_wyswietlenia:.2f}"
        rysowanie.text((szerokosc//2, 200), tekst_co2, fill=kolor_tekstu, font=czcionka_wartosc, anchor="mm")
        
        rysowanie.text((szerokosc//2, 380), etykieta, fill='#ffffff', font=czcionka_etykieta, anchor="mm")
        
        tekst_podrozy = f"{liczba} podróży"
        rysowanie.text((szerokosc//2, 480), tekst_podrozy, fill='#888888', font=czcionka_etykieta, anchor="mm")
        
        rysowanie.text((szerokosc//2, wysokosc-50), "hh25.morawski.my", fill='#666666', font=czcionka_etykieta, anchor="mm")
        
        img_io = BytesIO()
        obraz.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
    
    except Exception as e:
        logger.error(f"Błąd przy generowaniu grafiki: {e}")
        return jsonify({'error': 'Nie udało się wygenerować grafiki', 'details': str(e)}), 500


@app.route('/v1/share-graphic-stats/<user_id>', methods=['GET'])
def wygeneruj_grafike_statystyk(user_id):
    try:
        jest_poprawne, komunikat_bledu = waliduj_uzytkownik_id(user_id)
        if not jest_poprawne:
            return jsonify({'error': komunikat_bledu}), 400
        
        if not klient_supabase:
            return jsonify({'error': 'Statystyki niedostępne'}), 503
        
        wynik_statystyk = klient_supabase.table('user_stats').select('*').eq('user_id', user_id).execute()
        
        podroze_rowerem = 0
        podroze_samochodem = 0
        laczsny_co2_oszczedzony = 0
        laczsny_co2_emitowany = 0
        
        if wynik_statystyk.data:
            stat_uzytkownika = wynik_statystyk.data[0]
            laczsny_co2_oszczedzony = stat_uzytkownika['total_co2_saved_kg']
            laczsny_co2_emitowany = stat_uzytkownika.get('total_co2_emitted_kg', 0)
            podroze_rowerem = stat_uzytkownika['total_bike_journeys']
            podroze_samochodem = stat_uzytkownika['total_car_journeys']
        
        wynik_obliczen = klient_supabase.table('co2_calculations').select('distance_km,co2_savings_kg').eq('user_id', user_id).execute()
        laczsny_dystans = sum(item['distance_km'] for item in wynik_obliczen.data) if wynik_obliczen.data else 0
        stary_co2 = sum(item['co2_savings_kg'] for item in wynik_obliczen.data) if wynik_obliczen.data else 0
        
        laczsny_co2_oszczedzony += stary_co2
        netto = laczsny_co2_oszczedzony - laczsny_co2_emitowany
        jest_negatywny = netto < 0
        
        szerokosc, wysokosc = 1200, 630
        obraz = Image.new('RGB', (szerokosc, wysokosc), color='#000000')
        rysowanie = ImageDraw.Draw(obraz)
        
        try:
            czcionka_tytul = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
            czcionka_wartosc = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
            czcionka_etykieta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            czcionka_mala = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except Exception:
            czcionka_tytul = ImageFont.load_default()
            czcionka_wartosc = ImageFont.load_default()
            czcionka_etykieta = ImageFont.load_default()
            czcionka_mala = ImageFont.load_default()
        
        if jest_negatywny:
            for y in range(wysokosc):
                odcien = int(30 * (y / wysokosc))
                kolor = (odcien, 0, 0)
                rysowanie.rectangle([(0, y), (szerokosc, y+1)], fill=kolor)
            
            rysowanie.rectangle([(0, 0), (szerokosc, 10)], fill='#ff4444')
            kolor_tytul = '#ff4444'
            kolor_wartosc = '#ff4444'
            wartosc_do_wyswietlenia = abs(netto)
            etykieta_co2 = "kg CO₂ EMISJI"
            tytul = "Twoja emisja netto"
        else:
            for y in range(wysokosc):
                odcien = int(30 * (y / wysokosc))
                kolor = (odcien, odcien, odcien)
                rysowanie.rectangle([(0, y), (szerokosc, y+1)], fill=kolor)
            
            rysowanie.rectangle([(0, 0), (szerokosc, 10)], fill='#00ff00')
            kolor_tytul = '#00ff00'
            kolor_wartosc = '#00ff00'
            wartosc_do_wyswietlenia = netto
            etykieta_co2 = "kg CO₂ OSZCZĘDZONO"
            tytul = "Mój wpływ na klimat"
        
        rysowanie.text((szerokosc//2, 80), tytul, fill=kolor_tytul, font=czcionka_tytul, anchor="mm")
        
        tekst_co2 = f"{wartosc_do_wyswietlenia:.1f}"
        rysowanie.text((szerokosc//2, 250), tekst_co2, fill=kolor_wartosc, font=czcionka_wartosc, anchor="mm")
        
        rysowanie.text((szerokosc//2, 360), etykieta_co2, fill='#ffffff', font=czcionka_etykieta, anchor="mm")
        
        y_statystyk = 450
        tekst_statystyk = f"Rower: {podroze_rowerem} | Auto: {podroze_samochodem} | {laczsny_dystans:.1f} km"
        rysowanie.text((szerokosc//2, y_statystyk), tekst_statystyk, fill='#888888', font=czcionka_mala, anchor="mm")
        
        rysowanie.text((szerokosc//2, wysokosc-60), "hh25.morawski.my", fill='#666666', font=czcionka_etykieta, anchor="mm")
        
        img_io = BytesIO()
        obraz.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
    
    except Exception as e:
        logger.error(f"Błąd przy generowaniu grafiki statystyk: {e}")
        return jsonify({'error': 'Nie udało się wygenerować grafiki', 'details': str(e)}), 500


@app.route('/v1/global-stats', methods=['GET'])
def pobierz_globalne_statystyki():
    try:
        if not klient_supabase:
            return jsonify({'error': 'Statystyki niedostępne'}), 503
        
        wynik_uzytkownikow = klient_supabase.table('user_stats').select('total_co2_saved_kg,total_co2_emitted_kg,total_bike_journeys,total_car_journeys').execute()
        
        suma_co2_oszczedzono = 0
        suma_co2_emitowano = 0
        suma_podrozy_rowerem = 0
        suma_podrozy_samochodem = 0
        
        for user in wynik_uzytkownikow.data:
            suma_co2_oszczedzono += user.get('total_co2_saved_kg', 0)
            suma_co2_emitowano += user.get('total_co2_emitted_kg', 0)
            suma_podrozy_rowerem += user.get('total_bike_journeys', 0)
            suma_podrozy_samochodem += user.get('total_car_journeys', 0)
        
        return jsonify({
            'success': True,
            'global_co2_saved_kg': round(suma_co2_oszczedzono, 2),
            'global_co2_emitted_kg': round(suma_co2_emitowano, 2),
            'global_bike_journeys': suma_podrozy_rowerem,
            'global_car_journeys': suma_podrozy_samochodem,
            'total_users': len(wynik_uzytkownikow.data) if wynik_uzytkownikow.data else 0,
            'equivalent_trees': round(suma_co2_oszczedzono / 0.021, 2)
        }), 200
    
    except Exception as e:
        logger.error(f"Błąd przy pobieraniu globalnych statystyk: {e}")
        return jsonify({'error': 'Nie udało się pobrać statystyk', 'details': str(e)}), 500


@app.route('/favicon/<path:filename>')
def serve_favicon(filename):
    return send_file(f'favicon/{filename}', mimetype='image/x-icon' if filename.endswith('.ico') else 'image/png')


@app.route('/favicon/site.webmanifest')
def serve_manifest():
    try:
        with open('favicon/site.webmanifest', 'r') as f:
            return f.read(), 200, {'Content-Type': 'application/manifest+json'}
    except FileNotFoundError:
        return jsonify({'error': 'Manifest not found'}), 404


@app.route('/config', methods=['GET'])
def pobierz_config():
    return jsonify({
        'adres_supabase': os.getenv('ADRES_SUPABASE'),
        'klucz_supabase': os.getenv('KLUCZ_SUPABASE')
    }), 200


@app.route('/', methods=['GET'])
def index():
    try:
        with open('index.html', 'r') as f:
            zawartosc = f.read()
        
        return zawartosc, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'Plik nie znaleziony'}), 404


@app.route('/share', methods=['GET'])
def share():
    try:
        with open('share.html', 'r') as f:
            zawartosc = f.read()
        
        return zawartosc, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'Plik nie znaleziony'}), 404


@app.route('/history', methods=['GET'])
def history():
    try:
        with open('history.html', 'r') as f:
            zawartosc = f.read()
        
        return zawartosc, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return jsonify({'error': 'Plik nie znaleziony'}), 404


@app.errorhandler(404)
def nie_znaleziono(e):
    return jsonify({'error': 'Endpoint nie znaleziony'}), 404


@app.errorhandler(500)
def blad_wewnętrzny(e):
    return jsonify({'error': 'Błąd wewnętrzny serwera'}), 500


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 8080))
    debugowanie = os.getenv('DEBUGOWANIE', 'False') == 'True'
    
    logger.info(f"Uruchamianie Zielonego Pedału na porcie {port}")
    logger.info(f"Dostawca: {dostawca.nazwa()}")
    logger.info(f"Interfejs: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debugowanie)
