#!/bin/bash
# Run the API server with proper error handling

echo "Starting ISEE Tutor API..."
echo "Press Ctrl+C to stop"
echo ""

# Kill any existing processes on port 8000
lsof -ti:8000 | xargs -r kill -9 2>/dev/null

# Run the API with error output
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --log-level info 2>&1

# If it crashes, show the error
echo ""
echo "API server stopped. Exit code: $?"