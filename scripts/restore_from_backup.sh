#!/bin/bash

# ISEE Tutor Restore Script for New Jetson
# Restores the system from migration backup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ISEE Tutor Migration Restore Script ===${NC}"
echo "This script will restore ISEE Tutor on your new Jetson"
echo ""

# Check if running as root for system packages
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}This script must be run as root (sudo)${NC}"
    exit 1
fi

# Find backup files
echo -e "${GREEN}1. Looking for backup files...${NC}"
BACKUP_CODE=$(ls iseetutor_backup_*.tar.gz 2>/dev/null | head -1)
BACKUP_DB=$(ls iseetutor_db_*.sql 2>/dev/null | head -1)
BACKUP_MODELS=$(ls models_backup_*.tar.gz 2>/dev/null | head -1)

if [ -z "$BACKUP_CODE" ]; then
    echo -e "${RED}Error: No code backup found (iseetutor_backup_*.tar.gz)${NC}"
    exit 1
fi

echo "Found backups:"
echo "  - Code: $BACKUP_CODE"
[ ! -z "$BACKUP_DB" ] && echo "  - Database: $BACKUP_DB"
[ ! -z "$BACKUP_MODELS" ] && echo "  - Models: $BACKUP_MODELS"

# Install system dependencies
echo -e "\n${GREEN}2. Installing system dependencies...${NC}"
apt-get update
apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libboost-thread-dev \
    portaudio19-dev \
    ffmpeg \
    sox \
    libsox-fmt-all

# For Jetson specific
apt-get install -y \
    python3-opencv \
    libcudnn8 \
    libcublas11 \
    cuda-toolkit-11-4

echo "✓ System packages installed"

# Setup PostgreSQL
echo -e "\n${GREEN}3. Setting up PostgreSQL...${NC}"
systemctl start postgresql
systemctl enable postgresql

# Create database user and database
sudo -u postgres psql << EOF
CREATE USER iseetutor WITH PASSWORD 'iseetutor';
CREATE DATABASE iseetutor_db OWNER iseetutor;
GRANT ALL PRIVILEGES ON DATABASE iseetutor_db TO iseetutor;
EOF

echo "✓ PostgreSQL configured"

# Extract code backup
echo -e "\n${GREEN}4. Extracting code backup...${NC}"
cd /home/jetson
tar -xzf "$BACKUP_CODE"
chown -R jetson:jetson iseetutor/
echo "✓ Code extracted"

# Restore database if backup exists
if [ ! -z "$BACKUP_DB" ] && [ -f "$BACKUP_DB" ]; then
    echo -e "\n${GREEN}5. Restoring database...${NC}"
    sudo -u postgres psql iseetutor_db < "$BACKUP_DB"
    echo "✓ Database restored"
else
    echo -e "\n${YELLOW}5. No database backup found, skipping...${NC}"
fi

# Setup Python environment
echo -e "\n${GREEN}6. Setting up Python environment...${NC}"
cd /home/jetson/iseetutor

# Install Python packages
if [ -f "requirements.txt" ]; then
    sudo -u jetson pip3 install -r requirements.txt
fi

if [ -f "requirements-jetson.txt" ]; then
    sudo -u jetson pip3 install -r requirements-jetson.txt
fi

echo "✓ Python packages installed"

# Check storage directory
echo -e "\n${GREEN}7. Checking storage directory...${NC}"
if mount | grep -q "/mnt/storage"; then
    echo -e "${GREEN}✓ /mnt/storage is already mounted${NC}"
    df -h /mnt/storage
else
    echo -e "${YELLOW}Warning: /mnt/storage is not mounted${NC}"
    echo "Run ./mount_ssd.sh first to mount your NVMe SSD"
    echo -n "Continue without SSD? (y/n): "
    read CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Exiting. Please mount SSD first."
        exit 1
    fi
    mkdir -p /mnt/storage
    chown jetson:jetson /mnt/storage
fi

