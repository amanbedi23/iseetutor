#!/bin/bash
# Simple monitoring script that logs to file before crash

LOG_FILE="/home/tutor/iseetutor/logs/monitoring/crash_monitor_$(date +%Y%m%d_%H%M%S).log"
mkdir -p /home/tutor/iseetutor/logs/monitoring

echo "=== Crash Monitor Started at $(date) ===" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"

# Function to log system state
log_state() {
    echo -e "\n[$(date +%H:%M:%S)] System State:" | tee -a "$LOG_FILE"
    
    # Memory info
    echo "-- Memory --" | tee -a "$LOG_FILE"
    free -h | tee -a "$LOG_FILE"
    
    # CPU info
    echo -e "\n-- CPU Load --" | tee -a "$LOG_FILE"
    uptime | tee -a "$LOG_FILE"
    
    # Temperature
    echo -e "\n-- Temperature --" | tee -a "$LOG_FILE"
    for zone in /sys/devices/virtual/thermal/thermal_zone*/temp; do
        if [ -f "$zone" ]; then
            temp=$(cat "$zone")
            temp_c=$((temp/1000))
            zone_name=$(basename $(dirname "$zone"))
            echo "$zone_name: ${temp_c}°C" | tee -a "$LOG_FILE"
        fi
    done
    
    # Top processes
    echo -e "\n-- Top Processes (CPU) --" | tee -a "$LOG_FILE"
    ps aux --sort=-%cpu | head -10 | tee -a "$LOG_FILE"
    
    # Check for OOM killer activity
    echo -e "\n-- Checking dmesg for OOM killer --" | tee -a "$LOG_FILE"
    dmesg | grep -i "killed process" | tail -5 | tee -a "$LOG_FILE"
    
    # Disk space
    echo -e "\n-- Disk Space --" | tee -a "$LOG_FILE"
    df -h / | tee -a "$LOG_FILE"
    
    # Swap usage
    echo -e "\n-- Swap Usage --" | tee -a "$LOG_FILE"
    swapon --show | tee -a "$LOG_FILE"
    
    # GPU info if available
    if command -v nvidia-smi &> /dev/null; then
        echo -e "\n-- GPU Status --" | tee -a "$LOG_FILE"
        nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv | tee -a "$LOG_FILE"
    fi
    
    # Power mode
    if command -v nvpmodel &> /dev/null; then
        echo -e "\n-- Power Mode --" | tee -a "$LOG_FILE"
        nvpmodel -q | grep "NV Power Mode" | tee -a "$LOG_FILE"
    fi
    
    echo -e "\n==========================================\n" | tee -a "$LOG_FILE"
}

# Monitor loop
echo -e "\nStarting continuous monitoring (Ctrl+C to stop)...\n" | tee -a "$LOG_FILE"

while true; do
    log_state
    sleep 2
done