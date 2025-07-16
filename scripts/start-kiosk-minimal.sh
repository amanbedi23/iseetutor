#!/bin/bash
# Minimal kiosk startup - starts X and browser only

echo "Starting ISEE Tutor Minimal Kiosk..."

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

# Create a simple X session file
cat > /tmp/kiosk-session.sh << 'EOF'
#!/bin/bash
# Disable screen blanking
xset -dpms
xset s off
xset s noblank

# Hide cursor after 1 second
unclutter -idle 1 -root &

# Start window manager (minimal)
openbox &

# Give WM time to start
sleep 2

# Start browser in kiosk mode
exec /usr/bin/chromium-browser \
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
    --check-for-update-interval=31536000 \
    http://localhost:3000
EOF

chmod +x /tmp/kiosk-session.sh

# Start X with our session
echo "Starting X server with kiosk session..."
echo "Note: The display will switch to the kiosk. Press Ctrl+Alt+F2-F6 for other terminals."
startx /tmp/kiosk-session.sh -- :0 vt7

# Cleanup
rm -f /tmp/kiosk-session.sh