# Restore models if backup exists
if [ ! -z "$BACKUP_MODELS" ] && [ -f "$BACKUP_MODELS" ]; then
    echo -e "\n${GREEN}8. Restoring AI models (this may take a while)...${NC}"
    tar -xzf "$BACKUP_MODELS" -C /mnt/storage/
    echo "✓ Models restored"
else
    echo -e "\n${YELLOW}8. No model backup found${NC}"
    echo "You'll need to either:"
    echo "  1. Mount your NVMe drive with existing models"
    echo "  2. Download models using the setup scripts"
fi

# Setup services
echo -e "\n${GREEN}9. Setting up services...${NC}"

# Redis
systemctl start redis-server
systemctl enable redis-server

# Check for service files
if ls services_backup_*.tar.gz 1> /dev/null 2>&1; then
    echo "Restoring systemd services..."
    tar -xzf services_backup_*.tar.gz -C /etc/systemd/system/
    systemctl daemon-reload
fi

# NPM install for frontend
echo -e "\n${GREEN}10. Setting up frontend...${NC}"
if [ -d "/home/jetson/iseetutor/frontend" ]; then
    cd /home/jetson/iseetutor/frontend
    sudo -u jetson npm install
    echo "✓ Frontend dependencies installed"
fi

# Set permissions
echo -e "\n${GREEN}11. Setting permissions...${NC}"
chown -R jetson:jetson /home/jetson/iseetutor
chmod +x /home/jetson/iseetutor/scripts/*.sh
chmod +x /home/jetson/iseetutor/*.py

# Update .env file
echo -e "\n${GREEN}12. Checking configuration...${NC}"
if [ -f "/home/jetson/iseetutor/.env" ]; then
    echo -e "${YELLOW}Please review and update .env file:${NC}"
    echo "  - Database credentials"
    echo "  - Model paths (/mnt/storage/models/)"
    echo "  - API keys"
    echo "  - Hardware-specific settings"
else
    echo -e "${RED}Warning: No .env file found!${NC}"
    echo "Copy .env.example to .env and configure"
fi

# Hardware setup reminders
echo -e "\n${GREEN}13. Hardware Configuration Reminders:${NC}"
echo "  - Connect USB audio devices"
echo "  - Connect ReSpeaker 4-mic array"
echo "  - Update GPIO pin mappings if needed"
echo "  - Set Jetson to max performance: sudo nvpmodel -m 0"

# Create test script
cat > /home/jetson/iseetutor/test_migration.sh << 'EOF'
#!/bin/bash
echo "Testing ISEE Tutor migration..."

# Test database
echo -n "PostgreSQL: "
if sudo -u postgres psql -d iseetutor_db -c "SELECT 1" &>/dev/null; then
    echo "✓"
else
    echo "✗"
fi

# Test Redis
echo -n "Redis: "
if redis-cli ping &>/dev/null; then
    echo "✓"
else
    echo "✗"
fi

# Test Python
echo -n "Python imports: "
if python3 -c "import fastapi, torch, whisper" &>/dev/null; then
    echo "✓"
else
    echo "✗ (some packages may need installation)"
fi

# Test models
echo -n "Models directory: "
if [ -d "/mnt/storage/models" ]; then
    echo "✓"
    ls -la /mnt/storage/models/llm/*.gguf 2>/dev/null || echo "  No LLM models found"
else
    echo "✗"
fi

echo -e "\nRun the following to test components:"
echo "  cd /home/jetson/iseetutor"
echo "  python3 verify_setup.py"
echo "  python3 tests/test_companion_mode_simple.py"
EOF

chmod +x /home/jetson/iseetutor/test_migration.sh
chown jetson:jetson /home/jetson/iseetutor/test_migration.sh

# Summary
echo -e "\n${GREEN}=== Restore Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Review and update /home/jetson/iseetutor/.env"
echo "2. Mount or copy your AI models to /mnt/storage/models/"
echo "3. Run: /home/jetson/iseetutor/test_migration.sh"
echo "4. Run: cd /home/jetson/iseetutor && python3 verify_setup.py"
echo "5. Start the application: python3 start_api.py"
echo ""
echo -e "${GREEN}Welcome to your new Jetson Orin NX 16GB!${NC}"