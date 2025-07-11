# Finding Jetson USB Network Connection

## Method 1: Check Network Interfaces on Mac

On your Mac, run these commands:

```bash
# Before connecting Jetson
ifconfig -a > before.txt

# Connect Jetson via USB-C, wait 30 seconds

# After connecting
ifconfig -a > after.txt

# See what changed
diff before.txt after.txt
```

## Method 2: Look for New Network Interface

```bash
# List all interfaces
ifconfig -a | grep -A 4 "en[0-9]:"

# Look for interfaces with IPs like:
# - 192.168.55.x
# - 10.42.0.x
# - 169.254.x.x
```

## Method 3: Check System Profiler

```bash
# See USB devices
system_profiler SPUSBDataType | grep -A 10 -i "nvidia\|jetson"
```

## Method 4: Network Scanner

```bash
# If you have nmap installed
nmap -sn 192.168.55.0/24
nmap -sn 10.42.0.0/24

# Or use arp
arp -a | grep -E "(192.168.55|10.42.0)"
```

## Method 5: Check from Jetson Side

On your Jetson (using the display):

1. Open terminal
2. Run these commands:

```bash
# Check IP addresses
ip addr show

# Look specifically for USB network
ip addr show | grep -A 2 "usb0\|l4tbr0"

# Or simpler
hostname -I

# Check if USB gadget is enabled
lsmod | grep g_ether
```

## Common USB Network IPs:

The Jetson might use:
- **l4tbr0 interface**: 192.168.55.1
- **usb0 interface**: Different IP
- **rndis interface**: Windows compatibility

## If USB Networking Isn't Working:

On the Jetson, enable USB gadget mode:

```bash
# Check if USB gadget is loaded
sudo modprobe g_ether

# Or try CDC mode
sudo modprobe g_cdc

# Check dmesg for USB info
dmesg | tail -20
```

## Alternative: Use WiFi IP

Since you have WiFi working:

On Jetson:
```bash
# Get WiFi IP
ip addr show wlan0 | grep inet
# or
hostname -I
```

Then on Mac:
```bash
ssh nvidia@<WIFI_IP>
```

## Quick Debug Steps:

1. **Check cable**: Make sure using USB-C port (not USB-A)
2. **Check Jetson side**: Run `ip addr show` on Jetson
3. **Check Mac side**: Look for new network interface
4. **Try different cable**: Some cables are charge-only
5. **Reboot both**: Sometimes helps reset USB networking