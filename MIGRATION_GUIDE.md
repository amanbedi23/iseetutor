# ISEE Tutor Migration Guide - Jetson to Jetson

## Overview
This guide helps you migrate your ISEE Tutor system from the current Jetson Orin Nano 8GB to the new Jetson Orin NX 16GB.

## Current System Configuration

### Hardware
- **Current**: Jetson Orin Nano 8GB
- **Storage**: 
  - Internal: OS and system files
  - Flash Drive: Code and user data (possibly at /home/tutor)
  - NVMe SSD: 1TB at /mnt/storage for models and content

### Software Stack
- **OS**: Ubuntu 20.04 with JetPack 5.x
- **Python**: 3.10+
- **Database**: PostgreSQL 14.18
- **Cache**: Redis 6.0.16
- **AI Models**:
  - Llama 3.1 8B (4.58GB) at `/mnt/storage/models/llm/`
  - Whisper base model
  - OpenWakeWord models

## What Needs to Be Migrated

### 1. Code and Configuration
- `/home/tutor/iseetutor/` - All application code
- `/home/tutor/.env` - Environment variables
- System service files (if any in /etc/systemd/system/)

### 2. Databases
- PostgreSQL database: `iseetutor_db`
- Redis data (if persistence is enabled)
- ChromaDB vector stores in `/mnt/storage/knowledge/`

### 3. AI Models and Content
- `/mnt/storage/models/` - All AI models
- `/mnt/storage/content/` - Educational content
- `/mnt/storage/knowledge/` - Vector databases

### 4. User Data
- Student profiles
- Progress tracking data
- Quiz results
- Parent accounts

## Migration Steps

### Step 1: On Current Jetson - Create Backup

Run the backup script:
```bash
cd /home/tutor/iseetutor
sudo ./scripts/backup_for_migration.sh
```

This will create:
- `iseetutor_backup_[date].tar.gz` - Code and configs
- `iseetutor_db_[date].sql` - Database dump
- `models_backup_[date].tar.gz` - AI models (large file!)

### Step 2: Prepare New Jetson

1. **Flash JetPack** (same version as current)
   ```bash
   # Use NVIDIA SDK Manager on a host PC
   ```

2. **Initial Setup**
   ```bash
   # Connect to new Jetson
   ssh jetson@[new-ip]
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   ```

3. **Mount Storage**
   ```bash
   # If using same NVMe SSD, just mount it
   sudo mkdir -p /mnt/storage
   sudo mount /dev/nvme0n1p1 /mnt/storage
   
   # Add to /etc/fstab for auto-mount
   echo "UUID=$(sudo blkid -s UUID -o value /dev/nvme0n1p1) /mnt/storage ext4 defaults 0 2" | sudo tee -a /etc/fstab
   ```

### Step 3: Transfer Files

1. **Via Network** (if both Jetsons are on same network):
   ```bash
   # From old Jetson
   scp iseetutor_backup_*.tar.gz jetson@[new-ip]:/home/jetson/
   scp iseetutor_db_*.sql jetson@[new-ip]:/home/jetson/
   
   # Models (this will take time)
   scp models_backup_*.tar.gz jetson@[new-ip]:/home/jetson/
   ```

2. **Via External Drive**:
   ```bash
   # Copy to USB drive on old Jetson
   cp *.tar.gz *.sql /media/usb/
   
   # On new Jetson
   cp /media/usb/*.tar.gz /media/usb/*.sql ~/
   ```

### Step 4: Restore on New Jetson

Run the restore script:
```bash
# First, copy the restore script
tar -xzf iseetutor_backup_*.tar.gz iseetutor/scripts/restore_from_backup.sh
chmod +x iseetutor/scripts/restore_from_backup.sh

# Run restore
sudo ./iseetutor/scripts/restore_from_backup.sh
```

### Step 5: Verify Installation

```bash
cd /home/jetson/iseetutor
python3 verify_setup.py
```

## Important Notes

### Model Storage
- If you're moving the NVMe SSD physically, you won't need to transfer models
- Just mount the drive on the new Jetson

### Database Passwords
- PostgreSQL passwords are stored in .env
- Redis doesn't have auth by default

### Hardware-Specific Configs
- GPIO pin numbers might differ
- Check audio device names with `arecord -l`

### Memory Benefits
With 16GB RAM, you can:
- Run development and production simultaneously
- Use larger language models
- Enable more aggressive caching
- Run additional services

## Quick Migration Option

If both Jetsons will be available:
1. Set up new Jetson with fresh OS
2. Mount the NVMe SSD on new Jetson
3. Run network migration script
4. Switch over when ready

## Troubleshooting

### Issue: Models not loading
- Check `/mnt/storage` is mounted
- Verify model paths in `.env`

### Issue: Database connection failed
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify password in `.env`

### Issue: GPIO/Hardware errors
- Update pin mappings for Orin NX
- Check `jetson-gpio` version compatibility

## After Migration

1. Update Jetson power mode:
   ```bash
   sudo nvpmodel -m 0  # Max performance
   ```

2. Test all components:
   ```bash
   python3 tests/test_voice_pipeline.py
   python3 tests/test_companion_mode_simple.py
   ```

3. Update any hardcoded IPs or hostnames