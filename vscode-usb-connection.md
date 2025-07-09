# VS Code USB-C Connection to Jetson Orin Nano

## Quick Setup

### 1. Test USB Network Connection
On your Mac terminal:
```bash
# The Jetson typically appears at this IP over USB
ping 192.168.55.1

# If that works, try SSH
ssh nvidia@192.168.55.1
# Default password is usually 'nvidia'
```

### 2. Add to SSH Config (Optional but recommended)
```bash
# Edit SSH config on Mac
nano ~/.ssh/config
```

Add:
```
Host jetson-usb
    HostName 192.168.55.1
    User nvidia
    Port 22
```

### 3. Connect VS Code

1. **Open VS Code on your Mac**

2. **Press `Cmd+Shift+P`** to open command palette

3. **Type and select**: "Remote-SSH: Connect to Host..."

4. **Choose one of**:
   - Type: `nvidia@192.168.55.1`
   - Or if you added SSH config: `jetson-usb`

5. **Select "Linux"** when asked about platform

6. **Enter password** when prompted (default: nvidia)

### 4. First Time Setup
VS Code will automatically:
- Install VS Code Server on Jetson
- Set up the connection
- Open a new window connected to Jetson

### 5. Open Your Project
Once connected:
1. Click "Open Folder" in VS Code
2. Navigate to `/home/nvidia/`
3. Create new folder `isee-tutor` or open existing

## Troubleshooting

### Can't ping 192.168.55.1
1. Check USB-C cable is connected to the USB-C port (not USB-A)
2. Wait 30-60 seconds after Jetson boots
3. Try: `arp -a | grep 192.168.55`

### SSH Connection Refused
```bash
# On Mac, check if you can see the network interface
ifconfig | grep 192.168.55

# Try the alternate IP
ssh nvidia@192.168.55.100
```

### Alternative IPs to try:
- 192.168.55.1 (most common)
- 192.168.55.100
- 10.42.0.1
- 192.168.0.100

### Find the Correct IP
On your Mac:
```bash
# List all network interfaces
ifconfig -a

# Look for a new interface when Jetson is connected
# It might be named like 'en5' or 'en6' with IP in 192.168.55.x range
```

## Quick Test After Connection

Once VS Code is connected:

1. **Open integrated terminal** (`` Ctrl+` ``)

2. **Test you're on Jetson**:
   ```bash
   hostname
   # Should show your Jetson hostname
   
   jetson_release
   # Should show Jetson info
   ```

3. **Create project**:
   ```bash
   mkdir -p ~/isee-tutor
   cd ~/isee-tutor
   ```

You're now ready to develop directly on the Jetson from your Mac!