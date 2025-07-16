#!/bin/bash
# Simple startup script without snap dependencies

echo "Starting ISEE Tutor (Simple Mode)..."

# Start API server in background
echo "Starting API server..."
cd /home/tutor/iseetutor
python3 start_api.py &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "API server ready!"
        break
    fi
    sleep 1
done

# Start frontend dev server
echo "Starting frontend..."
cd /home/tutor/iseetutor/frontend
export BROWSER=none  # Prevent auto-opening browser
npm start &
FRONTEND_PID=$!

echo
echo "Services started:"
echo "  API PID: $API_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo
echo "Access the application at:"
echo "  http://localhost:3000"
echo "  http://$(hostname -I | awk '{print $1}'):3000"
echo
echo "To stop: kill $API_PID $FRONTEND_PID"
echo

# Keep script running
wait