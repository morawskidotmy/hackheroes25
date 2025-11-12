# API Examples & Test Cases

Complete examples for testing the CO2 Bike Calculator API.

## Setup & Testing

### 1. Start the Server

```bash
# Option 1: Using make
make run

# Option 2: Direct build and run
go run main.go providers.go

# Option 3: Using the setup script
./setup.sh
```

Server starts on `http://localhost:3000`

## Test Cases

### Test 1: Basic CO2 Calculation (Warsaw, Poland)

**Scenario**: Calculate CO2 savings for a 3.5km trip in Warsaw center

**Request**:
```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 52.2500,
    "destination_longitude": 21.0300
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "closest_vehicle": {
    "id": "123",
    "type": "bike",
    "provider": "MEVO",
    "name": "Central Station",
    "location": {
      "latitude": 52.2345,
      "longitude": 21.0145
    },
    "distance_km": 0.45,
    "bikes_available": 7,
    "docks_available": 5,
    "is_available": true
  },
  "distance_km": 3.5,
  "co2_savings_kg": 0.42,
  "travel_times": {
    "bike_minutes": "14 minutes",
    "car_minutes": "5 minutes"
  },
  "environmental_impact": {
    "co2_per_km_car_grams": 120,
    "co2_saved_grams": 420,
    "equivalent_trees": 0.02
  },
  "message": "By choosing a bike instead of a car for this 3.50km trip, you save approximately 0.42kg of CO2 emissions!",
  "providers_queried": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"]
}
```

### Test 2: Nearby Stations (Warsaw)

**Scenario**: Find all bikes/scooters within 2km of current location

**Request**:
```bash
curl "http://localhost:3000/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2"
```

**Expected Response**:
```json
{
  "success": true,
  "count": 5,
  "stations": [
    {
      "id": "123",
      "type": "bike",
      "provider": "MEVO",
      "name": "Central Station",
      "location": {
        "latitude": 52.2345,
        "longitude": 21.0145
      },
      "distance_km": 0.3,
      "bikes_available": 7,
      "docks_available": 5,
      "is_available": true
    },
    {
      "id": "456",
      "type": "bike",
      "provider": "MEVO",
      "name": "East Station",
      "location": {
        "latitude": 52.2420,
        "longitude": 21.0220
      },
      "distance_km": 0.85,
      "bikes_available": 3,
      "docks_available": 8,
      "is_available": true
    }
  ],
  "providers_queried": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"]
}
```

### Test 3: Invalid Coordinates (Should Fail)

**Scenario**: Test with invalid latitude > 90

**Request**:
```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 150.0,
    "longitude": 21.0122,
    "destination_latitude": 52.2500,
    "destination_longitude": 21.0300
  }'
```

**Expected Response**:
```json
{
  "error": "Invalid coordinates"
}
```

HTTP Status: 400

### Test 4: No Vehicles Available (Should Fail)

**Scenario**: Search in remote area with no bike-sharing

**Request**:
```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 10.5,
    "longitude": 20.5,
    "destination_latitude": 10.7,
    "destination_longitude": 20.7
  }'
```

**Expected Response**:
```json
{
  "error": "No bikes or scooters available in your area",
  "message": "Please try again later or expand your search radius",
  "providers_queried": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"]
}
```

HTTP Status: 404

### Test 5: Health Check

**Request**:
```bash
curl http://localhost:3000/health
```

**Expected Response**:
```json
{
  "status": "OK",
  "providers": 6
}
```

### Test 6: List Available Providers

**Request**:
```bash
curl http://localhost:3000/providers
```

**Expected Response**:
```json
{
  "success": true,
  "providers": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"],
  "count": 6
}
```

## Real-World Examples

### Example 1: Daily Commute (Berlin to Checkpoint)

**Scenario**: 8km commute from Charlottenburg to Mitte district

**Request**:
```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.5200,
    "longitude": 13.4050,
    "destination_latitude": 52.5170,
    "destination_longitude": 13.3890
  }'
```

**Expected Calculation**:
- Distance: ~3.0 km
- CO2 Savings: 0.36 kg
- Equivalent Trees: 0.017
- Bike Time: ~12 minutes
- Car Time: ~8 minutes (in ideal conditions)

### Example 2: Long Weekend Trip (Berlin to Potsdam)

**Scenario**: 30km trip using multiple transportation

**Request**:
```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.5200,
    "longitude": 13.4050,
    "destination_latitude": 52.3906,
    "destination_longitude": 13.0645
  }'
```

**Expected Calculation**:
- Distance: ~30.0 km
- CO2 Savings: 3.6 kg
- Equivalent Trees: 0.17
- Bike Time: ~2 hours
- Car Time: ~35 minutes

### Example 3: Urban Scooter Rental (EU Cities)

**Scenario**: Quick trip in city with multiple scooter providers

**Request** (Amsterdam):
```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.3676,
    "longitude": 4.9041,
    "destination_latitude": 52.3750,
    "destination_longitude": 4.9200
  }'
```

**Expected Result**: Aggregated results from VOI, Tier, and Hive scooters

## Performance Testing

### Load Test with Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Create a test file (test.json)
echo '{
  "latitude": 52.2297,
  "longitude": 21.0122,
  "destination_latitude": 52.2500,
  "destination_longitude": 21.0300
}' > test.json

# Run 1000 requests with 50 concurrent connections
ab -n 1000 -c 50 -p test.json -T application/json \
  http://localhost:3000/v1/calculate-co2-savings
