#!/bin/bash
# Install script for ISEE Tutor dependencies (Fixed version)
# Run with: sudo bash install_dependencies_fixed.sh

set -e

echo "=== Installing ISEE Tutor Dependencies ==="
echo "This script will install Python pip and other system dependencies"
echo ""

# Update package list
echo "Updating package list..."
apt update

# Install Python pip and development tools
echo "Installing Python pip and development tools..."
apt install -y python3-pip python3-dev python3-venv

# Install system dependencies for audio and other features
echo "Installing system dependencies..."
apt install -y \
    portaudio19-dev \
    ffmpeg \
    tesseract-ocr \
    postgresql \
    postgresql-contrib \
    redis-server \
    git \
    wget \
    curl \
    build-essential \
    cmake

# Check if npm is already installed via NodeSource
if command -v npm &> /dev/null; then
    echo "npm is already installed via NodeSource"
    echo "Node.js version: $(node --version)"
    echo "npm version: $(npm --version)"
else
    echo "Installing Node.js and npm from NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi

echo ""
echo "=== Installing Python packages ==="
# Upgrade pip first
pip3 install --upgrade pip setuptools wheel

# Install core packages in groups to avoid dependency conflicts
echo "Installing core web framework packages..."
pip3 install \
    fastapi \
    uvicorn[standard] \
    pydantic \
    python-multipart \
    websockets \
    aiofiles \
    python-dotenv \
    pyyaml \
    click

echo "Installing database packages..."
pip3 install \
    sqlalchemy \
    psycopg2-binary \
    redis \
    alembic

echo "Installing basic ML packages..."
pip3 install \
    numpy \
    scipy \
    pandas \
    scikit-learn

# Note: Larger ML packages should be installed separately
echo ""
echo "NOTE: Some packages need special handling on Jetson:"
echo "1. PyTorch - Install using NVIDIA's wheel for Jetson"
echo "2. Transformers, Whisper, etc. - Install after PyTorch"
echo "3. ChromaDB - May need additional system dependencies"

echo ""
echo "=== Starting PostgreSQL and Redis services ==="
systemctl start postgresql || echo "PostgreSQL start failed - may need configuration"
systemctl start redis-server || echo "Redis start failed - may need configuration"
systemctl enable postgresql || true
systemctl enable redis-server || true

echo ""
echo "=== Setting up PostgreSQL (if service is running) ==="
if systemctl is-active --quiet postgresql; then
    sudo -u postgres psql << EOF || echo "PostgreSQL setup failed - database may already exist"
CREATE USER iseetutor WITH PASSWORD 'iseetutor123';
CREATE DATABASE iseetutor_db OWNER iseetutor;
GRANT ALL PRIVILEGES ON DATABASE iseetutor_db TO iseetutor;
EOF
else
    echo "PostgreSQL is not running. Please start it manually and run:"
    echo "sudo -u postgres psql"
    echo "CREATE USER iseetutor WITH PASSWORD 'iseetutor123';"
    echo "CREATE DATABASE iseetutor_db OWNER iseetutor;"
fi

echo ""
echo "✅ Basic dependencies installed successfully!"
echo ""
echo "Next steps:"
echo "1. Install PyTorch for Jetson (see requirements-jetson.txt)"
echo "2. Install remaining Python packages: pip3 install -r requirements.txt"
echo "3. Download the Llama model"
echo "4. Set up knowledge bases"
echo "5. Start the application"