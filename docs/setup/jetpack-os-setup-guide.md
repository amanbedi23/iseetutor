# JetPack OS Installation Guide for Jetson Orin Nano

## Overview
This guide covers installing NVIDIA JetPack OS on your Jetson Orin Nano Developer Kit using your Mac.

## Prerequisites
- Mac computer with at least 40GB free space
- 256GB MicroSD card
- MicroSD card reader for Mac
- Stable internet connection
- Jetson Orin Nano Developer Kit

## Step 1: Download Required Software

### On your Mac:

1. **Download NVIDIA SDK Manager**
   - Visit: https://developer.nvidia.com/sdk-manager
   - Create NVIDIA Developer account (if needed)
   - Download SDK Manager for Mac
   - Note: If Mac version unavailable, use alternative method below

2. **Alternative: Download JetPack Image Directly**
   - Visit: https://developer.nvidia.com/embedded/jetpack
   - Download JetPack 5.1.2 or latest for Orin Nano
   - File will be ~7GB (e.g., `Jetson_Linux_R35.4.1_aarch64.tbz2`)

## Step 2: Prepare MicroSD Card (Using Balena Etcher)

### Install Balena Etcher:
```bash
# Using Homebrew
brew install --cask balenaetcher

# Or download from https://etcher.balena.io/
```

### Flash the Image:
1. Insert MicroSD card into Mac
2. Open Balena Etcher
3. Select the JetPack image file
4. Select the MicroSD card
5. Click "Flash!" and wait (~20-30 minutes)

## Step 3: Alternative Method - Using Command Line

### If using direct image:
```bash
# Identify MicroSD card
diskutil list
# Look for your 256GB disk (e.g., /dev/disk2)

# Unmount the disk
diskutil unmountDisk /dev/disk2

# Write image (replace disk2 with your disk)
sudo dd if=jetson-orin-nano-jp5.1.2.img of=/dev/rdisk2 bs=1m status=progress

# Eject when complete
diskutil eject /dev/disk2
```

## Step 4: First Boot Setup

1. **Insert MicroSD Card**
   - Power off Jetson
   - Insert flashed MicroSD card
   - Connect monitor, keyboard, mouse

2. **Power On**
   - Connect power adapter
   - Press power button
   - Wait for Ubuntu setup wizard (~2-3 minutes)

3. **Initial Configuration**
   - Language: English
   - Keyboard: Your preference
   - Timezone: Your location
   - Username: `nvidia` (recommended)
   - Password: Choose secure password
   - Computer name: `jetson-isee-tutor`

## Step 5: Post-Installation Setup

### Update System:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev build-essential
```

### Install JetPack Components:
```bash
# Install CUDA toolkit
sudo apt install nvidia-jetpack

# Verify installation
jetson_release
```

### Configure Performance:
```bash
# Set to max performance mode
sudo nvpmodel -m 0
sudo jetson_clocks
```

## Step 6: Essential Driver Setup

### WiFi Adapter (AX1800):
```bash
# Check if detected
lsusb
# Should show Realtek or similar device

# Install drivers if needed
sudo apt install linux-headers-$(uname -r)
git clone https://github.com/morrownr/8821au-20210708.git
cd 8821au-20210708
sudo ./install-driver.sh
```

### Audio Drivers:
```bash
# Install audio utilities
sudo apt install alsa-utils pulseaudio

# Test speaker
speaker-test -t sine -f 1000 -c 2

# Configure ReSpeaker USB Mic Array
# Should be detected automatically
arecord -l
```

### Touchscreen Setup:
```bash
# Install touch utilities
sudo apt install xinput-calibrator

# The 10.1" touchscreen should work out of box
# If calibration needed:
xinput_calibrator
```

## Step 7: Storage Configuration

### Mount NVMe SSD:
```bash
# Check if SSD is detected
lsblk
# Should show nvme0n1

# Create partition
sudo fdisk /dev/nvme0n1
# Press: n, p, 1, Enter, Enter, w

# Format partition
sudo mkfs.ext4 /dev/nvme0n1p1

# Create mount point
sudo mkdir /mnt/storage

# Mount permanently
echo "UUID=$(sudo blkid -s UUID -o value /dev/nvme0n1p1) /mnt/storage ext4 defaults 0 2" | sudo tee -a /etc/fstab
sudo mount -a

# Set permissions
sudo chown nvidia:nvidia /mnt/storage
```

## Step 8: Development Tools

### Install Essential Tools:
```bash
# Development tools
sudo apt install -y git cmake ninja-build
sudo apt install -y nodejs npm
sudo apt install -y htop iotop

# Python ML packages
pip3 install numpy scipy matplotlib
pip3 install jupyter notebook

# Install PyTorch for Jetson
# Visit: https://forums.developer.nvidia.com/t/pytorch-for-jetson
```

### Enable SSH:
```bash
sudo systemctl enable ssh
sudo systemctl start ssh

# Get IP address
ip addr show
```

## Step 9: Verify Installation

### Create test script:
```bash
nano ~/test_system.py
```

```python
#!/usr/bin/env python3
import subprocess
import os

def check_system():
    print("=== System Check ===")
    
    # Check Jetson stats
    print("\n1. Jetson Info:")
    os.system("jetson_release")
    
    # Check storage
    print("\n2. Storage:")
    os.system("df -h | grep -E 'nvme|mmcblk'")
    
    # Check GPU
    print("\n3. GPU Status:")
    os.system("nvidia-smi")
    
    # Check audio
    print("\n4. Audio Devices:")
    os.system("aplay -l")
    os.system("arecord -l")
    
    # Check network
    print("\n5. Network:")
    os.system("ip addr show | grep inet")

if __name__ == "__main__":
    check_system()
```

```bash
chmod +x ~/test_system.py
python3 ~/test_system.py
```

## Step 10: Backup Configuration

### Create system backup:
```bash
# Backup important configs
mkdir ~/jetson-backup
cp -r ~/.bashrc ~/.profile /etc/fstab ~/jetson-backup/

# Save package list
dpkg --get-selections > ~/jetson-backup/packages.list
```

## Troubleshooting

### Black Screen on Boot:
- Try different HDMI port
- Press Ctrl+Alt+F2 for console
- Check power supply (use official adapter)

### WiFi Not Working:
- Check `dmesg | grep -i wifi`
- May need specific driver for AX1800
- Use ethernet for initial setup

### Performance Issues:
- Check power mode: `sudo nvpmodel -q`
- Enable fan: `sudo jetson_clocks --fan`
- Monitor temps: `tegrastats`

### Storage Not Detected:
- Check connections
- Try `sudo nvme list`
- May need BIOS/UEFI update

## Next Steps
1. Connect via VS Code (see remote dev guide)
2. Set up project structure
3. Test hardware components
4. Begin development!

## Useful Commands
```bash
# Monitor system
tegrastats

# Check Jetson info
jetson_release -v

# Power modes
sudo nvpmodel -q  # Query current mode
sudo nvpmodel -m 0  # Max performance

# Temperature monitoring
cat /sys/devices/virtual/thermal/thermal_zone*/temp
```