#!/bin/bash

echo "🚀 Starting ISEE Tutor Development Environment"
echo "============================================="

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -f "react-scripts start" 2>/dev/null
pkill -f "serve -s build" 2>/dev/null

# Check if API is running
echo -n "Checking API server... "
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API not running"
    echo "Starting API server..."
    cd /home/tutor/iseetutor
    python3 start_api.py &
    API_PID=$!
    
    # Wait for API to be ready
    while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
        sleep 1
    done
    echo "✅ API server started (PID: $API_PID)"
else
    echo "✅ API already running"
fi

# Start React development server
echo ""
echo "Starting React frontend..."
cd /home/tutor/iseetutor/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "📱 Frontend starting on http://localhost:3000"
echo "📚 API documentation at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start React in foreground so Ctrl+C works
npm start