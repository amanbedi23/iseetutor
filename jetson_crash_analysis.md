# Jetson Nano Orin Crash Analysis

## Current System Status
- **Memory**: 7.4GB total (currently using ~1.5GB)
- **Swap**: 3.7GB zram (compressed RAM swap)
- **Power Mode**: 15W (lower than recommended 25W mode)
- **Temperature**: ~52-54°C (safe range)
- **Disk**: 233GB total, 14% used (plenty of space)

## Likely Crash Causes

### 1. **Memory Exhaustion (Most Likely)**
The ISEE Tutor app loads:
- Llama 3.1 8B model (~4.5GB)
- Whisper model (~140MB)
- ChromaDB embeddings
- Frontend React app
- Backend FastAPI server

**Total memory needed**: ~6-7GB minimum
**Available**: 7.4GB total (with OS using ~1.5GB)

This leaves very little headroom, especially in 15W power mode.

### 2. **Power Mode Throttling**
Currently in 15W mode, which may cause:
- CPU/GPU throttling under load
- Memory bandwidth limitations
- Sudden power drops causing system instability

### 3. **GPU Memory Pressure**
The Llama model uses GPU acceleration, which shares system memory on Jetson.

## Monitoring Instructions

1. **Start the monitors**:
   ```bash
   cd /home/tutor/iseetutor
   ./start_monitoring.sh
   ```

2. **Run your applications** in separate terminals:
   ```bash
   # Terminal 1 - Backend
   python3 start_api.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

3. **After a crash**, check the logs:
   ```bash
   ls -la /home/tutor/iseetutor/logs/monitoring/
   # View the latest logs
   tail -100 /home/tutor/iseetutor/logs/monitoring/system_monitor_*.log
   tail -100 /home/tutor/iseetutor/logs/monitoring/crash_monitor_*.log
   ```

## Immediate Recommendations

1. **Increase Power Mode** (before starting apps):
   ```bash
   sudo nvpmodel -m 1  # Switch to 25W mode
   ```

2. **Create a larger swap file**:
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   # Make permanent
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. **Optimize memory usage**:
   - Use smaller Whisper model (tiny instead of base)
   - Use quantized Llama model (Q4_K_M is good)
   - Limit ChromaDB cache size

4. **Monitor specific metrics**:
   - Watch for memory usage > 90%
   - Check for OOM killer messages
   - Monitor GPU memory usage
   - Watch for temperature spikes

The monitoring scripts will capture all this data before the crash, helping us identify the exact cause.