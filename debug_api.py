#!/usr/bin/env python3
"""Debug the API startup issues"""
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

print("1. Testing imports...")
try:
    from src.api.routes import companion, health
    print("✓ Routes imported successfully")
except Exception as e:
    print(f"✗ Failed to import routes: {e}")
    sys.exit(1)

print("\n2. Testing ModeManager...")
try:
    from src.core.companion.mode_manager import ModeManager
    print("✓ ModeManager imported successfully")
    
    print("\n3. Initializing ModeManager...")
    mode_manager = ModeManager()
    print("✓ ModeManager initialized successfully")
except Exception as e:
    print(f"✗ Failed with ModeManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing FastAPI app creation...")
try:
    from src.api.main import app
    print("✓ FastAPI app created successfully")
except Exception as e:
    print(f"✗ Failed to create app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All components loaded successfully!")
print("\nNow trying to start the server...")

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)