#!/bin/bash
# Install dependencies for kiosk mode

echo "Installing kiosk mode dependencies..."
echo "This will install minimal X server components"
echo

# Update package list
sudo apt update

# Install minimal X server and utilities
sudo apt install -y \
    xinit \
    xserver-xorg \
    x11-xserver-utils \
    openbox \
    unclutter \
    chromium-browser \
    --no-install-recommends

echo
echo "Dependencies installed!"
echo "You can now run:"
echo "  ./scripts/start-kiosk-minimal.sh"