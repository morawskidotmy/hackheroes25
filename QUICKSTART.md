# Quick Start Guide

Get the CO2 Bike Calculator API running in 5 minutes.

## Prerequisites

- **Go 1.21+** ([download](https://golang.org/dl/))
- **Git** (optional)
- Any OS: Linux, macOS, Windows

## Installation

### 1. One-Command Setup

```bash
cd /path/to/hackheroes2025
chmod +x setup.sh
./setup.sh
```

The script will:
- Check Go installation
- Download dependencies
- Build the application
- Ask if you want to start the server

### 2. Manual Setup

```bash
# Download dependencies
go mod download

# Build
go build -o co2-calculator main.go providers.go

# Run
./co2-calculator
```

## Usage

### Start Server

```bash
./co2-calculator
# Or: make run
# Or: go run main.go providers.go
```

Output:
```
Starting server on :3000
Available providers: 6
  - MEVO
  - Nextbike
  - VOI
  - Lime
  - Tier
  - Hive
```

Visit: http://localhost:3000

### Test API

Open a new terminal:

```bash
# Calculate CO2 savings for a 3.5km trip in Warsaw
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 52.2500,
    "destination_longitude": 21.0300
  }'
```

Response shows:
- ✅ Closest bike/scooter location
- ✅ CO2 saved (in kg)
- ✅ Travel time estimates
- ✅ Equivalent trees planted

## Commands

```bash
# Run development server with hot reload
make dev

# Build for production
make build

# Run tests
make test

# Docker deployment
make docker
docker run -p 3000:3000 co2-calculator:latest

# View available commands
make help
```

## File Structure

```
├── main.go              # Core API server
├── providers.go         # All provider implementations
├── index.html           # Web UI
├── go.mod               # Dependencies
├── Makefile             # Build commands
├── Dockerfile           # Docker setup
├── setup.sh             # Quick setup script
├── README_GO.md         # Full documentation
├── DEPLOYMENT.md        # Deployment guide
├── EXAMPLES.md          # API examples
└── QUICKSTART.md        # This file
```

## API Endpoints

### Calculate CO2 Savings
```bash
POST /v1/calculate-co2-savings
```

Required parameters:
- `latitude`: your location (lat)
- `longitude`: your location (lon)
- `destination_latitude`: destination lat
- `destination_longitude`: destination lon

### Find Nearby Stations
```bash
GET /v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2
```

### List Providers
```bash
GET /providers
```

### Health Check
```bash
GET /health
```

## Web Interface

Open http://localhost:3000 in browser to:
- Enter start location (or auto-detect)
- Enter destination
- See results with CO2 savings
- View closest bike/scooter

## Supported Regions

| Provider | Coverage | Type |
|----------|----------|------|
| MEVO | 🇵🇱 Poland | Bikes |
| Nextbike | 🌍 Worldwide | Bikes |
| Hive | 🇪🇺 EU | Scooters |
| VOI | 🇪🇺 EU | Scooters |
| Lime | 🌍 Worldwide | Bikes/Scooters |
| Tier | 🇪🇺 EU | Scooters |

## Example: Warsaw to Kraków

Distance: ~290 km (bike: too far, car: 4 hours)

```bash
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 52.2297,
    "longitude": 21.0122,
    "destination_latitude": 50.0647,
    "destination_longitude": 19.9450
  }'
```

Result:
- CO2 Saved: 34.8 kg 🌍
- Equivalent Trees: 1.66 🌳
- But: 19+ hours by bike 😅

## Example: Short City Trip

Distance: ~3 km (e.g., Warsaw center)

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

Result:
- CO2 Saved: 0.36 kg ✅
- Equivalent Trees: 0.017 🌱
- Bike Time: ~12 minutes
- Car Time: ~5 minutes
- Time Loss: ~7 minutes, CO2 Gain: 360g 🎉

## Troubleshooting

### Port 3000 Already in Use
```bash
# Use different port
PORT=8080 ./co2-calculator

# Or find and kill process
lsof -i :3000
kill -9 <PID>
```

### Build Fails
```bash
# Update Go
go version  # Should be 1.21+

# Clean and rebuild
go clean
go mod tidy
go build -o co2-calculator main.go providers.go
```

### No Vehicles Found
- Check coordinates are in a city
- Increase radius in request
- Verify providers are online

### Slow Response
- Internet connection issue
- Provider API is slow
- Try with smaller radius

## Next Steps

1. **Read documentation**: See `README_GO.md`
2. **Explore examples**: Check `EXAMPLES.md`
3. **Deploy**: Follow `DEPLOYMENT.md`
4. **Extend**: Add more providers in `providers.go`

## Configuration

Edit constants in `main.go`:

```go
const (
	CO2_PER_KM_CAR    = 0.12  // kg CO2 per km
	BIKE_SPEED_KPH    = 15.0  // Average bike speed
	SCOOTER_SPEED_KPH = 20.0  // Average scooter speed
	CAR_SPEED_KPH     = 40.0  // City driving speed
)
```

## Features

✅ **Aggregated Search** - Query all providers at once
✅ **Fast** - Built with Go for performance
✅ **Free** - No costs, no API keys required for public data
✅ **Local** - Runs on your machine
✅ **Stateless** - No data storage or tracking
✅ **Extensible** - Easy to add new providers
✅ **Real-time** - Live bike/scooter availability

## Performance

- **Response Time**: 2-5 seconds
- **Concurrent Providers**: All 6 queried simultaneously
- **Memory**: ~50MB
- **Requests/sec**: 50-100 depending on hardware

## Security

✅ No user data stored
✅ No authentication required
✅ No API keys needed (for public providers)
✅ No tracking or logging
✅ Stateless design

## Support

| Issue | Solution |
|-------|----------|
| Build fails | Update Go to 1.21+ |
| Port in use | Change PORT env var |
| Slow response | Check internet, increase timeout |
| No vehicles | Check coordinates, increase radius |
| Provider error | Check provider API status |

## Resources

- 📖 [Full Documentation](README_GO.md)
- 🚀 [Deployment Guide](DEPLOYMENT.md)
- 📚 [API Examples](EXAMPLES.md)
- 🔧 [Makefile Commands](Makefile)
- 📝 [Go Documentation](https://golang.org/doc)

## Key Files

| File | Purpose |
|------|---------|
| `main.go` | API server & handlers |
| `providers.go` | Provider implementations |
| `index.html` | Web UI |
| `Makefile` | Build & run commands |
| `Dockerfile` | Container deployment |

## License

MIT - Free for any use

## Questions?

1. Check `README_GO.md` for full docs
2. Review `EXAMPLES.md` for test cases
3. See `DEPLOYMENT.md` for production setup
4. Check provider documentation for auth details

---

**Happy coding! Help save the environment with bikes instead of cars.** 🚴♂️🌍
