#!/bin/bash
# Install script for ISEE Tutor dependencies
# Run with: sudo bash install_dependencies.sh

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
    nodejs \
    npm \
    git \
    wget \
    curl \
    build-essential \
    cmake

# Install Python packages globally (or you can use venv)
echo "Installing Python packages..."
pip3 install --upgrade pip setuptools wheel

# Core packages
pip3 install \
    langchain \
    langchain-community \
    fastapi \
    uvicorn[standard] \
    pydantic \
    python-multipart \
    websockets \
    aiofiles

# AI/ML packages
pip3 install \
    transformers \
    torch --index-url https://download.pytorch.org/whl/cpu \
    sentence-transformers \
    chromadb \
    openai-whisper \
    TTS

# Audio packages
pip3 install \
    pyaudio \
    speechrecognition \
    pydub \
    sounddevice \
    webrtcvad

# Database and storage
pip3 install \
    sqlalchemy \
    psycopg2-binary \
    redis \
    minio

# PDF and document processing
pip3 install \
    pypdf2 \
    pdf2image \
    pytesseract \
    python-docx

# Web framework packages
pip3 install \
    flask \
    flask-cors \
    python-socketio

# Utility packages
pip3 install \
    python-dotenv \
    pyyaml \
    click \
    requests \
    httpx \
    tqdm \
    colorama

# Development tools
pip3 install \
    pytest \
    pytest-asyncio \
    black \
    flake8 \
    ipython

echo ""
echo "=== Starting PostgreSQL and Redis services ==="
systemctl start postgresql
systemctl start redis-server
systemctl enable postgresql
systemctl enable redis-server

echo ""
echo "=== Creating PostgreSQL user and database ==="
sudo -u postgres psql << EOF
CREATE USER iseetutor WITH PASSWORD 'iseetutor123';
CREATE DATABASE iseetutor_db OWNER iseetutor;
GRANT ALL PRIVILEGES ON DATABASE iseetutor_db TO iseetutor;
EOF

echo ""
echo "✅ Dependencies installed successfully!"
echo ""
echo "Next steps:"
echo "1. Download the Llama model"
echo "2. Set up knowledge bases"
echo "3. Start the application"