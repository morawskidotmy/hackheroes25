# Deployment Guide

This guide covers deploying the CO2 Bike Calculator API on various platforms.

## Local Development

### Quick Start

```bash
# Install dependencies
go mod download

# Run server
go run main.go providers.go

# Server runs on http://localhost:3000
```

### Development with Hot Reload

```bash
# Install air (hot reload tool)
go install github.com/cosmtrek/air@latest

# Run with hot reload
air
```

Or use the Makefile:
```bash
make dev
```

## Production Build

### Standard Build

```bash
make build
# Binary created at ./co2-calculator
```

### Optimized Build

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
  -ldflags "-s -w" \
  -o co2-calculator \
  main.go providers.go
```

This creates a smaller binary (~5MB).

## Docker Deployment

### Build Docker Image

```bash
docker build -t co2-calculator:latest .
```

### Run Container

```bash
docker run -p 3000:3000 co2-calculator:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - GIN_MODE=release
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s
```

Run with:
```bash
docker-compose up -d
```

## Linux Systemd Service

### Create Service File

Create `/etc/systemd/system/co2-calculator.service`:

```ini
[Unit]
Description=CO2 Bike Calculator API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/co2-calculator
ExecStart=/opt/co2-calculator/co2-calculator
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment
Environment="GIN_MODE=release"
Environment="PORT=3000"

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
# Copy binary to /opt/co2-calculator/
sudo mkdir -p /opt/co2-calculator
sudo cp co2-calculator /opt/co2-calculator/
sudo cp index.html /opt/co2-calculator/

# Set permissions
sudo chown -R www-data:www-data /opt/co2-calculator

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable co2-calculator
sudo systemctl start co2-calculator

# Check status
sudo systemctl status co2-calculator

# View logs
sudo journalctl -u co2-calculator -f
```

## Nginx Reverse Proxy

### Nginx Configuration

Create `/etc/nginx/sites-available/co2-calculator`:

```nginx
upstream co2_api {
    server localhost:3000;
}

server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://co2_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:
```bash
sudo ln -s /etc/nginx/sites-available/co2-calculator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## HTTPS with Let's Encrypt

### Install Certbot

```bash
sudo apt-get install certbot python3-certbot-nginx
```

### Generate Certificate

```bash
sudo certbot certonly --nginx -d yourdomain.com
```

### Update Nginx Config

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://co2_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Auto-Renew Certificate

```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Cloud Deployment

### Heroku

1. Create `Procfile`:
```
web: ./co2-calculator
```

2. Create `go.mod` and `go.sum` (already done)

3. Deploy:
```bash
heroku create co2-calculator
git push heroku main
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Create app from repository
3. Configure:
   - **Build Command**: `go build -o co2-calculator main.go providers.go`
   - **Run Command**: `./co2-calculator`
   - **HTTP Port**: 3000

### AWS EC2

1. Launch Ubuntu instance
2. Install Go:
```bash
wget https://go.dev/dl/go1.21.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

3. Clone repository and build:
```bash
git clone <your-repo>
cd hackheroes2025
make build
./co2-calculator
```

4. Use Systemd service (see Linux Systemd Service section)

### Google Cloud Run

1. Create `cloudbuild.yaml`:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/go'
    args: ['build', '-o', 'co2-calculator', 'main.go', 'providers.go']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/co2-calculator', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/co2-calculator']

images:
  - 'gcr.io/$PROJECT_ID/co2-calculator'
```

2. Deploy:
```bash
gcloud run deploy co2-calculator \
  --image gcr.io/PROJECT_ID/co2-calculator \
  --platform managed \
  --port 3000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | Server port |
| `GIN_MODE` | debug | `debug` or `release` |

## Performance Tuning

### Connection Pooling

The application automatically uses connection pooling via Resty client.

### Caching

Currently no caching is implemented (stateless design). For production, consider:

```go
// Add Redis caching (optional)
// Cache vehicle locations for 30 seconds
```

### Rate Limiting

For production, add rate limiting:

```bash
# Install rate limiting middleware
go get -u github.com/gin-contrib/cors
```

## Monitoring

### Health Check

```bash
curl http://localhost:3000/health
```

### Application Logs

With Systemd:
```bash
sudo journalctl -u co2-calculator -f
```

With Docker:
```bash
docker logs -f <container-id>
```

### Metrics

Consider adding Prometheus metrics:

```go
import "github.com/prometheus/client_golang/prometheus"

// Add metrics for request count, latency, etc.
```

## Backup & Disaster Recovery

Since this is stateless:
1. No database backup needed
2. Configuration stored in environment variables
3. Re-deploy from source code if needed

## Rollback

To rollback to previous version:

```bash
# If using Docker
docker run -p 3000:3000 co2-calculator:v1.0

# If using Systemd
git checkout <previous-version>
make build
sudo systemctl restart co2-calculator
```

## Security

### Firewall Rules

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow only from trusted IPs (optional)
sudo ufw allow from 203.0.113.0/24 to any port 3000
```

### CORS Configuration

Currently allows all origins. For production, restrict:

```go
// In main.go
router.Use(cors.New(cors.Config{
    AllowOrigins: []string{"https://yourdomain.com"},
    AllowMethods: []string{"GET", "POST"},
}))
```

### Rate Limiting

Add rate limiting middleware:

```go
import "github.com/gin-contrib/ratelimit"

router.Use(ratelimit.Limit(time.Second / 10)) // 10 req/sec
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 3000
lsof -i :3000

# Kill it
kill -9 <PID>

# Or use different port
PORT=8080 ./co2-calculator
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u co2-calculator -n 50

# Check permissions
ls -la /opt/co2-calculator/

# Verify binary
/opt/co2-calculator/co2-calculator --help
```

### High Memory Usage

1. Check for goroutine leaks
2. Verify providers aren't caching data
3. Monitor with: `ps aux | grep co2-calculator`

### Slow Responses

1. Check provider API latency
2. Increase timeout if needed
3. Reduce search radius
4. Filter slow providers

## Maintenance

### Update Dependencies

```bash
go get -u ./...
go mod tidy
make build
```

### Update Binary

```bash
git pull
make build
sudo systemctl restart co2-calculator
```

## Support

For issues:
1. Check logs: `journalctl -u co2-calculator -f`
2. Verify network: `curl http://localhost:3000/health`
3. Test provider APIs directly
4. Check Go version: `go version`
