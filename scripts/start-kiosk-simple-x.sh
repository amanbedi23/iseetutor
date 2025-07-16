#!/bin/bash
# Simple X kiosk startup

echo "Starting ISEE Tutor Simple Kiosk..."

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

# Give services a moment
sleep 2

# Create simple X session script
cat > /tmp/start-browser.sh << 'EOF'
#!/bin/bash

# Wait for X to be ready
sleep 2

# Set display
export DISPLAY=:0

# Disable screen blanking
xset s off -dpms

# Try different browsers in order of preference
if command -v firefox >/dev/null 2>&1; then
    # Firefox (if installed as deb, not snap)
    firefox --kiosk http://localhost:3000
elif [ -f /usr/lib/chromium-browser/chromium-browser ]; then
    # Chromium actual binary
    /usr/lib/chromium-browser/chromium-browser --kiosk --no-sandbox http://localhost:3000
elif command -v epiphany-browser >/dev/null 2>&1; then
    # Epiphany without application mode
    epiphany-browser --new-window http://localhost:3000 &
    sleep 3
    # Try to make it fullscreen with xdotool if available
    if command -v xdotool >/dev/null 2>&1; then
        xdotool search --name "localhost" windowactivate key F11
    fi
    wait
elif command -v surf >/dev/null 2>&1; then
    # Surf - minimal webkit browser
    surf -F http://localhost:3000
else
    echo "No suitable browser found!"
    echo "Install one of: firefox (deb), epiphany-browser, surf"
    sleep 10
fi
EOF

chmod +x /tmp/start-browser.sh

echo "Starting X server..."
echo "Press Ctrl+Alt+F2-F6 to switch terminals, Ctrl+Alt+Backspace to exit"

# Start X and run browser
xinit /tmp/start-browser.sh -- :0 vt7

# Cleanup
rm -f /tmp/start-browser.sh