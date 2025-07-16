#!/bin/bash
# Optimized LLM startup for Jetson

echo "Setting up Jetson for optimal LLM performance..."

# Request sudo for system optimizations
if [ "$EUID" -ne 0 ]; then 
    echo "Some optimizations require sudo. Run with: sudo $0"
    echo "Continuing with user-level optimizations..."
fi

# Set environment variables for GPU usage
export CUDA_VISIBLE_DEVICES=0
export LLAMA_CUDA=1
export GGML_CUDA_NO_PINNED=1  # Use pinned memory carefully on Jetson

# Optimize system if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Setting maximum performance mode..."
    nvpmodel -m 0  # MAXN mode
    jetson_clocks  # Lock clocks to maximum
    
    echo "Setting CPU governor to performance..."
    for i in {0..5}; do
        echo performance > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor
    done
    
    echo "Increasing GPU memory allocation..."
    echo 536870912 > /sys/kernel/debug/nvmap/iovmm/maps/max_size 2>/dev/null || true
fi

# Kill unnecessary processes
echo "Stopping unnecessary services..."
pkill -f tracker-miner
pkill -f tracker-extract
systemctl --user stop gvfs-udisks2-volume-monitor.service 2>/dev/null || true

# Clear cache
echo "Clearing system caches..."
sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

# Check available memory
free -h

echo "Jetson optimized for LLM. Starting API server..."
cd /home/tutor/iseetutor

# Use optimized Python settings
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

# Start with GPU acceleration
python3 -u start_api.py
