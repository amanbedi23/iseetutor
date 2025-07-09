#!/bin/bash
# Initial Setup Script for ISEE Tutor Project
# Run this on your Jetson Orin Nano

set -e  # Exit on error

echo "=== ISEE Tutor Initial Setup ==="

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "Warning: This doesn't appear to be a Jetson device"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create project directory
PROJECT_DIR="$HOME/isee-tutor"
echo "Creating project directory at $PROJECT_DIR..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create directory structure
echo "Creating project structure..."
mkdir -p src/{core,education/subjects,ui/{web/{static/{css,js,images},templates},touch},utils}
mkdir -p data/{content,models,audio,users}
mkdir -p tests/{unit,integration,hardware}
mkdir -p config scripts docs logs
mkdir -p web/{src,public}

# Create Python package files
echo "Initializing Python packages..."
touch src/__init__.py
touch src/core/__init__.py
touch src/education/__init__.py
touch src/education/subjects/__init__.py
touch src/ui/__init__.py
touch src/ui/web/__init__.py
touch src/ui/touch/__init__.py
touch src/utils/__init__.py

# Create requirements.txt
echo "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
# Core dependencies
numpy==1.24.3
scipy==1.10.1
pandas==2.0.3

# Audio processing
pyaudio==0.2.11
speechrecognition==3.10.0
pyttsx3==2.90
sounddevice==0.4.6
librosa==0.10.0

# Web framework
flask==2.3.2
flask-cors==4.0.0
flask-socketio==5.3.4

# Hardware control
Jetson.GPIO==2.1.0
pyserial==3.5

# AI/ML (install PyTorch separately for Jetson)
transformers==4.30.2
sentencepiece==0.1.99

# Database
sqlalchemy==2.0.17
alembic==1.11.1

# Utilities
python-dotenv==1.0.0
pyyaml==6.0
click==8.1.3
requests==2.31.0
pytest==7.4.0
black==23.3.0
pylint==2.17.4

# Development
ipython==8.14.0
jupyter==1.0.0
EOF

# Create .env.example
echo "Creating .env.example..."
cat > .env.example << 'EOF'
# Application settings
APP_ENV=development
APP_DEBUG=True
APP_PORT=5000

# Audio settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK_SIZE=1024

# Speech recognition
SPEECH_RECOGNITION_ENGINE=google  # or sphinx, whisper
SPEECH_LANGUAGE=en-US

# TTS settings
TTS_ENGINE=pyttsx3  # or gtts, azure
TTS_VOICE_ID=0
TTS_RATE=150

# Hardware
BUTTON_GPIO_PIN=18
LED_GPIO_PIN=32
LED_COUNT=16

# Model settings
MODEL_PATH=/mnt/storage/models
CONTENT_PATH=/mnt/storage/content

# Database
DATABASE_URL=sqlite:///data/isee_tutor.db

# API Keys (if using cloud services)
# OPENAI_API_KEY=your_key_here
# AZURE_SPEECH_KEY=your_key_here
EOF

# Create .gitignore
echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
.env
*.log
logs/
data/users/*
data/models/*
!data/models/.gitkeep
data/content/*
!data/content/.gitkeep

# OS
.DS_Store
Thumbs.db

# Test coverage
htmlcov/
.coverage
.pytest_cache/

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Build
build/
dist/
*.egg-info/
EOF

# Create .gitkeep files
touch data/models/.gitkeep
touch data/content/.gitkeep
touch logs/.gitkeep

# Create main.py
echo "Creating main.py..."
cat > src/main.py << 'EOF'
#!/usr/bin/env python3
"""
ISEE Tutor - Main Application Entry Point
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("Starting ISEE Tutor application...")
    
    # Check environment
    env = os.getenv('APP_ENV', 'development')
    logger.info(f"Running in {env} mode")
    
    # TODO: Initialize components
    # - Audio system
    # - Speech recognition
    # - LLM interface
    # - Web server
    # - Hardware controls
    
    logger.info("ISEE Tutor is ready!")
    
    # Keep running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Shutting down ISEE Tutor...")

if __name__ == "__main__":
    main()
EOF

# Create hardware test script
echo "Creating hardware test script..."
cat > scripts/test_hardware.py << 'EOF'
#!/usr/bin/env python3
"""
Hardware Component Test Script
"""

import os
import sys
import time
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_audio_output():
    """Test audio output"""
    print("\n=== Testing Audio Output ===")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say("Hello, this is a test of the audio output system.")
        engine.runAndWait()
        print("✓ Audio output test complete")
    except Exception as e:
        print(f"✗ Audio output test failed: {e}")

def test_audio_input():
    """Test audio input"""
    print("\n=== Testing Audio Input ===")
    try:
        # List audio devices
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        print("Available recording devices:")
        print(result.stdout)
        
        # TODO: Add actual recording test
        print("✓ Audio input devices detected")
    except Exception as e:
        print(f"✗ Audio input test failed: {e}")

def test_gpio():
    """Test GPIO (button)"""
    print("\n=== Testing GPIO ===")
    try:
        import Jetson.GPIO as GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print("✓ GPIO initialized")
        print("Note: Physical button test requires manual interaction")
        GPIO.cleanup()
    except Exception as e:
        print(f"✗ GPIO test failed: {e}")

def test_storage():
    """Test storage availability"""
    print("\n=== Testing Storage ===")
    paths = [
        ('/mnt/storage', 'NVMe SSD'),
        (os.path.expanduser('~/isee-tutor/data'), 'Project data directory')
    ]
    
    for path, name in paths:
        if os.path.exists(path):
            try:
                # Get disk usage
                stat = os.statvfs(path)
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
                total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
                print(f"✓ {name}: {free_gb:.1f}GB free of {total_gb:.1f}GB")
            except Exception as e:
                print(f"✗ Error checking {name}: {e}")
        else:
            print(f"✗ {name} not found at {path}")

def main():
    """Run all hardware tests"""
    print("ISEE Tutor Hardware Test Suite")
    print("=" * 40)
    
    test_storage()
    test_audio_output()
    test_audio_input()
    test_gpio()
    
    print("\n" + "=" * 40)
    print("Hardware tests complete!")

if __name__ == "__main__":
    main()
EOF

# Make scripts executable
chmod +x scripts/test_hardware.py
chmod +x src/main.py

# Create README
echo "Creating README.md..."
cat > README.md << 'EOF'
# ISEE Tutor

An AI-powered interactive tutor device for ISEE test preparation.

## Features
- Voice interaction with speech recognition and synthesis
- Touch-based interface for visual learning
- Adaptive learning algorithms
- Progress tracking and reporting
- Multi-subject support (Math, Verbal, Reading)

## Hardware
- NVIDIA Jetson Orin Nano
- 10.1" Touchscreen Display
- ReSpeaker USB Mic Array
- USB Speaker
- 1TB NVMe SSD

## Quick Start

1. Clone this repository
2. Run setup: `./scripts/setup.sh`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and configure
5. Run: `python src/main.py`

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for development setup.

## License

Private project - All rights reserved
EOF

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate and install basic packages
echo "Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install wheel setuptools

# Install some basic packages (others may need special handling on Jetson)
pip install python-dotenv pyyaml click requests pytest black pylint

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Install remaining dependencies: pip install -r requirements.txt"
echo "3. Copy .env.example to .env and configure"
echo "4. Test hardware: python scripts/test_hardware.py"
echo "5. Start development: python src/main.py"
echo ""
echo "Project location: $PROJECT_DIR"
EOF

# Make setup script executable
chmod +x initial-setup.sh