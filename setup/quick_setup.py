#!/usr/bin/env python3
"""
Quick setup script for ISEE Tutor
Non-interactive version for easier setup
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, shell=False):
    """Run a command and return success status"""
    try:
        if shell:
            subprocess.run(cmd, shell=True, check=True)
        else:
            subprocess.run(cmd.split(), check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=== ISEE Tutor Quick Setup ===\n")
    
    # Check current directory
    if not Path("test_companion_mode_simple.py").exists():
        print("❌ Please run this script from the iseetutor directory")
        sys.exit(1)
    
    # Step 1: Check Python and pip
    print("1. Checking Python environment...")
    if run_command("python3 --version"):
        print("✅ Python3 is installed")
    else:
        print("❌ Python3 not found")
        sys.exit(1)
        
    if run_command("pip3 --version"):
        print("✅ pip3 is installed")
    else:
        print("❌ pip3 not found. Run: sudo apt install python3-pip")
        sys.exit(1)
    
    # Step 2: Create directories
    print("\n2. Creating directory structure...")
    dirs_to_create = [
        "/mnt/storage/models",
        "/mnt/storage/knowledge",
        "/mnt/storage/content", 
        "/mnt/storage/user_data",
        "logs",
        "data/models",
        "data/content",
        "data/users"
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")
    
    # Step 3: Install Python packages
    print("\n3. Installing essential Python packages...")
    essential_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-dotenv",
        "sqlalchemy",
        "redis",
        "requests",
        "tqdm"
    ]
    
    for package in essential_packages:
        print(f"   Installing {package}...")
        if not run_command(f"pip3 install {package}"):
            print(f"   ⚠️  Failed to install {package}")
    
    # Step 4: Create .env file
    print("\n4. Creating environment configuration...")
    env_content = """# ISEE Tutor Environment Configuration
APP_ENV=development
APP_DEBUG=True
APP_PORT=8000

# Database
DATABASE_URL=postgresql://iseetutor:iseetutor123@localhost/iseetutor_db

# Model paths
MODEL_PATH=/mnt/storage/models/Llama-3.2-8B-Instruct-Q4_K_M.gguf
KNOWLEDGE_PATH=/mnt/storage/knowledge

# Audio settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# Mode settings
DEFAULT_MODE=tutor
ALLOW_MODE_SWITCH=true
"""
    
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")
    
    # Step 5: Test companion mode
    print("\n5. Testing companion mode...")
    if run_command("python3 test_companion_mode_simple.py"):
        print("✅ Companion mode test passed!")
    else:
        print("⚠️  Companion mode test failed")
    
    # Summary
    print("\n" + "="*50)
    print("SETUP STATUS")
    print("="*50)
    
    checks = {
        "Python & pip": run_command("pip3 --version"),
        "Node.js & npm": run_command("npm --version"),
        "Directory structure": Path("/mnt/storage").exists(),
        "Environment file": Path(".env").exists(),
        "Companion mode": Path("src/core/companion/mode_manager.py").exists()
    }
    
    for item, status in checks.items():
        print(f"{item}: {'✅' if status else '❌'}")
    
    print("\n📋 NEXT STEPS:")
    print("1. Install system dependencies:")
    print("   sudo bash scripts/install_remaining_deps.sh")
    print("\n2. Download Llama model:")
    print("   python3 scripts/download_llama_model.py")
    print("\n3. Set up knowledge bases:")
    print("   python3 scripts/setup_knowledge_bases.py")
    print("\n4. Start developing!")
    
    # Check if we can import key modules
    print("\n🔍 Module availability:")
    modules_to_check = ["fastapi", "pydantic", "sqlalchemy", "langchain"]
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"   {module}: ✅")
        except ImportError:
            print(f"   {module}: ❌ (install with: pip3 install {module})")

if __name__ == "__main__":
    main()