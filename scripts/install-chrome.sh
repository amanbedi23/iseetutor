#!/bin/bash
# Install Google Chrome (non-snap) for kiosk mode

echo "Installing Google Chrome for kiosk mode..."
echo "This will download and install the official Chrome .deb package"
echo

# Download Chrome
wget -q -O /tmp/google-chrome-stable_current_arm64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_arm64.deb

# Install Chrome
echo "Installing Chrome (will require sudo password)..."
sudo dpkg -i /tmp/google-chrome-stable_current_arm64.deb

# Fix any dependency issues
sudo apt-get install -f -y

# Clean up
rm /tmp/google-chrome-stable_current_arm64.deb

echo
echo "Google Chrome installed!"
echo "You can now run the kiosk scripts."