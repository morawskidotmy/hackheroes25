import math
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from providers import Dostawa_MEVO
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
import supabase
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

ADRES_SUPABASE = os.getenv('ADRES_SUPABASE')
KLUCZ_SUPABASE = os.getenv('KLUCZ_SUPABASE')
SUPABASE_DOSTEPNY = ADRES_SUPABASE and KLUCZ_SUPABASE

if SUPABASE_DOSTEPNY:
    klient_supabase = supabase.create_client(ADRES_SUPABASE, KLUCZ_SUPABASE)
else:
    klient_supabase = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CO2_NA_KM_SAMOCHOD = 0.12
PREDKOSC_ROWERU_KMH = 15.0
PREDKOSC_SAMOCHODU_KMH = 40.0
DOMYSLNY_PROMIEN = 2.0

app = Flask(__name__)
CORS(app)

dostawca = Dostawa_MEVO()



def oblicz_dystans(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


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


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'OK',
        'provider': dostawca.nazwa()
    }), 200


@app.route('/v1/search-nearest-station', methods=['GET'])
def szukaj_najblizszej_stacji():
    try:
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        promien = request.args.get('radius', 2.0, type=float)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Brak szerokości lub długości geograficznej'}), 400
        
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
def oblicz_co2():
    try:
        dane = request.get_json()
        
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
        
        teraz = datetime.now()
        przyjazd_rowerem = (teraz + timedelta(minutes=czas_rower_minuty)).strftime("%H:%M")
        przyjazd_samochodem = (teraz + timedelta(minutes=czas_samochod_minuty)).strftime("%H:%M")
        
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
                'bike_arrival': przyjazd_rowerem,
                'car_arrival': przyjazd_samochodem
            },
            'environmental_impact': {
                'co2_per_km_car_grams': 120,
                'co2_saved_grams': int(oszczednosci_co2 * 1000),
                'equivalent_trees': round(oszczednosci_co2 / 0.021, 2)
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
def pobliskie_stacje():
    try:
        lat = request.args.get('latitude', type=float)
        lon = request.args.get('longitude', type=float)
        promien = request.args.get('radius', 1.0, type=float)
        
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


@app.route('/v1/save-journey', methods=['POST'])
def zapisz_podroze():
    try:
        dane = request.get_json()
        
        wymagane_pola = ['user_id', 'latitude', 'longitude', 'destination_latitude', 
                          'destination_longitude', 'chosen_transport']
        if not all(pole in dane for pole in wymagane_pola):
            return jsonify({
                'error': 'Brakujące wymagane pola',
                'required': wymagane_pola
            }), 400
        
        uzytkownik_id = dane['user_id']
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
        
        wynik = klient_supabase.table('user_stats').select('*').eq('user_id', uzytkownik_id).execute()
        
        if wynik.data:
            obecny = wynik.data[0]
            nowy_co2_oszczedzony = obecny['total_co2_saved_kg'] + (co2_oszczedzony if transport == 'bike' else 0)
            nowy_co2_emitowany = obecny.get('total_co2_emitted_kg', 0) + (dystans * CO2_NA_KM_SAMOCHOD if transport == 'car' else 0)
            nowa_liczba_rowerow = obecny['total_bike_journeys'] + (1 if transport == 'bike' else 0)
            nowa_liczba_samochodow = obecny['total_car_journeys'] + (1 if transport == 'car' else 0)
            
            saldo_netto = nowy_co2_oszczedzony - nowy_co2_emitowany
            neutralny_net = saldo_netto >= 0
            
            klient_supabase.table('user_stats').update({
                'total_co2_saved_kg': round(nowy_co2_oszczedzony, 3),
                'total_co2_emitted_kg': round(nowy_co2_emitowany, 3),
                'total_bike_journeys': nowa_liczba_rowerow,
                'total_car_journeys': nowa_liczba_samochodow,
                'net_neutral': neutralny_net,
                'last_updated': datetime.utcnow().isoformat()
            }).eq('user_id', uzytkownik_id).execute()
        else:
            neutralny_net = transport == 'bike'
            co2_emitowany = dystans * CO2_NA_KM_SAMOCHOD if transport == 'car' else 0
            klient_supabase.table('user_stats').insert({
                'user_id': uzytkownik_id,
                'total_co2_saved_kg': round(co2_oszczedzony if transport == 'bike' else 0, 3),
                'total_co2_emitted_kg': round(co2_emitowany, 3),
                'total_bike_journeys': 1 if transport == 'bike' else 0,
                'total_car_journeys': 1 if transport == 'car' else 0,
                'net_neutral': neutralny_net,
                'last_updated': datetime.utcnow().isoformat()
            }).execute()
    except Exception as e:
        logger.warning(f"Nie udało się zaktualizować statystyk użytkownika: {e}")


@app.route('/v1/user-stats/<user_id>', methods=['GET'])
def pobierz_statystyki_uzytkownika(user_id):
    try:
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
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_co2_kg': round(laczsny_co2 + stary_co2, 2),
            'total_co2_grams': int((laczsny_co2 + stary_co2) * 1000),
            'bike_journeys': podroze_rowerem,
            'car_journeys': podroze_samochodem,
            'net_neutral': neutralny_net,
            'trips_count': liczba_starych + podroze_rowerem + podroze_samochodem,
            'equivalent_trees': round((laczsny_co2 + stary_co2) / 0.021, 2)
        }), 200
    
    except Exception as e:
        logger.error(f"Błąd przy pobieraniu statystyk: {e}")
        return jsonify({'error': 'Nie udało się pobrać statystyk', 'details': str(e)}), 500


