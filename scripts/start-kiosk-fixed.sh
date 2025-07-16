#!/bin/bash

# Start ISEE Tutor in kiosk mode (fixed for Jetson)

echo "Starting ISEE Tutor Kiosk Mode..."

# Check if display is available
if [ -z "$DISPLAY" ]; then
    echo "No display set. Trying to detect..."
    # Try common display values
    for disp in :0 :1 :0.0; do
        if xset -display $disp q &>/dev/null; then
            export DISPLAY=$disp
            echo "Found display: $DISPLAY"
            break
        fi
    done
fi

if [ -z "$DISPLAY" ]; then
    echo "Warning: No X display found. Running in headless mode."
    HEADLESS=true
else
    echo "Using display: $DISPLAY"
    # Disable screen blanking if display exists
    xset -dpms 2>/dev/null || true
    xset s off 2>/dev/null || true
    xset s noblank 2>/dev/null || true
fi

# Start the API server
cd /home/tutor/iseetutor
echo "Starting API server..."
python3 start_api.py &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "API server ready!"
        break
    fi
    sleep 1
done

# Start frontend in development mode (more stable than kiosk for now)
echo "Starting frontend server..."
cd /home/tutor/iseetutor/frontend
export BROWSER=none  # Don't auto-open browser
npm start &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo "Waiting for frontend..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "Frontend ready!"
        break
    fi
    sleep 1
done

# If not headless, try to open browser
if [ "$HEADLESS" != "true" ]; then
    sleep 3
    
    # Use native chromium-browser (not snap)
    if [ -x /usr/bin/chromium-browser ]; then
        echo "Opening Chromium browser..."
        /usr/bin/chromium-browser \
            --no-sandbox \
            --disable-dev-shm-usage \
            --disable-gpu-sandbox \
            --disable-software-rasterizer \
            --no-first-run \
            --disable-features=TranslateUI \
            --app=http://localhost:3000 &
        BROWSER_PID=$!
    elif [ -x /usr/bin/firefox ]; then
        echo "Opening Firefox..."
        /usr/bin/firefox http://localhost:3000 &
        BROWSER_PID=$!
    else
        echo "No suitable browser found"
    fi
else
    echo "Running in headless mode - access via:"
fi

echo
echo "Services running:"
echo "  API: http://localhost:8000 (PID: $API_PID)"
echo "  Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
if [ -n "$BROWSER_PID" ]; then
    echo "  Browser PID: $BROWSER_PID"
fi
echo
echo "Remote access:"
echo "  http://$(hostname -I | awk '{print $1}'):3000"
echo
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "Stopping services..."
    [ -n "$BROWSER_PID" ] && kill $BROWSER_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    exit
}

trap cleanup INT TERM

# Keep script running
wait