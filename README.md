# sqrtco

Aplikacja do śledzenia wpływu na klimat poprzez wybór roweru zamiast samochodu.

**🌍 Dostępna na: [hh25.morawski.my](https://hh25.morawski.my)**

---

## O aplikacji

sqrtco to innowacyjna aplikacja, która pozwala na śledzenie wpływu Twoich decyzji transportowych na klimat. Każda podróż rowerem przyczynia się do realnych oszczędności CO₂, które możesz monitorować i dzielić się nimi w mediach społecznościowych.

### Co możesz robić:

- 📊 **Obliczać oszczędności CO₂** dla każdej trasy
- 🚴 **Śledzić wybory transportowe** (rower vs samochód)
- 🔍 **Wyszukiwać stacje rowerowe MEVO** w okolicy
- 📈 **Monitorować wpływ netto** na klimat
- 🌍 **Generować grafiki** do udostępniania w serwisach społecznościowych
- 👥 **Logować się** przez e-mail lub Discord
- 📱 **Otrzymywać motywacyjne powiadomienia** o ekologicznych wyborach

---

## Technologia

### Frontend
- **HTML5**, **CSS3**, **Vanilla JavaScript**
- Nowoczesny, responsywny design
- Dostępność na urządzeniach mobilnych i desktopowych

### Backend
- **Flask** (Python)
- **PIL/Pillow** do generowania grafik PNG
- **CORS** dla płynnej integracji z frontendem

### Baza danych
- **Supabase** (PostgreSQL)
- **Autoryzacja**: E-mail, hasło oraz Discord OAuth
- **RLS** (Row-Level Security) dla zwiększenia bezpieczeństwa

### Zewnętrzne API
- **MEVO API** - sugestie lokalnych stacji rowerowych
- **Haversine formula** dla precyzyjnego obliczania odległości

### Narzędzia
- **Python 3.9+**
- **Git** - kontrola wersji

---

## Funkcjonalność

### 1. Obliczanie oszczędności CO₂
Wprowadź punkty startu i końca, a aplikacja obliczy:
- Odległość w kilometrach
- Oszczędności CO₂ w kilogramach
- Czas podróży (rower vs samochód)
- Ilość uratowanych drzew

**Wzór**: 0.12 kg CO₂ na kilometr (średnia emisja dla samochodu)

### 2. Śledzenie transportu
Po zalogowaniu możesz dokumentować każdą podróż, wybierając:
- 🚴 Rower (oszczędza CO₂)
- 🚗 Samochód (generuje CO₂)

### 3. Bilans netto
Aplikacja oblicza Twój wpływ netto:
- **Zielony**: Oszczędzasz więcej CO₂, niż produkujesz ✓
- **Czerwony**: Wyższe emisje z samochodów ⚠️

### 4. Grafiki do mediów społecznych
Generuj efektowne grafiki PNG (1200x630 px):
- Pokazujące Twój bilans CO₂
- Dynamiczne kolory (zielony/czerwony)
- Statystyki podróży
- Gotowe do dzielenia się na Instagramie, Twitterze, TikToku

---

## Cechy

✅ **Bezpiecznie** - Twoje dane chronione przez RLS  
✅ **Responsywne** - dostosowane do różnych urządzeń  
✅ **Szybkie** - zoptymalizowana wydajność  
✅ **Motywujące** - mechaniki gamifikacji w bilansie netto  
✅ **Łatwe udostępnianie** w mediach społecznościowych  

---

## Punkty końcowe API

### Publiczne
- `GET /health` - status aplikacji
- `GET /v1/nearby-stations` - stacje rowerowe w pobliżu
- `GET /v1/search-nearest-station` - szukaj najbliższej stacji
- `POST /v1/calculate-co2-savings` - oblicz oszczędności CO₂

### Z autoryzacją
- `POST /v1/save-journey` - zapisz podróż
- `GET /v1/user-stats/{user_id}` - Twoje statystyki