@app.route('/v1/share-graphic/<user_id>', methods=['GET'])
def wygeneruj_grafike_dzielenia(user_id):
    try:
        if not klient_supabase:
            return jsonify({'error': 'Statystyki niedostępne'}), 503
        
        wynik = klient_supabase.table('co2_calculations').select(
            'co2_savings_kg'
        ).eq('user_id', user_id).execute()
        
        laczsny_co2 = sum(item['co2_savings_kg'] for item in wynik.data) if wynik.data else 0
        liczba = len(wynik.data) if wynik.data else 0
        
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
        
        for y in range(wysokosc):
            odcien = int(20 * (y / wysokosc))
            kolor = (odcien, odcien, odcien)
            rysowanie.rectangle([(0, y), (szerokosc, y+1)], fill=kolor)
        
        rysowanie.rectangle([(0, 0), (szerokosc, 8)], fill='#00ff00')
        
        tekst_co2 = f"{laczsny_co2:.2f}"
        rysowanie.text((szerokosc//2, 200), tekst_co2, fill='#00ff00', font=czcionka_wartosc, anchor="mm")
        
        rysowanie.text((szerokosc//2, 380), "KG CO₂ OSZCZĘDZONO", fill='#ffffff', font=czcionka_etykieta, anchor="mm")
        
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
        if not klient_supabase:
            return jsonify({'error': 'Statystyki niedostępne'}), 503
        
        wynik_statystyk = klient_supabase.table('user_stats').select('*').eq('user_id', user_id).execute()
        
        laczsny_co2_oszczedzony = 0
        laczsny_co2_emitowany = 0
        podroze_rowerem = 0
        podroze_samochodem = 0
        
        if wynik_statystyk.data:
            stat_uzytkownika = wynik_statystyk.data[0]
            laczsny_co2_oszczedzony = stat_uzytkownika['total_co2_saved_kg']
            laczsny_co2_emitowany = stat_uzytkownika.get('total_co2_emitted_kg', 0)
            podroze_rowerem = stat_uzytkownika['total_bike_journeys']
            podroze_samochodem = stat_uzytkownika['total_car_journeys']
        
        wynik_obliczen = klient_supabase.table('co2_calculations').select('co2_savings_kg').eq('user_id', user_id).execute()
        stary_co2 = sum(item['co2_savings_kg'] for item in wynik_obliczen.data) if wynik_obliczen.data else 0
        
        laczsny_co2_oszczedzony += stary_co2
        
        saldo_netto = laczsny_co2_oszczedzony - laczsny_co2_emitowany
        jest_pozytywne = saldo_netto >= 0
        
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
        
        for y in range(wysokosc):
            odcien = int(30 * (y / wysokosc))
            kolor = (odcien, odcien, odcien)
            rysowanie.rectangle([(0, y), (szerokosc, y+1)], fill=kolor)
        
        kolor_akcentu = '#00ff00' if jest_pozytywne else '#ff6b6b'
        rysowanie.rectangle([(0, 0), (szerokosc, 10)], fill=kolor_akcentu)
        
        tytul = "Mój wpływ na klimat"
        rysowanie.text((szerokosc//2, 80), tytul, fill=kolor_akcentu, font=czcionka_tytul, anchor="mm")
        
        tekst_netto = f"{abs(saldo_netto):.1f}"
        rysowanie.text((szerokosc//2, 250), tekst_netto, fill=kolor_akcentu, font=czcionka_wartosc, anchor="mm")
        
        tekst_jednostka = "kg CO₂ ZAOSZCZĘDZONO" if jest_pozytywne else "kg CO₂ EMISJI"
        rysowanie.text((szerokosc//2, 360), tekst_jednostka, fill='#ffffff', font=czcionka_etykieta, anchor="mm")
        
        y_statystyk = 450
        tekst_statystyk = f"🚴 {podroze_rowerem} podróży | 🚗 {podroze_samochodem} podróży | 📊 Oszczędzono: {laczsny_co2_oszczedzony:.1f} kg"
        rysowanie.text((szerokosc//2, y_statystyk), tekst_statystyk, fill='#888888', font=czcionka_mala, anchor="mm")
        
        if jest_pozytywne:
            tekst_statusu = "✓ NET POZYTYWNIE"
            kolor_statusu = '#00ff00'
        else:
            tekst_statusu = "⚠ NET NEGATYWNIE"
            kolor_statusu = '#ff6b6b'
        
        rysowanie.text((szerokosc//2, wysokosc-60), tekst_statusu, fill=kolor_statusu, font=czcionka_etykieta, anchor="mm")
        
        img_io = BytesIO()
        obraz.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=False)
    
    except Exception as e:
        logger.error(f"Błąd przy generowaniu grafiki statystyk: {e}")
        return jsonify({'error': 'Nie udało się wygenerować grafiki', 'details': str(e)}), 500


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
