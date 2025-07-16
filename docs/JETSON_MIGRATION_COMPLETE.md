# Complete Jetson Migration Documentation

## Overview
This document contains all instructions and scripts needed to migrate ISEE Tutor from Jetson Orin Nano 8GB to Jetson Orin NX 16GB.

## Migration Files Created

### Documentation
- `/MIGRATION_GUIDE.md` - Detailed migration guide
- `/QUICK_MIGRATION_STEPS.md` - Quick reference checklist
- `/docs/JETSON_MIGRATION_COMPLETE.md` - This file

### Scripts
- `/scripts/backup_for_migration.sh` - Creates complete system backup
- `/scripts/mount_ssd.sh` - Mounts NVMe SSD on new Jetson
- `/scripts/jetson_nx_setup.sh` - Initial setup for new Jetson
- `/scripts/restore_from_backup.sh` - Restores system from backup

## Pre-Migration (On Current Jetson)

### 1. Create System Backup
```bash
cd /home/tutor/iseetutor
sudo ./scripts/backup_for_migration.sh
```

This creates:
- `~/iseetutor_migration_backup/iseetutor_backup_[timestamp].tar.gz` - Code and configs
- `~/iseetutor_migration_backup/iseetutor_db_[timestamp].sql` - Database dump
- `~/iseetutor_migration_backup/migration_checklist_[timestamp].txt` - Checklist
- `~/iseetutor_migration_[timestamp].tar.gz` - Combined archive

### 2. Backup AI Models (Optional)
Since you're physically moving the SSD, you can skip this:
```bash
# Only if NOT moving the physical SSD:
tar -czf models_backup.tar.gz -C /mnt/storage models/
```

### 3. Note Current Configuration
```bash
# Check SSD device
lsblk | grep nvme

# Note important configs
cat /home/tutor/iseetutor/.env | grep -E "MODEL_PATH|DB_"
```

## Migration Day (On New Jetson)

### Step 1: Install JetPack OS
1. Download NVIDIA SDK Manager on a host PC
2. Connect Jetson Orin NX via USB-C
3. Flash JetPack 5.x (same version as current)
4. Complete initial Ubuntu setup

### Step 2: Physical Hardware Transfer
1. Power off both Jetsons
2. Move from old to new:
   - NVMe SSD (contains all models and data)
   - Flash drive (if /home is on it)
   - USB audio devices
   - ReSpeaker 4-mic array

### Step 3: Initial System Setup
```bash
# Copy migration files from flash drive or network
cd ~
cp /media/flash/iseetutor_migration_*.tar.gz .

# Extract just the scripts
tar -xzf iseetutor_migration_*.tar.gz iseetutor/scripts/
cd iseetutor/scripts
chmod +x *.sh

# Run initial setup (installs system packages)
./jetson_nx_setup.sh
```

### Step 4: Mount NVMe SSD
```bash
# This script auto-detects and mounts your SSD
sudo ./mount_ssd.sh
```

The script will:
- Detect NVMe drives
- Mount to `/mnt/storage`
- Set up automatic mounting on boot
- Verify AI models are present

### Step 5: Restore System
```bash
# Make sure you're in the directory with backup files
cd ~
sudo ./iseetutor/scripts/restore_from_backup.sh
```

This will:
- Install all dependencies
- Set up PostgreSQL and Redis
- Restore database
- Extract code
- Configure services
- Install Python packages

### Step 6: Verify Installation
```bash
cd ~/iseetutor

# Run verification script
python3 verify_setup.py

# Test core components
python3 tests/test_companion_mode_simple.py

# Check services
sudo systemctl status postgresql
sudo systemctl status redis-server
```

### Step 7: Start Application
```bash
# Terminal 1 - API Server
cd ~/iseetutor
python3 start_api.py

# Terminal 2 - Frontend (development)
cd ~/iseetutor/frontend
npm start
```

## Post-Migration Configuration

### Update Environment Variables
Edit `/home/tutor/iseetutor/.env` if needed:
```bash
# Verify model paths
MODEL_PATH=/mnt/storage/models
LLM_MODEL_PATH=/mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf

# Update any hardware-specific settings
AUDIO_DEVICE_INDEX=2  # Check with python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

### Performance Optimization
```bash
# Set to max performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Monitor performance
sudo jtop
```

### Configure Auto-Start (Optional)
```bash
# Enable ISEE Tutor service
sudo systemctl enable iseetutor.service
sudo systemctl start iseetutor.service
```

## Troubleshooting

### SSD Not Mounting
```bash
# Check if SSD is detected
sudo nvme list
lsblk

# Manual mount
sudo mount /dev/nvme0n1p1 /mnt/storage
```

### Database Issues
```bash
# Check PostgreSQL
sudo -u postgres psql
\l  # List databases
\c iseetutor_db  # Connect to database
\dt  # List tables
\q  # Quit

# Recreate database if needed
sudo -u postgres createdb iseetutor_db
sudo -u postgres psql iseetutor_db < ~/iseetutor_db_*.sql
```

### Model Loading Errors
```bash
# Verify model exists
ls -la /mnt/storage/models/llm/*.gguf

# Check permissions
sudo chown -R $USER:$USER /mnt/storage

# Test model loading
python3 -c "from llama_cpp import Llama; print('Model loading test...')"
```

### Audio Device Issues
```bash
# List audio devices
arecord -l
aplay -l

# Test audio
speaker-test -t wav -c 2

# Update device index in .env
```

## Memory Benefits with 16GB

### Before (8GB Orin Nano)
- System + OS: ~2GB
- API Server: ~3GB
- LLM Model: ~4.5GB
- **Total: 9.5GB → CRASH!**

### After (16GB Orin NX)
- System + OS: ~2GB
- API Server: ~3GB
- LLM Model: ~4.5GB
- Frontend Dev: ~2GB
- **Total: 11.5GB → 4.5GB FREE!**

### New Possibilities
1. Run larger models (13B parameter)
2. Multiple model inference
3. Development + Production simultaneously
4. Aggressive caching
5. Additional services (monitoring, analytics)

## Migration Timeline

- **15 min**: Create backup on old Jetson
- **20 min**: Flash JetPack on new Jetson
- **5 min**: Physical hardware transfer
- **10 min**: Run setup scripts
- **5 min**: Verification and testing
- **Total: ~55 minutes**

## Important Notes

1. **Keep Old Jetson** until migration is verified
2. **Test Everything** before decommissioning old system
3. **Update DNS/IP** if using fixed addresses
4. **Document Changes** in this file

## Success Checklist

- [ ] JetPack OS installed
- [ ] SSD mounted at `/mnt/storage`
- [ ] PostgreSQL running with data
- [ ] Redis running
- [ ] Models loading correctly
- [ ] API server starts
- [ ] Frontend builds
- [ ] Audio devices working
- [ ] Wake word detection functional
- [ ] Can run full voice pipeline

## Support

If issues arise:
1. Check `/home/tutor/iseetutor/logs/` for errors
2. Run `python3 verify_setup.py` for system check
3. Consult `CLAUDE.md` for system documentation
4. Review hardware connections

---

Migration scripts created by Claude on 2025-07-16
For ISEE Tutor project migration from Orin Nano 8GB to Orin NX 16GB