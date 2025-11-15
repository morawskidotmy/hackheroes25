#!/usr/bin/env python3

import subprocess
import time
import sys
import signal
import os
from datetime import datetime

ZIELONY = '\033[92m'
NIEBIESKI = '\033[94m'
ZOLTY = '\033[93m'
CZERWONY = '\033[91m'
RESET = '\033[0m'

PLIK_LOGU = 'test.log'


def drukuj_status(msg, kolor=NIEBIESKI):
    print(f"{kolor}[*] {msg}{RESET}")

def drukuj_sukces(msg):
    print(f"{ZIELONY}[✓] {msg}{RESET}")

def drukuj_blad(msg):
    print(f"{CZERWONY}[✗] {msg}{RESET}")

def drukuj_ostrzezenie(msg):
    print(f"{ZOLTY}[!] {msg}{RESET}")

def zapisz_log(msg):
    with open(PLIK_LOGU, 'a') as f:
        f.write(msg + '\n')

def czysc_log():
    with open(PLIK_LOGU, 'w') as f:
        f.write(f"sqrt(CO) - Kalkulator CO2 Rowerów - Log Testowy\n")
        f.write(f"Rozpoczęto: {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")

procesy = []

def czyszczenie(signum, frame):
    drukuj_ostrzezenie("Zamykanie...")
    zapisz_log("\n" + "=" * 80)
    zapisz_log(f"Zamknięto: {datetime.now()}")
    
    for proc in procesy:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
    drukuj_status("Czyszczenie ukończone")
    sys.exit(0)

signal.signal(signal.SIGINT, czyszczenie)
signal.signal(signal.SIGTERM, czyszczenie)

def uruchom_cmd(cmd, nazwa):
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        procesy.append(proc)
        stdout, stderr = proc.communicate()
        
        zapisz_log(f"\n[TEST] {nazwa}")
        zapisz_log(f"Polecenie: {cmd}")
        zapisz_log(f"Status: {'PASS' if proc.returncode == 0 else 'FAIL'}")
        
        if stdout:
            zapisz_log(f"Wyjście:\n{stdout}")
        if stderr:
            zapisz_log(f"Błąd:\n{stderr}")
        
        if proc.returncode == 0:
            drukuj_sukces(f"{nazwa}")
            return True
        else:
            drukuj_blad(f"{nazwa}")
            if stderr:
                print(f"  Błąd: {stderr[:100]}")
            return False
    except Exception as e:
        drukuj_blad(f"{nazwa} błąd: {e}")
        zapisz_log(f"\nWyjątek w {nazwa}: {e}")
        return False

def uruchom_serwer():
    try:
        proc = subprocess.Popen(
            "python3 app.py",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid
        )
        procesy.append(proc)
        drukuj_sukces("Serwer uruchomiony (PID: {})".format(proc.pid))
        zapisz_log(f"Serwer uruchomiony z PID: {proc.pid}")
        return proc
    except Exception as e:
        drukuj_blad(f"Nie udało się uruchomić serwera: {e}")
        zapisz_log(f"Nie udało się uruchomić serwera: {e}")
        return None

def testuj_api():
    drukuj_status("Czekanie 3 sekundy na start serwera...")
    time.sleep(3)
    
    zapisz_log("\n" + "-" * 80)
    zapisz_log("Testy API")
    zapisz_log("-" * 80)
    
    drukuj_status("Testowanie endpointu /health...")
    uruchom_cmd(
        'curl -s http://localhost:3000/health',
        "Sprawdzenie kondycji"
    )
    time.sleep(1)
    
    drukuj_status("Testowanie endpointu /v1/nearby-stations...")
    uruchom_cmd(
        'curl -s "http://localhost:3000/v1/nearby-stations?latitude=54.3520&longitude=18.6466&radius=2"',
        "Pobliskie stacje (Gdańsk)"
    )
    time.sleep(1)
    
    drukuj_status("Testowanie endpointu /v1/calculate-co2-savings...")
    uruchom_cmd(
        '''curl -s -X POST http://localhost:3000/v1/calculate-co2-savings \\
          -H "Content-Type: application/json" \\
          -d '{"latitude": 54.3520, "longitude": 18.6466, "destination_latitude": 54.4000, "destination_longitude": 18.7000}' ''',
        "Obliczenie CO2 (trasa Gdańsk)"
    )
    
    drukuj_status("Testowanie endpointu /v1/global-stats...")
    uruchom_cmd(
        'curl -s http://localhost:3000/v1/global-stats',
        "Globalne statystyki"
    )

def main():
    czysc_log()
    
    drukuj_status("Uruchamianie sqrt(CO) - Kalkulatora CO2 Rowerów...")
    zapisz_log("Uruchamianie sqrt(CO) - Kalkulatora CO2 Rowerów...\n")
    print()
    
    drukuj_status("Instalowanie zależności...")
    zapisz_log("Instalowanie zależności...")
    if not uruchom_cmd("pip install -q flask flask-cors requests supabase pillow python-dotenv gunicorn 2>&1", "Instalacja zależności"):
        drukuj_ostrzezenie("Niektóre zależności mogą nie być zainstalowane, kontynuowanie...")
        zapisz_log("OSTRZEŻENIE: Niektóre zależności mogą nie być zainstalowane")
    print()
    
    drukuj_status("Uruchamianie serwera Flask...")
    zapisz_log("\nUruchamianie serwera Flask...")
    proc_serwera = uruchom_serwer()
    if not proc_serwera:
        drukuj_blad("Nie udało się uruchomić serwera")
        zapisz_log("KRYTYCZNE: Nie udało się uruchomić serwera")
        return 1
    time.sleep(2)
    print()
    
    drukuj_status("Uruchamianie testów API...")
    zapisz_log("\nUruchamianie testów API...")
    testuj_api()
    print()
    
    drukuj_sukces("Wszystkie systemy uruchomione!")
    zapisz_log("\n" + "=" * 80)
    zapisz_log("Wszystkie systemy uruchomione pomyślnie!")
    zapisz_log(f"Serwer uruchomiony: {datetime.now()}")
    zapisz_log("=" * 80)
    
    drukuj_status("Serwer działa na http://localhost:3000")
    drukuj_status(f"Log testów: {PLIK_LOGU}")
    drukuj_status("Naciśnij Ctrl+C aby zatrzymać")
    print()
    
    try:
        proc_serwera.wait()
    except KeyboardInterrupt:
        czyszczenie(None, None)

if __name__ == '__main__':
    sys.exit(main())