```

**Expected Performance**:
- Requests/sec: 50-100
- Mean response time: 2-5 seconds
- Memory usage: ~50MB

### Load Test with Wrk

```bash
# Install wrk
git clone https://github.com/wg/wrk.git
cd wrk
make

# Create Lua script (test.lua)
cat > test.lua << 'EOF'
request = function()
   wrk.method = "POST"
   wrk.body = '{"latitude": 52.2297, "longitude": 21.0122, "destination_latitude": 52.2500, "destination_longitude": 21.0300}'
   wrk.headers["Content-Type"] = "application/json"
   return wrk.format(nil)
end
EOF

# Run test
./wrk -t4 -c100 -d30s -s test.lua http://localhost:3000/v1/calculate-co2-savings
```

## Integration Examples

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:3000"

def calculate_co2_savings(lat, lng, dest_lat, dest_lng):
    payload = {
        "latitude": lat,
        "longitude": lng,
        "destination_latitude": dest_lat,
        "destination_longitude": dest_lng
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/calculate-co2-savings",
        json=payload
    )
    
    return response.json()

# Example usage
result = calculate_co2_savings(52.2297, 21.0122, 52.2500, 21.0300)
print(f"CO2 Saved: {result['co2_savings_kg']} kg")
print(f"Provider: {result['closest_vehicle']['provider']}")
```

### JavaScript Client

```javascript
const API_URL = 'http://localhost:3000';

async function calculateCO2Savings(lat, lng, destLat, destLng) {
  try {
    const response = await fetch(`${API_URL}/v1/calculate-co2-savings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude: lat,
        longitude: lng,
        destination_latitude: destLat,
        destination_longitude: destLng,
      }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }

    return data;
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

// Example usage
calculateCO2Savings(52.2297, 21.0122, 52.2500, 21.0300)
  .then(result => {
    console.log(`CO2 Saved: ${result.co2_savings_kg} kg`);
    console.log(`Provider: ${result.closest_vehicle.provider}`);
  });
```

### cURL Scripts

#### Save as `test-api.sh`

```bash
#!/bin/bash

API_URL="http://localhost:3000"

# Test 1: Health check
echo "=== Health Check ==="
curl -s $API_URL/health | jq .

# Test 2: List providers
echo -e "\n=== Providers ==="
curl -s $API_URL/providers | jq .

# Test 3: Calculate CO2 savings
echo -e "\n=== CO2 Calculation ==="
curl -s -X POST $API_URL/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 52.2500,
    "destination_longitude": 21.0300
  }' | jq .

# Test 4: Nearby stations
echo -e "\n=== Nearby Stations ==="
curl -s "$API_URL/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2" | jq .
```

Run with:
```bash
chmod +x test-api.sh
./test-api.sh
```

## Debugging

### Enable Debug Mode

```bash
export GIN_MODE=debug
go run main.go providers.go
```

### Check Provider Connectivity

```bash
# Test MEVO API
curl -H "Client-Identifier: test" \
  https://gbfs.urbansharing.com/rowermevo.pl/station_information.json | jq .

# Test Nextbike API
curl https://api.nextbike.net/maps/nextbike-live.json?city=362 | jq .
```

### Monitor Requests

```bash
# In one terminal, run server with debug
export GIN_MODE=debug
go run main.go providers.go

# In another, make requests - you'll see detailed logs
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{"latitude": 52.2297, "longitude": 21.0122, "destination_latitude": 52.2500, "destination_longitude": 21.0300}'
```

## Batch Testing

### Test Multiple Cities

Create `cities.json`:
```json
[
  {"name": "Warsaw", "lat": 52.2297, "lng": 21.0122, "dest_lat": 52.2500, "dest_lng": 21.0300},
  {"name": "Berlin", "lat": 52.5200, "lng": 13.4050, "dest_lat": 52.5170, "dest_lng": 13.3890},
  {"name": "Amsterdam", "lat": 52.3676, "lng": 4.9041, "dest_lat": 52.3750, "dest_lng": 4.9200}
]
```

Run with Python:
```python
import json
import requests

with open('cities.json') as f:
    cities = json.load(f)

for city in cities:
    payload = {
        "latitude": city['lat'],
        "longitude": city['lng'],
        "destination_latitude": city['dest_lat'],
        "destination_longitude": city['dest_lng']
    }
    
    response = requests.post(
        'http://localhost:3000/v1/calculate-co2-savings',
        json=payload
    )
    
    data = response.json()
    print(f"{city['name']}: {data['co2_savings_kg']}kg CO2 saved")
```

## Expected Results Summary

| Scenario | Distance | CO2 Saved | Trees | Bike Time |
|----------|----------|-----------|-------|-----------|
| Short trip (1km) | 1.0 km | 0.12 kg | 0.006 | 4 min |
| Medium trip (3km) | 3.0 km | 0.36 kg | 0.017 | 12 min |
| Long trip (10km) | 10.0 km | 1.2 kg | 0.057 | 40 min |
| Very long (30km) | 30.0 km | 3.6 kg | 0.17 | 2 hrs |

## Troubleshooting Tests

### No Vehicles Found
- Check radius parameter
- Verify coordinates are in city with bike-sharing
- Check provider API availability

### Slow Response Time
- Increase timeout in providers.go
- Check internet connection
- Reduce number of providers

### Provider Data Mismatch
- Verify provider API is online
- Check API response format
- Review logs with debug mode enabled

---

For more information, see README_GO.md and DEPLOYMENT.md
