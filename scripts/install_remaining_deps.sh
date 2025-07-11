#!/bin/bash
# Install remaining dependencies for ISEE Tutor

set -e

echo "=== Installing Remaining ISEE Tutor Dependencies ==="
echo ""

# Install system dependencies (excluding npm which is already installed)
echo "Installing system dependencies..."
sudo apt install -y \
    portaudio19-dev \
    ffmpeg \
    tesseract-ocr \
    postgresql \
    postgresql-contrib \
    redis-server \
    build-essential \
    cmake

echo ""
echo "=== Installing Python packages ==="

# Upgrade pip first
echo "Upgrading pip..."
pip3 install --upgrade pip setuptools wheel

# Core packages
echo "Installing core Python packages..."
pip3 install \
    fastapi \
    uvicorn[standard] \
    pydantic \
    python-multipart \
    websockets \
    aiofiles \
    python-dotenv \
    pyyaml \
    click \
    requests \
    httpx \
    tqdm \
    colorama

# Database packages
echo "Installing database packages..."
pip3 install \
    sqlalchemy \
    psycopg2-binary \
    redis \
    minio

# Audio packages
echo "Installing audio packages..."
pip3 install \
    pyaudio \
    speechrecognition \
    pydub \
    sounddevice

# Note: Some packages might need special handling on Jetson
echo ""
echo "Note: Some AI/ML packages need special installation on Jetson:"
echo "- PyTorch: Use NVIDIA's pre-built wheels for Jetson"
echo "- Whisper: May need to build from source"
echo "- LangChain: Should install normally with pip"
echo ""

# Try to install LangChain
echo "Installing LangChain..."
pip3 install langchain langchain-community || echo "LangChain installation failed - may need manual installation"

echo ""
echo "=== Starting Services ==="
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server

echo ""
echo "=== Creating PostgreSQL Database ==="
echo "Creating database for ISEE Tutor..."
sudo -u postgres psql << EOF || echo "Database creation failed - may already exist"
CREATE USER iseetutor WITH PASSWORD 'iseetutor123';
CREATE DATABASE iseetutor_db OWNER iseetutor;
GRANT ALL PRIVILEGES ON DATABASE iseetutor_db TO iseetutor;
EOF

echo ""
echo "✅ Installation complete!"
echo ""
echo "Services running:"
systemctl is-active postgresql && echo "✅ PostgreSQL is running" || echo "❌ PostgreSQL is not running"
systemctl is-active redis-server && echo "✅ Redis is running" || echo "❌ Redis is not running"
echo ""
echo "Next steps:"
echo "1. Download the Llama model: python3 scripts/download_llama_model.py"
echo "2. Set up knowledge bases: python3 scripts/setup_knowledge_bases.py"
echo "3. Configure .env file with your settings"