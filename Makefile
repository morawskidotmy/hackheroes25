.PHONY: help build run dev clean test docker

help:
	@echo "CO2 Bike Calculator - Go Version"
	@echo ""
	@echo "Available targets:"
	@echo "  make build     - Build the application"
	@echo "  make run       - Build and run the application"
	@echo "  make dev       - Run in development mode with hot reload"
	@echo "  make clean     - Remove build artifacts"
	@echo "  make test      - Run tests"
	@echo "  make docker    - Build Docker image"
	@echo "  make install   - Download dependencies"
	@echo ""

install:
	@echo "Installing dependencies..."
	go mod download
	go mod tidy

build: install
	@echo "Building application..."
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o co2-calculator main.go providers.go
	@echo "Build complete: ./co2-calculator"

run: build
	@echo "Starting server on http://localhost:3000"
	./co2-calculator

dev: install
	@echo "Starting in development mode..."
	@which air > /dev/null || (echo "Installing air for hot reload..." && go install github.com/cosmtrek/air@latest)
	GIN_MODE=debug air

clean:
	@echo "Cleaning up..."
	rm -f co2-calculator
	rm -rf dist/

test:
	@echo "Running tests..."
	go test -v ./...

docker:
	@echo "Building Docker image..."
	docker build -t co2-calculator:latest .
	@echo "Run with: docker run -p 3000:3000 co2-calculator:latest"

docker-run: docker
	docker run -p 3000:3000 co2-calculator:latest

lint:
	@echo "Running linter..."
	@which golangci-lint > /dev/null || (echo "Installing golangci-lint..." && go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest)
	golangci-lint run

fmt:
	@echo "Formatting code..."
	go fmt ./...

deps:
	@echo "Dependencies:"
	go list -m all

update-deps:
	@echo "Updating dependencies..."
	go get -u ./...
	go mod tidy

.PHONY: help build run dev clean test docker docker-run lint fmt deps update-deps install
