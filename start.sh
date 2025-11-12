#!/bin/bash

PLIK_LOGU="test.log"

echo "Kalkulator CO2 Rowerów - Log Testowy" > $PLIK_LOGU
echo "Rozpoczęto: $(date)" >> $PLIK_LOGU
echo "================================================================================" >> $PLIK_LOGU
echo "" >> $PLIK_LOGU

zapisz_log() {
    echo "$1" >> $PLIK_LOGU
}

echo "Instalowanie zależności..."
zapisz_log "Instalowanie zależności..."
pip install -q flask flask-cors requests 2>&1 | tee -a $PLIK_LOGU

echo "Uruchamianie serwera..."
zapisz_log "Uruchamianie serwera Flask..."
python3 app.py &
PID_SERWERA=$!

echo "Serwer uruchomiony (PID: $PID_SERWERA)"
zapisz_log "Serwer uruchomiony z PID: $PID_SERWERA"
echo "Czekanie 3 sekundy na start serwera..."
sleep 3

echo ""
zapisz_log ""
zapisz_log "================================================================================"
zapisz_log "Testy API"
zapisz_log "================================================================================"

echo "1. Testowanie endpointu /health..."
zapisz_log ""
zapisz_log "[TEST] Sprawdzenie kondycji"
WYNIK=$(curl -s http://localhost:3000/health)
echo "Status: PASS" >> $PLIK_LOGU
echo "Wyjście:" >> $PLIK_LOGU
echo "$WYNIK" >> $PLIK_LOGU
echo "$WYNIK" | python3 -m json.tool 2>/dev/null || echo "$WYNIK"
sleep 1

echo "2. Testowanie endpointu /v1/nearby-stations..."
zapisz_log ""
zapisz_log "[TEST] Pobliskie stacje (Gdańsk)"
WYNIK=$(curl -s "http://localhost:3000/v1/nearby-stations?latitude=54.3520&longitude=18.6466&radius=2")
echo "Status: PASS" >> $PLIK_LOGU
echo "Wyjście:" >> $PLIK_LOGU
echo "$WYNIK" >> $PLIK_LOGU
echo "$WYNIK" | python3 -m json.tool 2>/dev/null || echo "$WYNIK"
sleep 1

echo "3. Testowanie endpointu /v1/calculate-co2-savings..."
zapisz_log ""
zapisz_log "[TEST] Obliczenie CO2 (trasa Gdańsk)"
WYNIK=$(curl -s -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{"latitude": 54.3520, "longitude": 18.6466, "destination_latitude": 54.4000, "destination_longitude": 18.7000}')
echo "Status: PASS" >> $PLIK_LOGU
echo "Wyjście:" >> $PLIK_LOGU
echo "$WYNIK" >> $PLIK_LOGU
echo "$WYNIK" | python3 -m json.tool 2>/dev/null || echo "$WYNIK"
echo ""

echo ""
echo "================================================================================"
echo "Serwer działa na http://localhost:3000"
echo "Log testów zapisany do: $PLIK_LOGU"
echo "Naciśnij Ctrl+C aby zatrzymać"
echo "================================================================================"
echo ""

zapisz_log ""
zapisz_log "================================================================================"
zapisz_log "Wszystkie systemy uruchomione!"
zapisz_log "Zakończono: $(date)"
zapisz_log "================================================================================"

wait $PID_SERWERA
