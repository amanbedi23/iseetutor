#!/bin/bash

# ISEE Tutor Backup Script for Migration
# Creates a complete backup of the system for migration to new hardware

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ISEE Tutor Migration Backup Script ===${NC}"
echo "This script will create backups of all necessary data for migration"
echo ""

# Check if running with appropriate permissions
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Warning: Not running as root. Some files may not be accessible.${NC}"
    echo "Consider running with sudo for complete backup."
fi

# Create backup directory
BACKUP_DIR="/home/tutor/iseetutor_migration_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo -e "${GREEN}1. Backing up code and configuration...${NC}"

# Backup application code and configs
cd /home/tutor
tar -czf "$BACKUP_DIR/iseetutor_backup_${TIMESTAMP}.tar.gz" \
    --exclude='iseetutor/data/models/*' \
    --exclude='iseetutor/data/knowledge/*' \
    --exclude='iseetutor/__pycache__' \
    --exclude='iseetutor/.git' \
    --exclude='iseetutor/logs/*' \
    --exclude='iseetutor/node_modules' \
    --exclude='iseetutor/frontend/node_modules' \
    --exclude='iseetutor/frontend/build' \
    iseetutor/ \
    .env \
    .bashrc \
    .profile \
    2>/dev/null || true

echo "✓ Code backup complete"

# Backup systemd services if they exist
echo -e "${GREEN}2. Checking for system services...${NC}"
if [ -d "/etc/systemd/system" ]; then
    SERVICE_FILES=$(ls /etc/systemd/system/iseetutor* 2>/dev/null || true)
    if [ ! -z "$SERVICE_FILES" ]; then
        tar -czf "$BACKUP_DIR/services_backup_${TIMESTAMP}.tar.gz" \
            -C /etc/systemd/system/ \
            $(basename -a $SERVICE_FILES)
        echo "✓ Service files backed up"
    fi
fi

# Backup PostgreSQL database
echo -e "${GREEN}3. Backing up PostgreSQL database...${NC}"
if command -v pg_dump &> /dev/null; then
    sudo -u postgres pg_dump iseetutor_db > "$BACKUP_DIR/iseetutor_db_${TIMESTAMP}.sql" 2>/dev/null || {
        echo -e "${YELLOW}Warning: Could not dump database. You may need to do this manually.${NC}"
        echo "Manual command: sudo -u postgres pg_dump iseetutor_db > iseetutor_db.sql"
    }
else
    echo -e "${YELLOW}PostgreSQL not found. Skipping database backup.${NC}"
fi

# Get database connection info
if [ -f "/home/tutor/.env" ]; then
    echo -e "${GREEN}Database configuration from .env:${NC}"
    grep -E "DB_|DATABASE_" /home/tutor/.env | sed 's/PASSWORD=.*/PASSWORD=***/' || true
fi

# Check Redis data
echo -e "${GREEN}4. Checking Redis data...${NC}"
if command -v redis-cli &> /dev/null; then
    REDIS_SIZE=$(redis-cli DBSIZE 2>/dev/null | awk '{print $2}' || echo "0")
    echo "Redis keys: $REDIS_SIZE"
    if [ "$REDIS_SIZE" != "0" ] && [ "$REDIS_SIZE" != "" ]; then
        redis-cli BGSAVE &>/dev/null || true
        sleep 2
        # Find Redis dump file
        REDIS_DIR=$(redis-cli CONFIG GET dir 2>/dev/null | tail -1 || echo "/var/lib/redis")
        if [ -f "$REDIS_DIR/dump.rdb" ]; then
            cp "$REDIS_DIR/dump.rdb" "$BACKUP_DIR/redis_dump_${TIMESTAMP}.rdb" 2>/dev/null || {
                echo -e "${YELLOW}Could not copy Redis dump. May need sudo.${NC}"
            }
        fi
    fi
fi

