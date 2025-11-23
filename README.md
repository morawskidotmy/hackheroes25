# sqrt(CO)

<div align="center">
  <img src="./favicon/apple-touch-icon.png" alt="sqrt(CO) logo" width="120" height="120">
</div>

Aplikacja do śledzenia wpływu Twoich podróży na klimat poprzez wybór roweru zamiast samochodu.

**🌍 Dostępna na: [hh25.morawski.my](https://hh25.morawski.my)**

---

## O aplikacji

sqrt(CO) to nowoczesna aplikacja, która umożliwia monitorowanie wpływu Twoich wyborów transportowych na klimat. Śledzenie oszczędności CO₂ oraz dzielenie się wynikami w mediach społecznościowych to kluczowe funkcje, które wspierają użytkowników w budowaniu świadomości ekologicznej.

### Możliwości aplikacji:

- 📊 **Obliczaj oszczędności CO₂** dla każdej trasy
- 🚴 **Śledź wybory transportowe** (rower vs samochód)
- 🔍 **Wyszukuj stacje rowerowe MEVO** w pobliżu
- 📈 **Monitoruj wpływ netto** na klimat
- 🌍 **Przeglądaj globalne wyniki społeczności**
- 🌳 **Zobacz równoważnik w uratowanych drzewach**
- 🎨 **Generuj grafiki** do mediów społecznościowych
- 👥 **Loguj się** przez Discord lub email
- 💾 **Zapisuj podróże** z metadanymi
- 📍 **Automatyczne dane lokalizacyjne**
- 🔄 **Synchronizacja danych** z chmurą Supabase

---

## Cechy

- **Statystyki społeczności**: liczba podróży i oszczędności CO₂
- **Inteligentne wyszukiwanie stacji**: sortowanie i dostępność rowerów
- **Szczegółowe raporty**: dokładne czasy przyjazdu
- **Identyfikacja roweru**: własny lub bike-sharing MEVO
- **Nowoczesny interfejs**: minimalistyczny z trybem ciemnym
- **Animacje**: płynne przejścia dla lepszego UX
- **Dostępność**: ARIA labels, responsywne fonty

---

## Technologia

### Frontend
- **HTML5**, **CSS3**, **Vanilla JavaScript**
- Responsywny design z CSS Grid i Flexbox

### Backend
- **Flask** (Python)
- **PIL/Pillow** do generowania grafik

### Baza danych
- **Supabase** (PostgreSQL)
- **Autoryzacja**: e-mail, Google, Discord

### Zewnętrzne API
- **MEVO API** - stacje rowerowe
- **Haversine formula** do obliczania odległości

---

## Funkcjonalności

### 1. Obliczanie oszczędności CO₂
Wprowadź punkty startu i końca, a aplikacja obliczy:
- Odległość w kilometrach
- Oszczędności CO₂
- Czas podróży (rower vs samochód)
- Ilość uratowanych drzew

### 2. Śledzenie transportu
Dokumentuj podróże, wybierając:
- 🚴 Rower (oszczędza CO₂)
- 🚗 Samochód (generuje CO₂)

### 3. Bilans netto
Aplikacja oblicza Twój wpływ netto:
- **Zielony**: oszczędności CO₂
- **Czerwony**: wyższe emisje

### 4. Statystyki społeczności
Widok zagregowanych danych:
- Całkowita oszczędność CO₂
- Liczba podróży

### 5. Grafiki do mediów społecznościowych
Generuj grafiki PNG (1200x630 px) z bilansem CO₂.

---

## API

### Publiczne
- `GET /health`
- `GET /v1/nearby-stations`
- `POST /v1/calculate-co2-savings`
- `GET /v1/global-stats`

### Z autoryzacją
- `POST /v1/save-journey`
- `GET /v1/user-stats/{user_id}`

---

## Instalacja

### Lokalna instalacja
```bash
pip install -r requirements.txt
export ADRES_SUPABASE="https://your-project.supabase.co"
export KLUCZ_SUPABASE="your_anon_key"
python app.py
