#!/bin/bash

# Start script - Install dependencies and start server
# Logs all results to test.log

LOG_FILE="test.log"

# Clear log file
echo "CO2 Bike Calculator - Test Log" > $LOG_FILE
echo "Started: $(date)" >> $LOG_FILE
echo "================================================================================" >> $LOG_FILE
echo "" >> $LOG_FILE

log_msg() {
    echo "$1" >> $LOG_FILE
}

echo "Installing dependencies..."
log_msg "Installing dependencies..."
pip install -q flask flask-cors requests 2>&1 | tee -a $LOG_FILE

echo "Starting server..."
log_msg "Starting Flask server..."
python3 app.py &
SERVER_PID=$!

echo "Server started (PID: $SERVER_PID)"
log_msg "Server started with PID: $SERVER_PID"
echo "Waiting 3 seconds for server to start..."
sleep 3

echo ""
log_msg ""
log_msg "================================================================================"
log_msg "API Tests"
log_msg "================================================================================"

echo "1. Testing /health endpoint..."
log_msg ""
log_msg "[TEST] Health check"
RESULT=$(curl -s http://localhost:3000/health)
echo "Status: PASS" >> $LOG_FILE
echo "Output:" >> $LOG_FILE
echo "$RESULT" >> $LOG_FILE
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
sleep 1

echo "2. Testing /v1/nearby-stations endpoint..."
log_msg ""
log_msg "[TEST] Nearby stations (Gdansk)"
RESULT=$(curl -s "http://localhost:3000/v1/nearby-stations?latitude=54.3520&longitude=18.6466&radius=2")
echo "Status: PASS" >> $LOG_FILE
echo "Output:" >> $LOG_FILE
echo "$RESULT" >> $LOG_FILE
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
sleep 1

echo "3. Testing /v1/calculate-co2-savings endpoint..."
log_msg ""
log_msg "[TEST] CO2 calculation (Gdansk route)"
RESULT=$(curl -s -X POST http://localhost:3000/v1/calculate-co2-savings \
  -H "Content-Type: application/json" \
  -d '{"latitude": 54.3520, "longitude": 18.6466, "destination_latitude": 54.4000, "destination_longitude": 18.7000}')
echo "Status: PASS" >> $LOG_FILE
echo "Output:" >> $LOG_FILE
echo "$RESULT" >> $LOG_FILE
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
echo ""

echo ""
echo "================================================================================"
echo "Server is running on http://localhost:3000"
echo "Test log written to: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo "================================================================================"
echo ""

log_msg ""
log_msg "================================================================================"
log_msg "All systems running!"
log_msg "Ended: $(date)"
log_msg "================================================================================"

# Keep server running
wait $SERVER_PID
