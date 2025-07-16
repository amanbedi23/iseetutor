#!/bin/bash
# Direct kiosk startup without window manager

echo "Starting ISEE Tutor Direct Kiosk..."

# Ensure we're in the right directory
cd /home/tutor/iseetutor

# Check if API is already running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting API server..."
    python3 start_api.py &
    API_PID=$!
    
    # Wait for API
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "API ready!"
            break
        fi
        sleep 1
    done
else
    echo "API already running"
fi

# Check if frontend is already running
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Starting frontend..."
    cd frontend
    export BROWSER=none
    npm start &
    FRONTEND_PID=$!
    
    # Wait for frontend
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "Frontend ready!"
            break
        fi
        sleep 1
    done
    cd ..
else
    echo "Frontend already running"
fi

# Start X with chromium directly (no window manager needed for kiosk)
echo "Starting X server with browser..."
echo "Note: The display will switch to the kiosk. Press Ctrl+Alt+F2-F6 for other terminals."

# Use the native chromium-browser binary directly
xinit /usr/bin/chromium-browser \
    --kiosk \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu-sandbox \
    --disable-software-rasterizer \
    --no-first-run \
    --disable-features=TranslateUI \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --disable-features=OverscrollHistoryNavigation \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --check-for-update-interval=31536000 \
    --simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT' \
    http://localhost:3000 \
    -- :0 vt7 -nocursor