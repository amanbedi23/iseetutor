#!/bin/bash
# Working kiosk script that avoids snap issues

echo "Starting ISEE Tutor Kiosk (Working Version)..."

# Function to find a working browser
find_browser() {
    # Check for non-snap chromium
    if [ -f /usr/lib/chromium-browser/chromium-browser ]; then
        echo "/usr/lib/chromium-browser/chromium-browser"
        return
    fi
    
    # Check for google-chrome
    if command -v google-chrome-stable >/dev/null 2>&1; then
        echo "google-chrome-stable"
        return
    fi
    
    # Default to chromium-browser and hope it works
    echo "/usr/bin/chromium-browser"
}

# Ensure we're in the right directory
cd /home/tutor/iseetutor

# Start API if needed
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Starting API server..."
    python3 start_api.py &
    API_PID=$!
    sleep 5
fi

# Start frontend if needed
if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Starting frontend..."
    cd frontend
    export BROWSER=none
    npm start &
    FRONTEND_PID=$!
    
    # Wait for frontend
    echo "Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "Frontend ready!"
            break
        fi
        sleep 1
    done
    cd ..
fi

# Find browser
BROWSER_BIN=$(find_browser)
echo "Using browser: $BROWSER_BIN"

# Method 1: Try with xinit first
echo "Attempting to start kiosk with xinit..."
xinit $BROWSER_BIN \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu-sandbox \
    --disable-software-rasterizer \
    --no-first-run \
    --kiosk \
    --app=http://localhost:3000 \
    -- :0 vt7 -nocursor 2>/dev/null

# If xinit fails, try startx
if [ $? -ne 0 ]; then
    echo "xinit failed, trying startx..."
    
    # Create minimal xinitrc
    cat > /tmp/.xinitrc << EOF
#!/bin/bash
exec $BROWSER_BIN \
    --no-sandbox \
    --disable-setuid-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu-sandbox \
    --disable-software-rasterizer \
    --no-first-run \
    --kiosk \
    --app=http://localhost:3000
EOF
    
    chmod +x /tmp/.xinitrc
    HOME=/tmp startx -- :0 vt7
fi