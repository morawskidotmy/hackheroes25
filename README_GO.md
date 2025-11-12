# CO2 Bike Calculator API - Go Version

A high-performance, aggregated bike-sharing and scooter API that calculates CO2 savings by choosing eco-friendly transport instead of driving. Built in Go with support for multiple mobility providers.

## Features

✅ **Multi-Provider Aggregation** - Query 6+ providers simultaneously
✅ **Zero Data Storage** - All processing is stateless and ephemeral
✅ **Free & Open** - No authentication required, no API keys needed for public data
✅ **High Performance** - Concurrent requests with Go's goroutines
✅ **Local Deployment** - Single binary, runs anywhere
✅ **CO2 Calculations** - Accurate environmental impact metrics
✅ **Multiple Vehicle Types** - Bikes, scooters, and more

## Supported Providers

| Provider | Type | Coverage | Status |
|----------|------|----------|--------|
| **MEVO** | Bikes | Poland | ✅ Active |
| **Nextbike** | Bikes | Worldwide | ✅ Active |
| **VOI** | Scooters | EU | 🔐 Requires Auth |
| **Lime** | Bikes/Scooters | Worldwide | 🔐 Requires Auth |
| **Tier** | Scooters | EU | 🔐 Requires Auth |
| **Hive** | Scooters | EU | ✅ Active |
| **GBFS Generic** | Any | Any with GBFS | ✅ Extensible |

## Installation

### Prerequisites
- Go 1.21 or later
- No external databases or services required

### Setup

```bash
# Clone/navigate to project directory
cd /path/to/hackheroes2025

# Download dependencies
go mod download
go mod tidy

# Build the binary
go build -o co2-calculator

# Run the server
./co2-calculator
```

Server starts on `http://localhost:3000`

## Usage

### Quick Start

```bash
# Install & run
go run main.go providers.go

# In another terminal, test:
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 52.4064,
    "destination_longitude": 16.9252
  }'
```

### API Endpoints

#### 1. Calculate CO2 Savings (Main Endpoint)

**POST** `/v1/calculate-co2-savings`

Finds the closest bike/scooter across all providers and calculates CO2 savings.

**Request:**
```json
{
  "latitude": 52.2297,
  "longitude": 21.0122,
  "destination_latitude": 52.4064,
  "destination_longitude": 16.9252,
  "radius": 2.0
}
```

**Response:**
```json
{
  "success": true,
  "closest_vehicle": {
    "id": "123",
    "type": "bike",
    "provider": "MEVO",
    "name": "Station Name",
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
    "car_minutes": "8 minutes"
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

#### 2. Nearby Stations (Helper Endpoint)

**GET** `/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=1`

Returns all available vehicles within specified radius.

**Parameters:**
- `latitude` (required): Your latitude
- `longitude` (required): Your longitude  
- `radius` (optional): Search radius in km (default: 1)

**Response:**
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
      "is_available": true
    }
  ],
  "providers_queried": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"]
}
```

#### 3. List Providers

**GET** `/providers`

Returns available providers.

**Response:**
```json
{
  "success": true,
  "providers": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"],
  "count": 6
}
```

#### 4. Health Check

**GET** `/health`

Returns server status.

**Response:**
```json
{
  "status": "OK",
  "providers": 6
}
```

## Configuration

### Environment Variables

```bash
# Set Gin mode (debug, release)
export GIN_MODE=release

# Change port (default 3000)
export PORT=8080
```

### Constants (in main.go)

Modify these if needed:
```go
const (
	CO2_PER_KM_CAR    = 0.12  // kg CO2 per km (default: European car)
	BIKE_SPEED_KPH    = 15.0  // Average bike speed
	SCOOTER_SPEED_KPH = 20.0  // Average scooter speed
	CAR_SPEED_KPH     = 40.0  // Average city car speed
)
```

## Architecture

### Project Structure

```
├── main.go           # Core API server, request handlers
├── providers.go      # All provider implementations
├── go.mod            # Dependencies
├── index.html        # Web UI
└── README_GO.md      # This file
```

### Design Principles

1. **Concurrent Queries** - All providers queried in parallel using goroutines
2. **No State** - Stateless design, no databases, no caching
3. **Provider Abstraction** - All providers implement the `Provider` interface
4. **Error Isolation** - One provider failure doesn't affect others
5. **Zero Dependencies** - Only Gin (web framework) and Resty (HTTP client)

### Adding New Providers

To add a new provider:

