# Headless Setup Guide for Jetson Orin Nano

## Overview
This guide helps you set up your Jetson Orin Nano without a display (headless mode) and connect to it from your Mac.

## Method 1: USB Device Mode (Recommended for Initial Setup)

### Steps:
1. **Flash the MicroSD Card**
   - Follow the JetPack OS guide to flash the SD card on your Mac
   - Insert the flashed SD card into the Jetson

2. **Connect via USB-C**
   - Use a USB-C cable to connect your Mac to the Jetson's USB-C port
   - Connect the power adapter to the Jetson
   - Power on the Jetson (press power button)

3. **Wait for Boot**
   - Wait ~2-3 minutes for first boot
   - The Jetson will appear as a network device on your Mac

4. **Connect via USB Network**
   ```bash
   # On your Mac, the Jetson typically appears at 192.168.55.1
   ssh nvidia@192.168.55.1
   # Default password is 'nvidia'
   ```

5. **Complete Initial Setup via SSH**
   ```bash
   # Set hostname
   sudo hostnamectl set-hostname jetson-isee-tutor
   
   # Update system
   sudo apt update
   sudo apt upgrade -y
   
   # Set up WiFi (so you can disconnect USB later)
   sudo nmcli device wifi connect "YOUR_WIFI_SSID" password "YOUR_WIFI_PASSWORD"
   
   # Get the WiFi IP address
   ip addr show wlan0
   ```

## Method 2: Ethernet Connection

### If USB Device Mode doesn't work:
1. **Connect Ethernet**
   - Connect Jetson to your router via Ethernet cable
   - Power on the Jetson

2. **Find Jetson's IP**
   ```bash
   # On your Mac, scan network
   # Install nmap if needed: brew install nmap
   sudo nmap -sn 192.168.1.0/24
   # Look for "NVIDIA" in the results
   
   # Or check router's DHCP client list
   ```

3. **SSH to Jetson**
   ```bash
   ssh nvidia@<JETSON_IP>
   ```

## Initial Configuration Steps

### 1. Create User Account (if needed)
```bash
# If system prompts for initial setup
sudo adduser nvidia
sudo usermod -aG sudo nvidia
```

### 2. Enable SSH (if not enabled)
```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 3. Set Up WiFi Adapter
```bash
# Plug in your AX1800 WiFi adapter
# Check if detected
lsusb | grep -i wireless

# Install NetworkManager TUI for easier setup
sudo apt install network-manager
sudo nmtui
# Use arrow keys to configure WiFi
```

### 4. Configure Performance Mode
```bash
# Set to max performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 5. Mount NVMe SSD
```bash
# Check if SSD is detected
lsblk

# If nvme0n1 appears, partition and format
sudo fdisk /dev/nvme0n1
# Press: n, p, 1, Enter, Enter, w

# Format
sudo mkfs.ext4 /dev/nvme0n1p1

# Mount
sudo mkdir -p /mnt/storage
sudo mount /dev/nvme0n1p1 /mnt/storage
sudo chown nvidia:nvidia /mnt/storage

# Make permanent
echo "UUID=$(sudo blkid -s UUID -o value /dev/nvme0n1p1) /mnt/storage ext4 defaults 0 2" | sudo tee -a /etc/fstab
```

## Test Hardware Components

### 1. Test USB Speaker
```bash
# Install audio tools
sudo apt install alsa-utils pulseaudio

# List audio devices
aplay -l

# Test speaker (you should hear a tone)
speaker-test -t sine -f 1000 -c 2 -D plughw:1,0
```

### 2. Test ReSpeaker Mic Array
```bash
# List recording devices
arecord -l

# Record a test (speak for 5 seconds)
arecord -d 5 -f cd -D plughw:2,0 test.wav

# Play it back
aplay test.wav
```

### 3. Test RGB LED Ring (Basic GPIO)
```bash
# Install GPIO library
sudo apt install python3-pip
pip3 install Jetson.GPIO

# Create test script
cat > ~/test_led.py << 'EOF'
import Jetson.GPIO as GPIO
import time

# Pin 32 = GPIO 124
LED_PIN = 32

GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

# Blink test
for i in range(5):
    GPIO.output(LED_PIN, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(LED_PIN, GPIO.LOW)
    time.sleep(0.5)

GPIO.cleanup()
print("LED test complete")
EOF

# Run test
python3 ~/test_led.py
```

### 4. Test Push Button
```bash
# Create button test script
cat > ~/test_button.py << 'EOF'
import Jetson.GPIO as GPIO
import time

# Pin 18 = GPIO 24
BUTTON_PIN = 18

GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Press the button (Ctrl+C to exit)...")
try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Button pressed!")
            time.sleep(0.3)  # Debounce
except KeyboardInterrupt:
    GPIO.cleanup()
EOF

# Run test
python3 ~/test_button.py
```

## Remote Development Setup

### 1. Note the WiFi IP
```bash
# Get your Jetson's WiFi IP
ip addr show wlan0 | grep inet
# Note the IP address (e.g., 192.168.1.100)
```

### 2. Update SSH Config on Mac
```bash
# On your Mac
nano ~/.ssh/config
```
Add:
```
Host jetson
    HostName 192.168.1.100  # Use your Jetson's IP
    User nvidia
    Port 22
```

### 3. Test Connection
```bash
# Disconnect USB cable
# Connect via WiFi
ssh jetson
```

## Next Steps Without Display

You can now:
1. Set up VS Code remote development (follow the VS Code guide)
2. Install development tools and libraries
3. Test all USB peripherals
4. Begin developing the backend services
5. Create web-based UI for testing (accessible from Mac browser)

## When Display Arrives

When your DP-to-HDMI adapter arrives:
1. Connect display and boot normally
2. Run `startx` if needed to start GUI
3. Configure display settings
4. Test touchscreen functionality

## Troubleshooting

### Can't connect via USB Device Mode:
- Make sure using USB-C port (not USB-A)
- Try different USB cable
- May need to wait longer for first boot

### WiFi adapter not working:
- Check `dmesg | tail -20` after plugging in
- May need specific drivers
- Use ethernet as backup

### SSH connection refused:
- Ensure Jetson is fully booted (wait 3-5 min)
- Check if SSH is enabled
- Verify correct IP address