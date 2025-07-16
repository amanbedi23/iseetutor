# Jetson Hang Diagnosis and Solutions

## Problem Summary
Your Jetson is hanging and restarting when testing frontend and backend together.

## Likely Causes

### 1. **Memory Exhaustion** (Most Likely)
- Running both frontend (Node.js) and backend (Python/FastAPI) simultaneously
- Large language models loading into memory
- Multiple VS Code server processes consuming resources

### 2. **Power Issues**
- Insufficient power supply for peak loads
- Running in low power mode (25W instead of MAXN)

### 3. **Thermal Throttling**
- Temperature reaching ~51°C under load
- Could cause sudden shutdowns if it spikes

## Solutions

### Immediate Actions

1. **Use the monitoring script**:
   ```bash
   ./test_with_monitoring.sh
   ```
   This will log system resources during testing to identify the exact failure point.

2. **Start services with optimization**:
   ```bash
   # Instead of: python3 start_api.py
   python3 start_api_optimized.py
   ```

3. **Use Jetson-specific environment**:
   ```bash
   # Copy optimized settings
   cp .env.jetson .env
   
   # Or source it temporarily
   export $(cat .env.jetson | xargs)
   ```

### System Optimizations

1. **Increase swap space**:
   ```bash
   sudo swapoff -a
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

2. **Set maximum performance mode**:
   ```bash
   sudo nvpmodel -m 0  # MAXN mode
   sudo jetson_clocks  # Lock clocks to maximum
   ```

3. **Disable unnecessary services**:
   ```bash
   # Disable GNOME tracker
   systemctl --user mask tracker-miner-fs-3.service
   systemctl --user mask tracker-extract-3.service
   
   # Stop VS Code if not needed
   pkill -f vscode-server
   ```

### Development Workflow

1. **Test components separately**:
   ```bash
   # Terminal 1: Backend only
   python3 start_api_optimized.py
   
   # Terminal 2: Test API without frontend
   curl http://localhost:8000/health
   
   # Terminal 3: Frontend only (after backend is stable)
   cd frontend && npm run dev
   ```

2. **Use lighter models for testing**:
   - Whisper: Use "tiny" instead of "base"
   - LLM: Use smaller quantized models
   - Disable features not being tested

3. **Monitor during startup**:
   ```bash
   # Watch memory usage
   watch -n 1 free -h
   
   # Watch processes
   htop
   
   # Watch Jetson stats
   tegrastats
   ```

### Hardware Recommendations

1. **Power Supply**: Ensure using the official 65W adapter
2. **Cooling**: Add a fan if not already present
3. **Storage**: Use NVMe SSD for swap (already configured at /mnt/storage)

## Testing Protocol

1. Start monitoring: `./test_with_monitoring.sh`
2. Start backend: `python3 start_api_optimized.py`
3. Wait for full initialization
4. Check memory usage
5. Start frontend: `cd frontend && npm run dev`
6. Test gradually, checking logs

## If Still Hanging

1. Check `jetson_monitor.log` for resource spikes
2. Look for kernel panics: `sudo dmesg -T | grep -i panic`
3. Check for OOM killer: `sudo dmesg -T | grep -i "killed process"`
4. Test with minimal configuration (.env.jetson)

The optimized startup script and monitoring tools should help identify and prevent the hangs.