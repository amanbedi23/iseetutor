#!/bin/bash
# Start monitoring before running the apps

echo "Starting system monitoring for ISEE Tutor crash diagnosis..."
echo "This will create logs in: /home/tutor/iseetutor/logs/monitoring/"
echo
echo "Current system state:"
echo "- Memory: $(free -h | grep Mem | awk '{print $3 " / " $2}')"
echo "- Power Mode: $(nvpmodel -q | grep 'NV Power Mode' | cut -d: -f2)"
echo "- Temperature: $(cat /sys/devices/virtual/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000 "°C"}')"
echo

# Start the monitoring in background
echo "Starting background monitor..."
nohup python3 /home/tutor/iseetutor/monitor_system.py > /dev/null 2>&1 &
MONITOR_PID=$!
echo "Monitor PID: $MONITOR_PID"

# Also start the simple bash monitor
nohup /home/tutor/iseetutor/monitor_crash.sh > /dev/null 2>&1 &
CRASH_MONITOR_PID=$!
echo "Crash monitor PID: $CRASH_MONITOR_PID"

echo
echo "Monitors started. You can now run your applications."
echo "To stop monitoring: kill $MONITOR_PID $CRASH_MONITOR_PID"
echo
echo "Logs will be in:"
echo "  /home/tutor/iseetutor/logs/monitoring/"
echo
echo "After a crash, check the latest log files to see what happened."