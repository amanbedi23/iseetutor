#!/bin/bash
# Install Epiphany browser for kiosk mode

echo "Installing Epiphany (GNOME Web) browser..."
echo "This is a lightweight browser perfect for kiosk mode"
echo

# Install epiphany and dependencies
echo "Installing (will require sudo password)..."
sudo apt update
sudo apt install -y epiphany-browser xserver-xorg xinit x11-xserver-utils

echo
echo "Epiphany browser installed!"
echo "You can now run the kiosk with Epiphany."