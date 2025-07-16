#!/usr/bin/env python3
"""
Optimize LLM settings for Jetson Orin Nano
"""

import os
import subprocess
import json

def check_jetson_status():
    """Check current Jetson configuration"""
    print("Checking Jetson configuration...")
    
    # Check power mode
    try:
        result = subprocess.run(['nvpmodel', '-q'], capture_output=True, text=True)
        print(f"Power mode: {result.stdout.strip()}")
    except:
        print("Could not check power mode (needs sudo)")
    
    # Check if jetson_clocks is active
    try:
        result = subprocess.run(['jetson_clocks', '--show'], capture_output=True, text=True)
        print(f"Jetson clocks: {'Active' if result.returncode == 0 else 'Not active'}")
    except:
        pass

def create_optimized_config():
    """Create optimized LLM configuration"""
    
    config = {
        "model_config": {
            "model_path": "/mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "n_ctx": 2048,  # Context window
            "n_batch": 512,  # Batch size
            "n_threads": 4,  # CPU threads (Jetson has 6 cores)
            "n_gpu_layers": 35,  # Offload layers to GPU (adjust based on testing)
            "use_mlock": True,  # Lock model in RAM
            "use_mmap": True,  # Memory-map the model
            "offload_kqv": True,  # Offload KQV to GPU
            "f16_kv": True,  # Use half precision for key/value cache
            "low_vram": False,  # Jetson has unified memory
            "main_gpu": 0,
            "tensor_split": None,
            "rope_freq_base": 10000.0,
            "rope_freq_scale": 1.0,
            "verbose": False
        },
        "generation_config": {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "stop": ["</s>", "[INST]", "[/INST]"]
        }
    }
    
    with open('llm_config_optimized.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Created llm_config_optimized.json")
    return config

def create_startup_script():
    """Create optimized startup script for LLM"""
    
    script = '''#!/bin/bash
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
'''
    
    with open('start_llm_optimized.sh', 'w') as f:
        f.write(script)
    
    os.chmod('start_llm_optimized.sh', 0o755)
    print("Created start_llm_optimized.sh")

def create_test_script():
    """Create script to test LLM performance"""
    
    script = '''#!/usr/bin/env python3
import time
import psutil
import GPUtil
from llama_cpp import Llama

print("Testing LLM on Jetson...")

# Monitor resources
start_memory = psutil.virtual_memory().used / 1024 / 1024 / 1024

# Load model with GPU
print("Loading model with GPU acceleration...")
start_time = time.time()

llm = Llama(
    model_path="/mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    n_ctx=2048,
    n_batch=512,
    n_threads=4,
    n_gpu_layers=35,  # Adjust this value
    use_mlock=True,
    verbose=True
)

load_time = time.time() - start_time
print(f"\\nModel loaded in {load_time:.2f} seconds")

# Check memory usage
current_memory = psutil.virtual_memory().used / 1024 / 1024 / 1024
print(f"Memory used: {current_memory - start_memory:.2f} GB")

# Test inference
print("\\nTesting inference...")
start_time = time.time()

response = llm(
    "Explain photosynthesis to a 10-year-old in 2 sentences.",
    max_tokens=100,
    temperature=0.7,
    stop=["\\n\\n"]
)

inference_time = time.time() - start_time
print(f"\\nInference time: {inference_time:.2f} seconds")
print(f"Response: {response['choices'][0]['text']}")

# Calculate tokens per second
token_count = response['usage']['completion_tokens']
print(f"\\nTokens per second: {token_count / inference_time:.2f}")
'''
    
    with open('test_llm_performance.py', 'w') as f:
        f.write(script)
    
    print("Created test_llm_performance.py")

def main():
    print("Jetson LLM Optimization Setup")
    print("=" * 50)
    
    check_jetson_status()
    print()
    
    create_optimized_config()
    create_startup_script()
    create_test_script()
    
    print("\nOptimization files created!")
    print("\nNext steps:")
    print("1. Run with sudo for full optimization: sudo ./start_llm_optimized.sh")
    print("2. Or test LLM performance: python3 test_llm_performance.py")
    print("3. Monitor with: tegrastats")
    print("\nThe key is using GPU acceleration (n_gpu_layers) to offload work from CPU/RAM to GPU.")

if __name__ == "__main__":
    main()