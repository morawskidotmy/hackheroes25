#!/bin/bash

# CO2 Bike Calculator - Setup Script
# This script sets up and runs the application

set -e

echo "================================"
echo "CO2 Bike Calculator Setup"
echo "================================"
echo ""

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed."
    echo ""
    echo "Install Go 1.21+ from: https://golang.org/dl/"
    echo ""
    echo "Quick install for Linux:"
    echo "  wget https://go.dev/dl/go1.25.3.linux-amd64.tar.gz"
    echo "  sudo tar -C /usr/local -xzf go1.25.3.linux-amd64.tar.gz"
    echo "  export PATH=\$PATH:/usr/local/go/bin"
    echo ""
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}')
echo "✅ Go version: $GO_VERSION"
echo ""

# Check if we're in the right directory
if [ ! -f "go.mod" ]; then
    echo "❌ go.mod not found. Please run this script from the project root."
    exit 1
fi

echo "📦 Downloading dependencies..."
go mod download
go mod tidy
echo "✅ Dependencies downloaded"
echo ""

echo "🔨 Building application..."
go build -o co2-calculator main.go providers.go
echo "✅ Build complete: ./co2-calculator"
echo ""

# Check if binary was created
if [ ! -f "co2-calculator" ]; then
    echo "❌ Build failed. Binary not found."
    exit 1
fi

echo "📋 Application ready!"
echo ""
echo "To start the server, run:"
echo "  ./co2-calculator"
echo ""
echo "Or use make:"
echo "  make run"
echo ""
echo "Server will be available at: http://localhost:3000"
echo ""

# Ask if user wants to start now
read -p "Start server now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting server..."
    echo ""
    export GIN_MODE=release
    ./co2-calculator
fi
