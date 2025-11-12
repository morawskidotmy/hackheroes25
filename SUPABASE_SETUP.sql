CREATE TABLE obliczenia_co2 (
  id BIGSERIAL PRIMARY KEY,
  uzytkownik_id VARCHAR(255) NOT NULL,
  oszczedzony_co2_kg DECIMAL(10, 3) NOT NULL,
  dystans_km DECIMAL(10, 2) NOT NULL,
  start_lat DECIMAL(10, 6) NOT NULL,
  start_lon DECIMAL(10, 6) NOT NULL,
  koniec_lat DECIMAL(10, 6) NOT NULL,
  koniec_lon DECIMAL(10, 6) NOT NULL,
  utworzono TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  zaktualizowano TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE śledzenie_podrozy (
  id BIGSERIAL PRIMARY KEY,
  uzytkownik_id VARCHAR(255) NOT NULL,
  start_lat DECIMAL(10, 6) NOT NULL,
  start_lon DECIMAL(10, 6) NOT NULL,
  koniec_lat DECIMAL(10, 6) NOT NULL,
  koniec_lon DECIMAL(10, 6) NOT NULL,
  dystans_km DECIMAL(10, 2) NOT NULL,
  wybrany_transport VARCHAR(50) NOT NULL CHECK (wybrany_transport IN ('rower', 'samochod')),
  potencjalny_oszczedzony_co2_kg DECIMAL(10, 3),
  nazwa_najblizszej_stacji VARCHAR(255),
  najblisza_stacja_lat DECIMAL(10, 6),
  najblisza_stacja_lon DECIMAL(10, 6),
  utworzono TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  zaktualizowano TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE statystyki_uzytkownika (
  uzytkownik_id VARCHAR(255) PRIMARY KEY,
  laczsny_oszczedzony_co2_kg DECIMAL(10, 3) DEFAULT 0,
  laczsne_podroze_rowerem INT DEFAULT 0,
  laczsne_podroze_samochodem INT DEFAULT 0,
  neutralny_netto BOOLEAN DEFAULT FALSE,
  ostatnio_zaktualizowano TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_obliczenia_co2_uzytkownik_id ON obliczenia_co2(uzytkownik_id);
CREATE INDEX idx_obliczenia_co2_utworzono ON obliczenia_co2(utworzono);
CREATE INDEX idx_śledzenie_podrozy_uzytkownik_id ON śledzenie_podrozy(uzytkownik_id);
CREATE INDEX idx_śledzenie_podrozy_utworzono ON śledzenie_podrozy(utworzono);

ALTER TABLE obliczenia_co2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE śledzenie_podrozy ENABLE ROW LEVEL SECURITY;
ALTER TABLE statystyki_uzytkownika ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Użytkownicy mogą widzieć swoje obliczenia"
  ON obliczenia_co2
  FOR SELECT
  USING (uzytkownik_id = auth.uid()::text);

CREATE POLICY "Użytkownicy mogą wstawiać swoje obliczenia"
  ON obliczenia_co2
  FOR INSERT
  WITH CHECK (uzytkownik_id = auth.uid()::text);

CREATE POLICY "Użytkownicy mogą widzieć swoje podróże"
  ON śledzenie_podrozy
  FOR SELECT
  USING (uzytkownik_id = auth.uid()::text);

CREATE POLICY "Użytkownicy mogą wstawiać swoje podróże"
  ON śledzenie_podrozy
  FOR INSERT
  WITH CHECK (uzytkownik_id = auth.uid()::text);

CREATE POLICY "Użytkownicy mogą widzieć swoje statystyki"
  ON statystyki_uzytkownika
  FOR SELECT
  USING (uzytkownik_id = auth.uid()::text);

CREATE POLICY "Użytkownicy mogą aktualizować swoje statystyki"
  ON statystyki_uzytkownika
  FOR UPDATE
  USING (uzytkownik_id = auth.uid()::text);
