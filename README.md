# sqrtco

Aplikacja do śledzenia wpływu na klimat poprzez wybór roweru zamiast samochodu.

**🌍 Dostępna na: [hh25.morawski.my](https://hh25.morawski.my)**

---

## O aplikacji

Zielony Pedał pokazuje realny wpływ Twoich wyborów transportu na środowisko. Każda podróż rowerem generuje konkretne oszczędności CO₂, które możesz śledzić i udostępniać na mediach społecznych.

### Co możesz robić:

- 📊 **Obliczać oszczędności CO₂** dla każdej podróży
- 🚴 **Śledzić wybory transportu** (rower vs samochód)
- 🔍 **Wyszukiwać stacje rowerów MEVO** w okolicy
- 📈 **Monitorować wpływ netto** - czy jesteś net-pozytywny dla klimatu
- 🌍 **Generować grafiki** do udostępniania na Instagramie, Twitterze, TikToku
- 👥 **Logować się** przez Email lub Discord
- 📱 **Otrzymywać motywację** do dalszych ekologicznych wyborów

---

## Technologia

### Frontend
- **HTML5**, **CSS3**, **Vanilla JavaScript**
- Nowoczesny, responsywny design
- Działa na mobilnych i desktopowych urządzeniach

### Backend
- **Flask** (Python)
- **PIL/Pillow** - generowanie grafik PNG
- **CORS** - integracja z frontendem

### Baza danych
- **Supabase** (PostgreSQL)
- **Autentykacja**: Email/Hasło, Discord OAuth
- **RLS** - Row-Level Security dla bezpieczeństwa

### Zewnętrzne API
- **MEVO API** - dane o stacjach rowerów
- **Haversine formula** - dokładne obliczanie odległości

### Narzędzia
- **Python 3.9+**
- **Docker** - containerization
- **Git** - version control

---

## Funkcjonalność

### 1. Obliczanie oszczędności CO₂
Wpisz punkt startu i koniec - aplikacja obliczy:
- Odległość (km)
- Oszczędzę CO₂ (kg)
- Czas podróży (rower vs samochód)
- Równoważną ilość uratowanych drzew

**Wzór**: 0.12 kg CO₂ na km (emisje samochodu)

### 2. Śledzenie transportu
Po zalogowaniu możesz zapisać każdą podróż i wybrać:
- 🚴 Rower (oszczędza CO₂)
- 🚗 Samochód (produkuje CO₂)

### 3. Net Balance
Aplikacja oblicza Twój wpływ netto:
- **Zielony**: Oszczędzasz więcej CO₂, niż produkujesz ✓
- **Czerwony**: Większe emisje z samochodów ⚠️

### 4. Grafiki do mediów społecznych
Generuj piękne grafiki PNG (1200x630px):
- Pokazują Twój net CO₂ balance
- Dynamiczne kolory (zielony/czerwony)
- Statystyki podróży
- Gotowe do udostępniania na Instagramie, Twitterze, TikToku

---

## Cechy

✅ **Całkowicie po polsku** - UI, dokumentacja, komunikaty  
✅ **Bezpłatne** - bez ukrytych opłat  
✅ **Bezpieczne** - Twoje dane chronione przez RLS  
✅ **Responsywne** - działa na wszystkich urządzeniach  
✅ **Szybkie** - optymalizowana wydajność  
✅ **Motywujące** - gamification poprzez net-balance  
✅ **Shareable** - udostępnianie na mediach społecznych  

---

## Punkty końcowe API

### Publiczne
- `GET /health` - Status aplikacji
- `GET /v1/nearby-stations` - Stacje rowerów w pobliżu
- `GET /v1/search-nearest-station` - Wyszukaj najbliższą stację
- `POST /v1/calculate-co2-savings` - Oblicz oszczędności CO₂

### Z autentykacją
- `POST /v1/save-journey` - Zapisz podróż
- `GET /v1/user-stats/{user_id}` - Twoje statystyki
- `GET /v1/share-graphic/{user_id}` - Grafika oszczędności
- `GET /v1/share-graphic-stats/{user_id}` - Grafika net balance

---

## Baza danych

### Tabele
- **journey_tracking** - Historia podróży (rower/samochód)
- **user_stats** - Statystyki użytkownika (net neutrality)
- **co2_calculations** - Historyczne obliczenia

### Bezpieczeństwo
Wszystkie dane są:
- Scoped do użytkownika (RLS policies)
- Szyfrowane w przesyłaniu (HTTPS)
- Zabezpieczone w bazie danych

---

## Obliczenia

### CO₂ Zaoszczędzony
```
CO₂ = odległość (km) × 0.12 kg/km
```

### Net Balance
```
Net = Całkowity CO₂ Zaoszczędzony - (Podróże samochodem × 10km × 0.12 kg/km)

Jeśli Net ≥ 0: Net Pozytywny ✓ (zielony)
Jeśli Net < 0: Net Negatywny ⚠️ (czerwony)
```

### Równoważność
```
1 drzewo neutralizuje: 0.021 kg CO₂ rocznie
Drzewa = Całkowity CO₂ / 0.021
```

---

## Licencja

GNU General Public License v3.0 - patrz [LICENSE](LICENSE)

---

## Kontakt & Linki

- **Demo**: https://hh25.morawski.my
- **GitHub**: https://github.com/morawskidotmy/hackheroes25
- **Issues**: GitHub Issues

---

## Dzięki

Hack Heroes 2025 - Projekt edukacyjny

---

**Każda podróż rowerem ratuje planetę. 🌍🚴💚**
