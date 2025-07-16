#!/bin/bash
# Test ISEE Tutor with text browser (for debugging)

echo "Testing ISEE Tutor with text browser..."

# Ensure services are running
cd /home/tutor/iseetutor

if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "API not running. Start it with: python3 start_api.py"
    exit 1
fi

if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend not running. Start it with: cd frontend && npm start"
    exit 1
fi

echo
echo "Services are running!"
echo "Testing API health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo
echo "Frontend is available at: http://localhost:3000"
echo "API docs at: http://localhost:8000/docs"
echo
echo "Since we're in terminal mode, you can:"
echo "1. Install Epiphany: ./scripts/install-epiphany.sh"
echo "2. Access from another device: http://$(hostname -I | awk '{print $1}'):3000"
echo "3. Use lynx/w3m text browser: sudo apt install lynx && lynx http://localhost:3000"