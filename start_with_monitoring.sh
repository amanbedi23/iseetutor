#!/bin/bash
# Start ISEE Tutor with system monitoring

echo "=== Starting ISEE Tutor with System Monitoring ==="
echo

# Check current system state
echo "Current System State:"
echo "- Memory: $(free -h | grep Mem | awk '{print "Used: " $3 " / Total: " $2}')"
echo "- Power Mode: $(nvpmodel -q | grep 'NV Power Mode')"
echo "- CPU Temp: $(cat /sys/devices/virtual/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000}')°C"
echo

# Create log directory
mkdir -p /home/tutor/iseetutor/logs/monitoring

# Start monitoring
echo "Starting system monitors..."
cd /home/tutor/iseetutor

# Python monitor
nohup python3 monitor_system.py > /dev/null 2>&1 &
MONITOR_PID=$!
echo "System monitor started (PID: $MONITOR_PID)"

# Bash monitor
nohup ./monitor_crash.sh > /dev/null 2>&1 &
CRASH_PID=$!
echo "Crash monitor started (PID: $CRASH_PID)"

# Give monitors time to start
sleep 2

# Start the application
echo
echo "Starting ISEE Tutor application..."
./scripts/start-simple.sh &
APP_PID=$!

echo
echo "All services started!"
echo "Monitor logs: /home/tutor/iseetutor/logs/monitoring/"
echo
echo "To stop everything: kill $MONITOR_PID $CRASH_PID $APP_PID"
echo
echo "If the system crashes, check the latest log files."

# Keep running
wait