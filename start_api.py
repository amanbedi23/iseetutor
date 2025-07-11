#!/usr/bin/env python3
"""
Start the ISEE Tutor API server
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the app
from src.api.main import app
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 8000))
    print(f"🚀 Starting ISEE Tutor API on port {port}")
    print(f"📚 Knowledge base: {os.getenv('KNOWLEDGE_PATH', './data/knowledge')}")
    print(f"📖 API docs available at: http://localhost:{port}/docs")
    print("")
    
    # Check if uvicorn is in PATH
    uvicorn_path = os.path.expanduser("~/.local/bin/uvicorn")
    if os.path.exists(uvicorn_path):
        print(f"Using uvicorn from: {uvicorn_path}")
    
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)