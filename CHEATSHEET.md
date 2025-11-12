# Quick Reference Cheatsheet

## Setup (One Liner)
```bash
./setup.sh
```

## Run
```bash
make run        # Build & run
go run main.go providers.go  # Direct run
./co2-calculator  # Run binary
make dev        # Dev with hot reload
```

## Test API

### Health Check
```bash
curl http://localhost:3000/health
```

### List Providers
```bash
curl http://localhost:3000/providers
```

### Find Nearby Bikes (Warsaw)
```bash
curl "http://localhost:3000/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2"
```

### Calculate CO2 (Warsaw, 3.5km)
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

## Build

```bash
make build              # Build binary
CGO_ENABLED=0 go build -o co2-calculator main.go providers.go  # Manual build
make docker             # Build Docker image
docker run -p 3000:3000 co2-calculator  # Run Docker
```

## Documentation

| Document | Time | Content |
|----------|------|---------|
| QUICKSTART.md | 5 min | How to get started |
| MEVO_SETUP.md | 10 min | MEVO integration |
| README_GO.md | 30 min | Complete docs |
| EXAMPLES.md | 15 min | Test cases |
| DEPLOYMENT.md | 20 min | Production setup |
| PROJECT_SUMMARY.md | 15 min | Full overview |

## MEVO Integration

### What You Need
**NOTHING!** ✅

MEVO GBFS is:
- ✅ Free
- ✅ Public
- ✅ No auth required
- ✅ Already integrated

### Test MEVO Directly
```bash
curl -H "Client-Identifier: test" \
  https://gbfs.urbansharing.com/rowermevo.pl/station_information.json
```

### Customize (Optional)
Edit `providers.go`:
```go
SetHeader("Client-Identifier", "yourname-appname")
```

## Project Structure

```
Core:           main.go, providers.go, index.html
Config:         go.mod, Makefile, Dockerfile
Scripts:        setup.sh
Docs:           *.md files (7 guides)
```

## Key Endpoints

```
POST   /v1/calculate-co2-savings   ← Main endpoint
GET    /v1/nearby-stations          ← Find nearby
GET    /providers                   ← List providers
GET    /health                      ← Health check
```

## API Response (Example)

```json
{
  "success": true,
  "closest_vehicle": {
    "id": "123",
    "type": "bike",
    "provider": "MEVO",
    "name": "Station Name",
    "distance_km": 0.45,
    "bikes_available": 7
  },
  "distance_km": 3.5,
  "co2_savings_kg": 0.42,
  "travel_times": {
    "bike_minutes": "14 minutes",
    "car_minutes": "8 minutes"
  },
  "environmental_impact": {
    "co2_saved_grams": 420,
    "equivalent_trees": 0.02
  }
}
```

## Supported Providers

| Provider | Type | Coverage | Status |
|----------|------|----------|--------|
| MEVO | Bikes | 🇵🇱 Poland | ✅ |
| Nextbike | Bikes | 🌍 Global | ✅ |
| Hive | Scooters | 🇪🇺 EU | ✅ |
| VOI | Scooters | 🇪🇺 EU | 🔐 |
| Lime | Both | 🌍 Global | 🔐 |
| Tier | Scooters | 🇪🇺 EU | 🔐 |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | `go version` (need 1.21+) |
| Port in use | `PORT=8080 make run` |
| No bikes found | Use Warsaw coords: `52.2297,21.0122` |
| Slow response | Check internet, increase timeout |
| MEVO not working | Test: `curl https://gbfs.urbansharing.com/rowermevo.pl/station_information.json` |

## Deployment

```bash
# Docker
make docker
docker run -p 3000:3000 co2-calculator

# Native
make build
./co2-calculator

# systemd (Linux)
sudo systemctl start co2-calculator
sudo systemctl status co2-calculator
```

## Make Commands

```bash
make build        Build binary
make run          Build & run
make dev          Dev mode (hot reload)
make clean        Remove build artifacts
make test         Run tests
make docker       Build Docker image
make docker-run   Run Docker
make help         Show all commands
make lint         Run linter
make fmt          Format code
make deps         List dependencies
```

## Development

```bash
# Watch for changes
make dev

# Format code
make fmt

# Build & test
go test ./...

# View dependencies
go list -m all
```

## File Roles

| File | Role |
|------|------|
| main.go | API server, handlers |
| providers.go | Data sources (MEVO, Nextbike, etc) |
| index.html | Web UI |
| Makefile | Build commands |
| Dockerfile | Container config |

## Useful Coordinates

| City | Latitude | Longitude |
|------|----------|-----------|
| Warsaw (start) | 52.2297 | 21.0122 |
| Warsaw (dest) | 52.2500 | 21.0300 |
| Berlin | 52.5200 | 13.4050 |
| Amsterdam | 52.3676 | 4.9041 |
| Gdańsk | 54.3520 | 18.6466 |

## Performance

- Response: 2-5 seconds
- Requests/sec: 50-100
- Memory: ~50MB
- Binary size: ~8MB

## Constants (in main.go)

```go
CO2_PER_KM_CAR    = 0.12  // kg per km
BIKE_SPEED_KPH    = 15.0  // Average
SCOOTER_SPEED_KPH = 20.0  // Average
CAR_SPEED_KPH     = 40.0  // City
```

## Environment Variables

```bash
export GIN_MODE=release    # Production mode
export PORT=3000           # Server port
```

## Testing

```bash
# Health
curl http://localhost:3000/health

# Providers
curl http://localhost:3000/providers

# Nearby (2km radius, Warsaw)
curl "http://localhost:3000/v1/nearby-stations?latitude=52.2297&longitude=21.0122&radius=2"

# CO2 calculation
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{"latitude": 52.2297, "longitude": 21.0122, "destination_latitude": 52.2500, "destination_longitude": 21.0300}'
```

## Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run test
ab -n 1000 -c 100 http://localhost:3000/health
```

## Docker Quick Start

```bash
# Build
docker build -t co2-calc .

# Run
docker run -p 3000:3000 co2-calc

# Stop
docker stop <container-id>
```

## Common Tasks

```bash
# Build for production
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o co2-calculator main.go providers.go

# Run server
./co2-calculator

# Test endpoint
curl -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{"latitude": 52.2297, "longitude": 21.0122, "destination_latitude": 52.2500, "destination_longitude": 21.0300}'

# Check logs
journalctl -u co2-calculator -f

# Restart service
sudo systemctl restart co2-calculator
```

## Documentation Priority

**New users**: QUICKSTART.md → MEVO_SETUP.md
**Developers**: README_GO.md → EXAMPLES.md
**DevOps**: DEPLOYMENT.md → Dockerfile
**Reference**: This cheatsheet

---

Everything you need on one page! 📄
