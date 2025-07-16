#!/bin/bash

# Quick Setup Script for Jetson Orin NX 16GB
# Run this after basic OS installation

set -e

echo "=== Jetson Orin NX 16GB Setup for ISEE Tutor ==="
echo ""

# Check if running as regular user (not root)
if [ "$EUID" -eq 0 ]; then 
    echo "Please run as regular user (jetson), not root"
    echo "The script will use sudo when needed"
    exit 1
fi

# Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "2. Installing essential packages..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    git \
    curl \
    wget \
    htop \
    nvtop \
    build-essential \
    cmake

# Install audio packages
echo "3. Installing audio packages..."
sudo apt install -y \
    portaudio19-dev \
    libsndfile1 \
    ffmpeg \
    sox \
    alsa-utils \
    pulseaudio

# Configure PostgreSQL
echo "4. Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create swap file (helpful even with 16GB)
echo "5. Creating swap file..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 8G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Set Jetson to max performance
echo "6. Setting Jetson to maximum performance..."
sudo nvpmodel -m 0
sudo jetson_clocks

# Create directory structure
echo "7. Creating directory structure..."
mkdir -p ~/iseetutor
mkdir -p /mnt/storage
sudo chown $USER:$USER /mnt/storage

# Install Docker (optional but useful)
echo "8. Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Python packages for Jetson
echo "9. Installing Python packages..."
pip3 install --upgrade pip
pip3 install wheel setuptools

# Jetson-specific Python packages
pip3 install \
    jetson-stats \
    Jetson.GPIO \
    pyserial

# Create helpful aliases
echo "10. Adding helpful aliases..."
cat >> ~/.bashrc << 'EOF'

# ISEE Tutor aliases
alias isee='cd ~/iseetutor'
alias isee-start='cd ~/iseetutor && python3 start_api.py'
alias isee-test='cd ~/iseetutor && python3 verify_setup.py'
alias isee-logs='cd ~/iseetutor && tail -f logs/*.log'

# Jetson monitoring
alias gpu-watch='watch -n 1 nvidia-smi'
alias temp-watch='watch -n 1 "cat /sys/devices/virtual/thermal/thermal_zone*/temp"'

# System
alias ll='ls -la'
alias storage='cd /mnt/storage'
EOF

# Enable SPI for LED control
echo "11. Enabling SPI for WS2812B LEDs..."
sudo modprobe spidev
echo 'spidev' | sudo tee -a /etc/modules

# Audio setup
echo "12. Configuring audio..."
# Add user to audio group
sudo usermod -a -G audio $USER

# Create ISEE Tutor systemd service
echo "13. Creating systemd service..."
sudo tee /etc/systemd/system/iseetutor.service << EOF
[Unit]
Description=ISEE Tutor API Server
After=network.target postgresql.service redis-server.service

[Service]
Type=exec
User=$USER
WorkingDirectory=/home/$USER/iseetutor
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/$USER/iseetutor/start_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Performance tuning
echo "14. Applying performance tuning..."
# Increase file descriptors
echo "$USER soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "$USER hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Network tuning for WebSocket
sudo tee -a /etc/sysctl.conf << EOF
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
EOF
sudo sysctl -p

# Summary
echo ""
echo "=== Setup Complete ==="
echo ""
echo "System configured for ISEE Tutor on Jetson Orin NX 16GB!"
echo ""
echo "Next steps:"
echo "1. Log out and back in (for docker group)"
echo "2. Transfer your backup files"
echo "3. Run restore_from_backup.sh"
echo "4. Mount your NVMe SSD with models"
echo ""
echo "Useful commands:"
echo "  jetson_clocks --show    # Check performance mode"
echo "  sudo jtop               # Monitor Jetson resources"
echo "  isee-start              # Start ISEE Tutor"
echo ""
echo "Your 16GB RAM advantages:"
echo "  - Run larger models (13B parameter LLMs)"
echo "  - Development + production simultaneously"
echo "  - More aggressive caching"
echo "  - Multiple model inference"