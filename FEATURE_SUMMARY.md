# New Features Summary

## Overview
Added user login (existing) + per-journey tracking with transport choice selection (bike/car), nearest station search, and net neutrality calculation.

## 1. Nearest Station Search
**Endpoint**: `GET /v1/search-nearest-station`
- Search for the nearest MEVO bike station from user's current location
- Parameters: `latitude`, `longitude`, `radius` (optional, default 2.0km)
- Returns: Station name, bikes available, distance
- UI: "🔍 Find Station" button shows station info below the map

## 2. Transport Choice Selection (Bike/Car)
**Frontend Feature**:
- After calculating a route, users can select "🚴 Bike" or "🚗 Car"
- Selection appears only when logged in
- Shows net neutrality badge:
  - Green (✓) for bike: "This journey saves CO₂"
  - Red (⚠️) for car: "This journey produces CO₂"
- "Save Journey" button to record the choice

## 3. Journey Tracking
**Endpoint**: `POST /v1/save-journey`
- Saves each journey with:
  - User ID, coordinates, distance
  - Transport choice (bike/car)
  - Potential CO₂ savings
  - Nearest station info (if searched)
- Automatically updates user stats

**Database Table**: `journey_tracking`
- `id`: Journey ID
- `user_id`: User identifier
- `start_lat/lon, end_lat/lon`: Coordinates
- `distance_km`: Calculated distance
- `chosen_transport`: 'bike' or 'car'
- `potential_co2_savings_kg`: CO₂ savings if bike chosen
- `nearest_station_name`: Name of nearest station
- `created_at`: Timestamp

## 4. Per-User Statistics
**Endpoint**: `GET /v1/user-stats/<user_id>`
- Returns:
  - `total_co2_kg`: Total CO₂ saved from all bike journeys
  - `bike_journeys`: Count of bike journeys
  - `car_journeys`: Count of car journeys
  - `net_neutral`: Boolean - true if total CO₂ saved >= estimated CO₂ from car journeys
  - `equivalent_trees`: Trees equivalent to CO₂ saved

**Database Table**: `user_stats`
- `user_id`: Primary key
- `total_co2_saved_kg`: Cumulative CO₂ from bike journeys
- `total_bike_journeys`: Count
- `total_car_journeys`: Count
- `net_neutral`: True if user is net carbon neutral
- `last_updated`: Timestamp

## 5. Net Neutrality Calculation
**Logic**:
```
net_neutral = total_co2_saved_kg >= (total_car_journeys × 0.12kg_CO2_per_km × avg_10km_distance)
```
- Estimated average journey: 10km
- CO₂ per km by car: 0.12kg (standard)
- User is net neutral when total savings ≥ total car journey emissions

**Display**:
- Share section shows "✓ Your Impact (Net Neutral)" when net_neutral = true
- Journey save shows badge with status

## 6. Database Changes

### New Tables

#### `journey_tracking`
```sql
CREATE TABLE journey_tracking (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  start_lat DECIMAL(10, 6),
  start_lon DECIMAL(10, 6),
  end_lat DECIMAL(10, 6),
  end_lon DECIMAL(10, 6),
  distance_km DECIMAL(10, 2),
  chosen_transport VARCHAR(50) CHECK (chosen_transport IN ('bike', 'car')),
  potential_co2_savings_kg DECIMAL(10, 3),
  nearest_station_name VARCHAR(255),
  nearest_station_lat DECIMAL(10, 6),
  nearest_station_lon DECIMAL(10, 6),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `user_stats`
```sql
CREATE TABLE user_stats (
  user_id VARCHAR(255) PRIMARY KEY,
  total_co2_saved_kg DECIMAL(10, 3) DEFAULT 0,
  total_bike_journeys INT DEFAULT 0,
  total_car_journeys INT DEFAULT 0,
  net_neutral BOOLEAN DEFAULT FALSE,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7. UI Components Added

### Find Station Button
- Location: Next to "📍 My Location" button
- Shows nearest MEVO station with distance and available bikes
- Green border when found, red when not found

### Transport Choice Section (Below Stats)
- Visible only when:
  - User is logged in
  - A calculation has been performed
- Two buttons:
  - "🚴 Bike" (green border)
  - "🚗 Car" (red border)
- Selected button highlighted
- Net neutrality badge below buttons
- "Save Journey" button to record choice

### Net Neutral Status
- Shown in share section title
- Displayed in journey save confirmation
- Tracked in user stats endpoint

## 8. Integration with Existing Features

- **Login**: Transport choice only visible when logged in
- **Share Section**: Updated to show "Net Neutral" status
- **User Stats**: Now includes journey counts and net neutral flag
- **Backward Compatible**: Legacy co2_calculations table still supported

## 9. API Changes

### New Endpoints
1. `GET /v1/search-nearest-station` - Find nearest station
2. `POST /v1/save-journey` - Save journey with transport choice

### Updated Endpoints
1. `GET /v1/user-stats/<user_id>` - Now includes:
   - `bike_journeys`
   - `car_journeys`
   - `net_neutral`

## Implementation Notes

- All journey data is scoped to user via RLS policies
- Net neutrality calculation considers average 10km journey length
- Station search respects user privacy (uses geolocation)
- Saving journey is optional - calculation alone doesn't require it
- Transport choice is required to save journey (if user chooses to)
