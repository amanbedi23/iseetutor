#!/bin/bash

echo "Testing ISEE Tutor Frontend Setup"
echo "================================="

# Check if API is running
echo -n "1. Checking API server... "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "❌ API is not running. Start with: python3 start_api.py"
    exit 1
fi

# Check WebSocket endpoint
echo -n "2. Checking WebSocket endpoint... "
if curl -s http://localhost:8000/docs | grep -q "/ws"; then
    echo "✅ WebSocket endpoint available"
else
    echo "⚠️  WebSocket endpoint not found"
fi

# Build the React app for testing
echo "3. Building React app for production..."
cd /home/tutor/iseetutor/frontend
npm run build

# Serve the built app
echo "4. Starting production server..."
npx serve -s build -l 3000 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Test the frontend
echo -n "5. Testing frontend... "
if curl -s http://localhost:3000 | grep -q "ISEE Tutor"; then
    echo "✅ Frontend is working"
else
    echo "❌ Frontend not responding"
fi

echo ""
echo "Frontend is running at: http://localhost:3000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "To stop the server, run: kill $SERVER_PID"
echo ""
echo "For development mode, run:"
echo "  cd frontend && npm start"