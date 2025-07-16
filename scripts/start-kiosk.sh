#!/bin/bash

# Wait for network (important for API)
sleep 5

# Disable screen blanking and power management
export DISPLAY=:0
xset -dpms
xset s off
xset s noblank

# Hide cursor after 1 second of inactivity
unclutter -idle 1 -root &

# Start the API server
cd /home/tutor/iseetutor
python3 start_api.py &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
done
echo "API server ready!"

# Determine which browser to use
# Prefer native packages over snaps
if command -v firefox-esr >/dev/null 2>&1; then
    BROWSER="firefox-esr"
elif command -v chromium-browser >/dev/null 2>&1 && [ ! -L /usr/bin/chromium-browser ]; then
    BROWSER="chromium-browser"
elif command -v google-chrome >/dev/null 2>&1; then
    BROWSER="google-chrome"
elif command -v firefox >/dev/null 2>&1; then
    BROWSER="firefox"
elif command -v chromium >/dev/null 2>&1; then
    BROWSER="chromium"
    CHROMIUM_FLAGS="--no-sandbox"
else
    echo "No supported browser found. Please install firefox-esr or chromium-browser."
    exit 1
fi

echo "Selected browser: $BROWSER"

# Start browser in kiosk mode
while true; do
    if [[ "$BROWSER" == "firefox" ]] || [[ "$BROWSER" == "firefox-esr" ]]; then
        # Firefox kiosk mode
        $BROWSER --kiosk http://localhost:8000 &
    else
        # Chromium kiosk mode
        $BROWSER \
            ${CHROMIUM_FLAGS:-} \
            --kiosk \
            --no-first-run \
            --disable-infobars \
            --disable-session-crashed-bubble \
            --disable-features=TranslateUI \
            --disable-pinch \
            --overscroll-history-navigation=0 \
            --disable-features=OverscrollHistoryNavigation \
            --check-for-update-interval=31536000 \
            --simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT' \
            --app=http://localhost:8000 &
    fi
    
    # Wait for browser process
    wait $!
    
    # If browser crashes, wait a moment and restart
    echo "Browser exited, restarting..."
    sleep 2
done