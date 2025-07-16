# Quick Migration Steps - Jetson Orin Nano → Orin NX

## On Current Jetson (Before Shutdown):

1. **Create Backup** (5 minutes):
   ```bash
   cd /home/tutor/iseetutor
   sudo ./scripts/backup_for_migration.sh
   ```
   This creates a backup file: `~/iseetutor_migration_*.tar.gz`

2. **Copy Backup to USB** (if not using network):
   ```bash
   cp ~/iseetutor_migration_*.tar.gz /media/YOUR_USB_DRIVE/
   ```

3. **Note Your Configuration**:
   - Check SSD device: `lsblk | grep nvme`
   - Note any custom settings in `.env`

## On New Jetson Orin NX:

### Day 1 - Initial Setup (30 minutes):

1. **Flash JetPack OS** using NVIDIA SDK Manager

2. **Boot and Initial Config**:
   ```bash
   # Set hostname (optional)
   sudo hostnamectl set-hostname iseetutor-nx
   
   # Create user if needed
   sudo adduser tutor
   ```

3. **Transfer Files**:
   - Physically move NVMe SSD and flash drive to new Jetson
   - Or copy backup via network/USB

4. **Run Setup Script**:
   ```bash
   cd ~
   # Copy from backup or flash drive
   tar -xzf iseetutor_migration_*.tar.gz iseetutor/scripts/
   chmod +x iseetutor/scripts/*.sh
   
   # Run initial setup
   ./iseetutor/scripts/jetson_nx_setup.sh
   ```

5. **Mount Your SSD**:
   ```bash
   sudo ./iseetutor/scripts/mount_ssd.sh
   ```

6. **Restore Everything**:
   ```bash
   sudo ./iseetutor/scripts/restore_from_backup.sh
   ```

### Day 1 - Verification (10 minutes):

1. **Test Basic Functions**:
   ```bash
   cd ~/iseetutor
   python3 verify_setup.py
   ```

2. **Check Services**:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl status redis-server
   ```

3. **Test AI Models**:
   ```bash
   python3 tests/test_companion_mode_simple.py
   ```

4. **Start Application**:
   ```bash
   python3 start_api.py
   # In another terminal:
   cd frontend && npm start
   ```

## What Gets Migrated Automatically:

✅ **Via Backup Script**:
- All code from `/home/tutor/iseetutor/`
- Database with all user data
- Configuration files (`.env`)
- Python package list
- System service configs

✅ **Via Physical SSD Move**:
- AI models (4.5GB Llama)
- ChromaDB vector stores
- Educational content
- All data in `/mnt/storage/`

## Post-Migration Benefits with 16GB RAM:

1. **No More Memory Crashes!** 
2. **Run Everything Simultaneously**:
   - API server (3GB)
   - Frontend dev server (2GB)
   - LLM model (4.5GB)
   - Still have 6GB free!

3. **Future Upgrades**:
   - Try Llama 3.1 13B models
   - Run multiple models at once
   - Enable aggressive caching

## Troubleshooting:

**SSD Not Detected?**
```bash
sudo nvme list
lsblk
# Check power/cables
```

**Database Error?**
```bash
sudo -u postgres psql
\l  # List databases
\q
```

**Models Not Loading?**
```bash
ls -la /mnt/storage/models/llm/
# Check .env for correct paths
```

## Total Migration Time: ~45 minutes

Most of that is just waiting for OS install and file copies!