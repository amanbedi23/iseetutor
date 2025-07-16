#!/bin/bash
# Start display with Epiphany (no special modes)

echo "Starting ISEE Tutor with display..."

cd /home/tutor/iseetutor

# Ensure services are running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting API..."
    python3 start_api.py &
    sleep 5
fi

if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Starting frontend..."
    cd frontend
    export BROWSER=none
    npm start &
    cd ..
    
    echo "Waiting for frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
fi

echo "Services ready. Starting display..."

# Simple xinit with just epiphany
xinit -- :0 vt7 &
XINIT_PID=$!

sleep 3

# Start epiphany on the display
DISPLAY=:0 epiphany-browser http://localhost:3000 &

echo
echo "Display started!"
echo "Press Ctrl+C to stop"

wait