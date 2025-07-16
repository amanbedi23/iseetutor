#!/bin/bash
# Diagnose common Jetson Nano Orin issues that cause crashes

echo "=== Jetson Nano Orin Diagnostic Report ==="
echo "Date: $(date)"
echo

# Check current memory status
echo "1. MEMORY STATUS:"
free -h
echo

# Check if swap is enabled (critical for Jetson with limited RAM)
echo "2. SWAP STATUS:"
swapon --show
if [ -z "$(swapon --show)" ]; then
    echo "⚠️  WARNING: No swap space configured! This can cause crashes with heavy workloads."
    echo "   Recommended: Create at least 8GB swap file"
fi
echo

# Check temperature
echo "3. TEMPERATURE STATUS:"
for zone in /sys/devices/virtual/thermal/thermal_zone*/temp; do
    if [ -f "$zone" ]; then
        temp=$(cat "$zone")
        temp_c=$((temp/1000))
        zone_name=$(basename $(dirname "$zone"))
        echo "$zone_name: ${temp_c}°C"
        if [ $temp_c -gt 80 ]; then
            echo "⚠️  WARNING: Temperature above 80°C!"
        fi
    fi
done
echo

# Check power mode
echo "4. POWER MODE:"
if command -v nvpmodel &> /dev/null; then
    nvpmodel -q | grep "NV Power Mode"
    echo "   Note: Mode 0 (MAXN) uses maximum power but may cause thermal issues"
    echo "   Mode 1 (25W) is more stable for continuous operation"
fi
echo

# Check for thermal throttling
echo "5. THERMAL THROTTLING CHECK:"
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq ]; then
    cur_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
    max_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)
    echo "Current CPU freq: $((cur_freq/1000)) MHz"
    echo "Max CPU freq: $((max_freq/1000)) MHz"
    if [ $cur_freq -lt $max_freq ]; then
        echo "⚠️  CPU may be throttled!"
    fi
fi
echo

# Check for OOM killer activity
echo "6. OOM KILLER ACTIVITY (last 24 hours):"
dmesg -T | grep -i "killed process" | tail -10
if [ -z "$(dmesg -T | grep -i 'killed process')" ]; then
    echo "No OOM killer activity detected"
fi
echo

# Check disk space
echo "7. DISK SPACE:"
df -h /
echo

# Check for memory-heavy processes
echo "8. MEMORY-HEAVY PROCESSES:"
ps aux --sort=-%mem | head -10
echo

# Check ulimits
echo "9. ULIMIT SETTINGS:"
ulimit -a
echo

# Check for zombie processes
echo "10. ZOMBIE PROCESSES:"
ps aux | grep defunct | grep -v grep
if [ -z "$(ps aux | grep defunct | grep -v grep)" ]; then
    echo "No zombie processes found"
fi
echo

# Recommendations
echo "=== RECOMMENDATIONS FOR STABILITY ==="
echo "1. Create swap file if not present:"
echo "   sudo fallocate -l 8G /swapfile"
echo "   sudo chmod 600 /swapfile"
echo "   sudo mkswap /swapfile"
echo "   sudo swapon /swapfile"
echo
echo "2. Set power mode to 25W for stability:"
echo "   sudo nvpmodel -m 1"
echo
echo "3. Increase swap tendency for earlier swapping:"
echo "   echo 'vm.swappiness=60' | sudo tee -a /etc/sysctl.conf"
echo
echo "4. Monitor and limit memory usage in applications"
echo "5. Consider adding cooling if temperatures exceed 80°C"
echo
echo "=== END DIAGNOSTIC REPORT ===">