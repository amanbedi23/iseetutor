#!/bin/bash
# Start the ISEE Tutor API server

cd /home/tutor/iseetutor

# Kill any existing processes
pkill -f "uvicorn src.api.main:app" 2>/dev/null

# Start the API server
echo "Starting ISEE Tutor API server..."
python3 start_api.py