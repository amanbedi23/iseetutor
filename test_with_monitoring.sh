#!/bin/bash
# Script to test frontend/backend with monitoring

echo "Starting Jetson monitoring in background..."
python3 monitor_jetson.py &
MONITOR_PID=$!

echo "Monitor PID: $MONITOR_PID"
echo ""
echo "Now start your frontend and backend tests."
echo "The monitor will log system resources to jetson_monitor.log"
echo ""
echo "To stop monitoring, run: kill $MONITOR_PID"
echo "To view live stats: tail -f jetson_monitor.log"
echo ""
echo "Suggested test sequence:"
echo "1. In terminal 1: python3 start_api.py"
echo "2. In terminal 2: cd frontend && npm run dev"
echo "3. Watch this monitor for resource spikes"
echo ""
echo "Press Ctrl+C here to stop monitoring"

# Wait for user to stop
wait $MONITOR_PID