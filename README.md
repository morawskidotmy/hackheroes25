# sqrt(CO)

Aplikacja do śledzenia wpływu na klimat poprzez wybór roweru zamiast samochodu.

**🌍 Dostępna na: [hh25.morawski.my](https://hh25.morawski.my)**

---

## O aplikacji

sqrt(CO) to innowacyjna aplikacja, która pozwala na śledzenie wpływu Twoich decyzji transportowych na klimat. Każda podróż rowerem przyczynia się do realnych oszczędności CO₂, które możesz monitorować i dzielić się nimi w mediach społecznych. Aplikacja wspiera polskich użytkowników w zmianie nawyków transportowych i budowaniu świadomości ekologicznej.

### Co możesz robić:

- 📊 **Obliczać oszczędności CO₂** dla każdej trasy z precyzyjnym wyliczeniem
- 🚴 **Śledzić wybory transportowe** (rower vs samochód) z historią podróży
- 🔍 **Wyszukiwać stacje rowerowe MEVO** w okolicy w czasie rzeczywistym
- 📈 **Monitorować wpływ netto** na klimat (oszczędzony vs emisji)
- 🌍 **Przeglądać globalne wyniki społeczności** - ile CO₂ zaoszczędziła nasza społeczność
- 🌳 **Widzieć równoważnik w uratowanych drzewach** dla każdej podróży
- 🎨 **Generować grafiki** do udostępniania w serwisach społecznościowych
- 👥 **Logować się** przez Discord lub email
- 💾 **Zapisywać podróże** z metadanymi (typ roweru, stacja)
- 📍 **Automatyczne dane lokalizacyjne** z geolokalizacji
- 🔄 **Synchronizacja danych** z chmurą Supabase
- ⚡ **Szybkie interfejsy** z wygenerowanymi grafikami PNG na żądanie

---

## Nowinki w ulepszeniu

### Nowe Funkcjonalności
- **Globalne statystyki społeczności**: Widok liczby podróży rowerem, CO₂ oszczędzonego globalnie, uratowanych drzew i liczby aktywnych użytkowników
- **Inteligentne wyszukiwanie stacji**: Sortowanie po odległości, wyświetlanie liczby dostępnych rowerów
- **Szczegółowe raporty czasowe**: Dokładne wyliczenia czasów przyjazdu dla obydwu środków transportu
- **Identyfikacja typu roweru**: Możliwość wskazania czy używasz własnego roweru czy bike-sharingu MEVO
- **Informacja o statusie netto**: Wizualne potwierdzenie czy podróż przynosi oszczędności czy emisje
- **Zaawansowane grafiki do udostępniania**: Raport statystyk użytkownika z pokazaniem wpływu netto

### Ulepszenia Techniczne
- **Optymalizacja wydajności**: Zmniejszone rozmiary żądań, szybsza przebudowa UI
- **Polskie interfejsy**: 100% tekstu w interfejsie w języku polskim
- **Responsywny design**: Obsługa urządzeń mobilnych z pełną funkcjonalnością
- **Bezpieczne uwierzytelnianie**: OAuth2 (Google, Discord) + email/hasło
- **Caching**: Inteligentne cache'owanie wyników stacji
- **Zoptymalizowana baza danych**: Efektywne zapytania do Supabase z indeksami

### Design & UX
- **Nowoczesny interfejs**: Minimalistyczny dark mode z akcentami zielonymi
- **Wizualizacja danych**: Bento grid dla przejrzystej prezentacji statystyk
- **Animacje**: Płynne przejścia i feedback wizualny dla interakcji
- **Dostępność**: ARIA labels, kontrast kolorów, responsywne fonty
- **Wskaźnik postępu**: Progress bar pokazujący wielkość CO₂ oszczędzonego

---

## Technologia

### Frontend
- **HTML5**, **CSS3**, **Vanilla JavaScript**
- Nowoczesny, responsywny design z CSS Grid i Flexbox
- Asynchroniczne operacje z Fetch API
- Lokalna geolokalizacja i integracja z mapami

### Backend
- **Flask** (Python)
- **PIL/Pillow** do generowania grafik PNG (1200x630 px) z gradientami
- **CORS** dla płynnej integracji frontend-backend
- **Logging** dla monitorowania błędów

### Baza danych
- **Supabase** (PostgreSQL)
- **Autoryzacja**: E-mail, hasło, Google OAuth, Discord OAuth
- **RLS** (Row-Level Security) dla bezpieczeństwa danych użytkownika
- **Tabele**: user_stats, journey_tracking, co2_calculations

### Zewnętrzne API
- **MEVO API** (GBFS) - stacje rowerowe, dostępność w czasie rzeczywistym
- **Haversine formula** dla precyzyjnego obliczania odległości geograficznej

### Narzędzia & Biblioteki
- **Python 3.9+**
- **Git** - kontrola wersji
- **Gunicorn** - produkcyjny serwer WSGI
- **Supabase JS Client** - synchronizacja chmury z frontendem

---

## Funkcjonalność

### 1. Obliczanie oszczędności CO₂
Wprowadź punkty startu i końca, a aplikacja obliczy:
- Odległość w kilometrach (algorytm Haversine'a)
- Oszczędności CO₂ w kilogramach
- Czas podróży (rower vs samochód)
- Ilość uratowanych drzew
- Informacje o najbliższych stacjach MEVO

**Wzór**: 0.12 kg CO₂ na kilometr (średnia emisja dla samochodu)

### 2. Śledzenie transportu
Po zalogowaniu możesz dokumentować każdą podróż, wybierając:
- 🚴 Rower (oszczędza CO₂) - z opcją wybrania typu (własny/MEVO)
- 🚗 Samochód (generuje CO₂)
- Wszystkie podróże są synchronizowane z chmurą

### 3. Bilans netto
Aplikacja oblicza Twój wpływ netto:
- **Zielony**: Oszczędzasz więcej CO₂, niż produkujesz ✓
- **Czerwony**: Wyższe emisje z samochodów ⚠️
- Historyczne dane są przechowywane i aktualizowane

### 4. Statystyki globalnej społeczności
Widok zagregowanych danych wszystkich użytkowników:
- Całkowita liczba kg CO₂ oszczędzonych
- Liczba podróży rowerem i samochodem
- Równoważnik w uratowanych drzewach
- Liczba aktywnych użytkowników aplikacji

### 5. Grafiki do mediów społecznych
Generuj efektowne grafiki PNG (1200x630 px):
- Pokazujące Twój bilans CO₂
- Dynamiczne kolory (zielony/czerwony)
- Statystyki podróży
- Gotowe do dzielenia się na Instagramie, Twitterze, TikToku

---

## Cechy

✅ **Bezpiecznie** - Twoje dane chronione przez RLS i OAuth  
✅ **Responsywne** - dostosowane do różnych urządzeń  
✅ **Szybkie** - zoptymalizowana wydajność z cachingiem  
✅ **Motywujące** - mechaniki gamifikacji w bilansie netto  
✅ **Łatwe udostępnianie** w mediach społecznościowych  
✅ **Globalne community** - zobacz wpływ całej społeczności  
✅ **Integracja API** - dane z realnych stacji MEVO

---

## Punkty końcowe API

### Publiczne
- `GET /health` - status aplikacji
- `GET /v1/nearby-stations` - stacje rowerowe w pobliżu
- `GET /v1/search-nearest-station` - szukaj najbliższej stacji
- `POST /v1/calculate-co2-savings` - oblicz oszczędności CO₂
- `GET /v1/global-stats` - globalne statystyki społeczności

### Z autoryzacją
- `POST /v1/save-journey` - zapisz podróż
- `GET /v1/user-stats/{user_id}` - statystyki użytkownika
- `GET /v1/share-graphic/{user_id}` - grafika oszczędności CO₂
- `GET /v1/share-graphic-stats/{user_id}` - grafika statystyk użytkownika

---

## Instalacja

```bash
pip install -r requirements.txt
export ADRES_SUPABASE="https://your-project.supabase.co"
export KLUCZ_SUPABASE="your_anon_key"
python app.py
```

---

## Zgodność z kryteriami konkursu

### Przydatność społeczna (1-5)
Aplikacja promuje zdrowy styl życia, świadomość ekologiczną i wspiera decyzje pro-środowiskowe. Integracja z realnym systemem MEVO zwiększa praktyczne zastosowanie.

### Pomysł (1-5)
Gamifikacja oszczędności CO₂ z wizualizacją wpływu na klimat jest innowacyjnym podejściem do zmiany nawyków transportowych.

### Wykonanie - Estetyka (1-3)
Nowoczesny dark mode z minimalistycznym designem, efektowne animacje, responsywna siatka CSS Grid.

### Wykonanie - Responsywność/Szybkość (1-3)
Aplikacja jest zoptymalizowana pod względem wydajności: szybkie żądania API, asynchroniczny JavaScript, cache'owanie wyników, minimalne TTFB.

### Wykorzystane technologie (0-2 bonus)
- **Real-time API** z MEVO (GBFS)
- **Generowanie grafik** PNG na serwerze
- **OAuth2** z Google i Discord
- **Geolokalizacja** w przeglądarce
- **Supabase** jako BaaS z RLS
- **Algoritmy geograficzne** (Haversine)
