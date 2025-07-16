#!/bin/bash
# Install surf - a simple webkit-based browser perfect for kiosk

echo "Installing surf browser for kiosk mode..."
echo "Surf is a minimal browser designed for kiosk/embedded use"
echo

sudo apt update
sudo apt install -y surf xdotool

echo
echo "Surf browser installed!"
echo "Run: ./scripts/start-kiosk-simple-x.sh"