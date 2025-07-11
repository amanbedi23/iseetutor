# ISEE Tutor Setup Steps

## Current Status
- ✅ Jetson flashed and running Ubuntu
- ✅ Touchscreen working
- ✅ VS Code connected
- ✅ Basic Python packages installed (fastapi, uvicorn, redis)
- ✅ Knowledge databases created
- ❌ PostgreSQL not installed
- ❌ Redis server not installed
- ❌ LLM models not downloaded
- ❌ Storage directories not created

## Step-by-Step Setup Guide

### 1. Complete System Dependencies Installation

Since npm is already installed, let's install the remaining dependencies:

```bash
# Install remaining system packages
sudo apt install -y portaudio19-dev ffmpeg tesseract-ocr postgresql postgresql-contrib redis-server

# Or use the fixed script
sudo bash scripts/install_dependencies_fixed.sh
```

### 2. Create Storage Directories

```bash
bash setup/create_storage_dirs.sh
```

This creates:
- `/mnt/storage/models` - For LLM models
- `/mnt/storage/knowledge` - For knowledge bases
- `/mnt/storage/content` - For processed content
- `/mnt/storage/user_data` - For user data

### 3. Install Python Dependencies

Install in stages to avoid conflicts:

```bash
# Stage 1: Core packages (already done)
pip3 install fastapi uvicorn redis python-dotenv

# Stage 2: Database and web
pip3 install sqlalchemy psycopg2-binary alembic aiofiles websockets

# Stage 3: Basic ML packages
pip3 install numpy scipy pandas scikit-learn

# Stage 4: LLM support (do this AFTER installing PyTorch)
pip3 install langchain langchain-community transformers
```

### 4. Install PyTorch for Jetson

```bash
# Download PyTorch wheel for Jetson
wget https://developer.download.nvidia.com/compute/redist/jp/v511/pytorch/torch-2.1.0a0+41361538.nv23.06-cp310-cp310-linux_aarch64.whl

# Install it
pip3 install torch-2.1.0a0+41361538.nv23.06-cp310-cp310-linux_aarch64.whl

# Verify installation
python3 -c "import torch; print(f'PyTorch {torch.__version__}')"
```

### 5. Download LLM Models

First, check if the download script exists:

```bash
# Check the script
cat scripts/download_llama_model.py

# If it exists, run it
python3 scripts/download_llama_model.py
```

If not, I can help create it.

### 6. Set Up Databases

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER iseetutor WITH PASSWORD 'iseetutor123';
CREATE DATABASE iseetutor_db OWNER iseetutor;
GRANT ALL PRIVILEGES ON DATABASE iseetutor_db TO iseetutor;
EOF

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 7. Test the System

```bash
# Test database connections
python3 -c "import psycopg2; print('PostgreSQL OK')"
python3 -c "import redis; r=redis.Redis(); r.ping(); print('Redis OK')"

# Test the API
python3 start_api.py
```

## Quick Setup Commands (Run in Order)

```bash
# 1. System dependencies
sudo apt install -y portaudio19-dev ffmpeg tesseract-ocr postgresql postgresql-contrib redis-server

# 2. Storage setup
bash setup/create_storage_dirs.sh

# 3. Database setup
sudo systemctl start postgresql redis-server
sudo systemctl enable postgresql redis-server
sudo -u postgres createuser iseetutor -P  # Enter password: iseetutor123
sudo -u postgres createdb -O iseetutor iseetutor_db

# 4. Python packages (basic)
pip3 install sqlalchemy psycopg2-binary alembic langchain

# 5. Test
python3 start_api.py
```

## What's Next After Basic Setup

1. **Audio Hardware Setup**
   - Connect USB microphone
   - Connect USB speaker
   - Test with `arecord -l` and `aplay -l`

2. **Download Models**
   - Llama 3.2 model (4-6GB)
   - Whisper model for speech recognition
   - Text-to-speech models

3. **Configure Environment**
   - Update `.env` file with correct paths
   - Set model paths after downloading

4. **Build Web Interface**
   - cd web && npm install
   - npm start

5. **Test Complete System**
   - Voice interaction
   - Mode switching
   - Knowledge retrieval