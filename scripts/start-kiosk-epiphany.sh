#!/bin/bash
# Start ISEE Tutor kiosk with Epiphany browser

echo "Starting ISEE Tutor Kiosk with Epiphany..."

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

# Give services a moment to stabilize
sleep 2

# Start X with Epiphany in kiosk mode
echo "Starting display with Epiphany browser..."
echo "Note: Press Ctrl+Alt+F2-F6 to switch to other terminals"

# Create profile directory
mkdir -p /tmp/epiphany-kiosk

# Create a wrapper script for Epiphany kiosk mode
cat > /tmp/epiphany-kiosk.sh << 'EOF'
#!/bin/bash
# Hide cursor
xsetroot -cursor_name none &

# Disable screen saver and DPMS
xset s off
xset -dpms
xset s noblank

# Create profile directory if it doesn't exist
mkdir -p /tmp/epiphany-kiosk

# Start Epiphany in application mode (kiosk-like)
exec epiphany-browser \
    --application-mode \
    --profile=/tmp/epiphany-kiosk \
    http://localhost:3000
EOF

chmod +x /tmp/epiphany-kiosk.sh

# Start X with our kiosk script
xinit /tmp/epiphany-kiosk.sh -- :0 vt7 -nocursor

# Cleanup
rm -f /tmp/epiphany-kiosk.sh
rm -rf /tmp/epiphany-kiosk