# List models and content (don't backup yet due to size)
echo -e "${GREEN}5. Analyzing models and content...${NC}"
if [ -d "/mnt/storage" ]; then
    echo "Models directory size:"
    du -sh /mnt/storage/models/* 2>/dev/null || echo "No models found"
    
    echo -e "\n${YELLOW}Models need to be backed up separately due to size.${NC}"
    echo "To backup models, run:"
    echo "  tar -czf models_backup_${TIMESTAMP}.tar.gz -C /mnt/storage models/"
    
    # Create a manifest of models
    echo -e "\nCreating model manifest..."
    find /mnt/storage/models -type f -name "*.gguf" -o -name "*.bin" -o -name "*.tflite" 2>/dev/null | \
        xargs -I {} ls -lh {} > "$BACKUP_DIR/model_manifest_${TIMESTAMP}.txt" || true
fi

# Package list
echo -e "${GREEN}6. Saving package lists...${NC}"

# Python packages
if command -v pip3 &> /dev/null; then
    pip3 freeze > "$BACKUP_DIR/python_packages_${TIMESTAMP}.txt"
fi

# System packages
dpkg -l > "$BACKUP_DIR/system_packages_${TIMESTAMP}.txt"

# Hardware info
echo -e "${GREEN}7. Saving hardware configuration...${NC}"
{
    echo "=== JETSON INFO ==="
    jetson_release -v 2>/dev/null || echo "jetson_release not available"
    echo -e "\n=== AUDIO DEVICES ==="
    arecord -l 2>/dev/null || echo "No audio recording devices"
    echo -e "\n=== USB DEVICES ==="
    lsusb
    echo -e "\n=== GPIO INFO ==="
    ls -la /dev/gpio* 2>/dev/null || echo "No GPIO devices"
    echo -e "\n=== DISK USAGE ==="
    df -h
} > "$BACKUP_DIR/hardware_info_${TIMESTAMP}.txt"

# Create migration checklist
echo -e "${GREEN}8. Creating migration checklist...${NC}"
cat > "$BACKUP_DIR/migration_checklist_${TIMESTAMP}.txt" << EOF
ISEE Tutor Migration Checklist
Generated: $(date)

Current System:
- Jetson Model: $(jetson_release -m 2>/dev/null || echo "Unknown")
- Python Version: $(python3 --version)
- PostgreSQL: $(psql --version 2>/dev/null | head -1 || echo "Not found")
- Redis: $(redis-server --version 2>/dev/null | head -1 || echo "Not found")

Files Created:
1. iseetutor_backup_${TIMESTAMP}.tar.gz - Application code and configs
2. iseetutor_db_${TIMESTAMP}.sql - PostgreSQL database dump
3. python_packages_${TIMESTAMP}.txt - Python dependencies
4. system_packages_${TIMESTAMP}.txt - System packages
5. hardware_info_${TIMESTAMP}.txt - Hardware configuration

TODO on New Jetson:
[ ] Install JetPack (same version)
[ ] Install PostgreSQL 14+
[ ] Install Redis
[ ] Create iseetutor_db database
[ ] Restore database from SQL dump
[ ] Extract code backup
[ ] Install Python packages
[ ] Mount NVMe storage
[ ] Copy/mount AI models
[ ] Update .env file
[ ] Test all components

Models to Transfer (check sizes):
$(find /mnt/storage/models -type f -name "*.gguf" -o -name "*.bin" 2>/dev/null | xargs -I {} du -h {} || echo "No models found")
EOF

# Summary
echo -e "\n${GREEN}=== Backup Complete ===${NC}"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Files created:"
ls -lh "$BACKUP_DIR"/*_${TIMESTAMP}.* 2>/dev/null | awk '{print "  - "$9 " (" $5 ")"}'
echo ""
echo -e "${YELLOW}IMPORTANT: Don't forget to backup the AI models separately!${NC}"
echo "Run: tar -czf $BACKUP_DIR/models_backup_${TIMESTAMP}.tar.gz -C /mnt/storage models/"
echo ""
echo "Total backup size (excluding models):"
du -sh "$BACKUP_DIR"

# Create a convenient backup package
echo -e "\n${GREEN}Creating consolidated backup archive...${NC}"
cd "$BACKUP_DIR"
tar -czf "../iseetutor_migration_${TIMESTAMP}.tar.gz" *_${TIMESTAMP}.*
echo -e "✓ Complete backup available at: ${GREEN}/home/tutor/iseetutor_migration_${TIMESTAMP}.tar.gz${NC}"