1. Create a new struct implementing the `Provider` interface:
```go
type MyProvider struct {
	client *resty.Client
}

func NewMyProvider() *MyProvider {
	return &MyProvider{
		client: resty.New().SetTimeout(5 * time.Second),
	}
}

func (m *MyProvider) Name() string {
	return "MyProvider"
}

func (m *MyProvider) GetVehicles(latitude, longitude, radius float64) ([]Vehicle, error) {
	// Fetch and filter vehicles
	return vehicles, nil
}
```

2. Add to `GlobalProviders` in `init()` function in `main.go`:
```go
GlobalProviders = []Provider{
	NewMEVOProvider(),
	NewMyProvider(), // Add here
	// ...
}
```

## Performance

### Benchmarks

- **Concurrent Requests**: All providers queried in parallel
- **Response Time**: ~2-5 seconds (depends on provider API speed)
- **Memory Usage**: ~50MB at runtime
- **No Database**: All computation is in-memory

### Optimization Tips

1. Increase timeout if providers are slow:
```go
client: resty.New().SetTimeout(10 * time.Second)
```

2. Filter providers if some are slow:
```go
GlobalProviders = []Provider{
	NewMEVOProvider(), // Fast GBFS
	NewHiveProvider(), // Fast API
}
```

3. Run with release mode:
```bash
GIN_MODE=release go run main.go providers.go
```

## Error Handling

The API gracefully handles provider failures:
- If one provider fails, others continue
- Returns best results from available providers
- Returns 404 if no vehicles found
- Returns 400 for invalid coordinates

Example error response:
```json
{
  "error": "No bikes or scooters available in your area",
  "message": "Please try again later or expand your search radius",
  "providers_queried": ["MEVO", "Nextbike", "VOI", "Lime", "Tier", "Hive"]
}
```

## Authentication & Credentials

### Free Providers (No Auth)
- MEVO (GBFS)
- Nextbike
- Hive

### Requires Authentication
- **VOI**: Requires API key (phone + OTP verification)
- **Lime**: Requires session cookie + authentication
- **Tier**: Requires API key header

To enable these, add credentials in `providers.go`:
```go
func (v *VOIProvider) GetVehicles(...) ([]Vehicle, error) {
	// Add authentication logic
	// Replace empty implementation with actual API calls
}
```

## Deployment

### Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM golang:1.21-alpine AS build
WORKDIR /app
COPY . .
RUN go build -o co2-calculator

FROM alpine:latest
COPY --from=build /app/co2-calculator /
COPY index.html /
CMD ["/co2-calculator"]
```

Build and run:
```bash
docker build -t co2-calculator .
docker run -p 3000:3000 co2-calculator
```

### Linux Service

Create `/etc/systemd/system/co2-calculator.service`:
```ini
[Unit]
Description=CO2 Bike Calculator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/co2-calculator
ExecStart=/opt/co2-calculator/co2-calculator
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Testing

### Manual Tests

```bash
# Test with Warsaw coordinates
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 52.2500,
    "destination_longitude": 21.0200
  }'

# Get nearby stations
curl "http://localhost:3000/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2"

# Check health
curl http://localhost:3000/health

# List providers
curl http://localhost:3000/providers
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run 100 concurrent requests
ab -n 1000 -c 100 -p request.json \
  -T application/json \
  http://localhost:3000/v1/calculate-co2-savings
```

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process using port 3000
lsof -i :3000
kill -9 <PID>

# Or use different port
PORT=8080 go run main.go providers.go
```

### Slow Response

1. Check provider API status
2. Increase timeout in providers.go
3. Reduce radius parameter
4. Filter to faster providers

### Providers Not Returning Data

1. Check internet connection
2. Verify provider API is online
3. Check logs for specific errors
4. Some providers require authentication

## License

MIT - Free to use, modify, and distribute

## Future Enhancements

- [ ] Advanced route planning
- [ ] Weather integration
- [ ] Cost comparison (bike vs car fuel)
- [ ] Gamification (achievements, streak tracking)
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Trip analytics
- [ ] Provider-specific features
- [ ] Real-time traffic integration

## Support & Contribution

To add new providers or features:
1. Implement the `Provider` interface
2. Add error handling for API failures
3. Test with concurrent requests
4. Submit PR with documentation

## Contact

For issues or questions, check provider documentation:
- **MEVO**: kontakt@rowermevo.pl, +48 58 739 11 23
- **Nextbike**: https://nextbike.net
- **Lime**: https://lime.bike
- **VOI**: https://voiscooter.com
- **Tier**: https://www.tier.app
- **Hive**: https://www.hivelondon.com

---

**Built with ❤️ for a greener tomorrow**
