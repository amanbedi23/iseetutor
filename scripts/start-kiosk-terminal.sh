#!/bin/bash
# Start ISEE Tutor in kiosk mode from terminal (no desktop required)

echo "Starting ISEE Tutor Kiosk Mode from Terminal..."

# Kill any existing X servers
sudo pkill -9 Xorg 2>/dev/null
sleep 2

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

# Start frontend
echo "Starting frontend server..."
cd /home/tutor/iseetutor/frontend
export BROWSER=none
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

# Start X server and browser in kiosk mode
echo "Starting display server and browser..."

# Method 1: Using xinit (recommended)
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
    --check-for-update-interval=31536000 \
    --app=http://localhost:3000 \
    -- :0 vt1 &

XINIT_PID=$!

echo
echo "Kiosk mode started!"
echo "Services running:"
echo "  API PID: $API_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo "  Display PID: $XINIT_PID"
echo
echo "Press Ctrl+Alt+F1 to see the kiosk"
echo "Press Ctrl+Alt+F2-F6 to switch to other terminals"
echo "Press Ctrl+C here to stop all services"

# Cleanup function
cleanup() {
    echo "Stopping services..."
    sudo kill $XINIT_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    sudo pkill -9 Xorg 2>/dev/null
    exit
}

trap cleanup INT TERM

# Keep script running
wait