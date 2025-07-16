#!/bin/bash
# Simple browser startup that works without kiosk mode

echo "Starting ISEE Tutor in browser..."

# Ensure we're in the right directory
cd /home/tutor/iseetutor

# Start API if needed
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting API server..."
    python3 start_api.py &
    API_PID=$!
    
    echo "Waiting for API..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "API ready!"
            break
        fi
        sleep 1
    done
fi

# Start frontend if needed
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Starting frontend..."
    cd frontend
    export BROWSER=none
    npm start &
    FRONTEND_PID=$!
    
    echo "Waiting for frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "Frontend ready!"
            break
        fi
        sleep 1
    done
    cd ..
fi

echo
echo "Services are running!"
echo "Open a browser and navigate to: http://localhost:3000"
echo
echo "Since we're in terminal mode, you have a few options:"
echo "1. Install Google Chrome: ./scripts/install-chrome.sh"
echo "2. Access from another device: http://$(hostname -I | awk '{print $1}'):3000"
echo "3. Switch to GUI mode: sudo systemctl set-default graphical.target && sudo reboot"
echo
echo "Press Ctrl+C to stop the services"

# Keep running
while true; do
    sleep 1
done