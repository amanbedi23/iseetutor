#!/usr/bin/env python3
"""
Optimized API startup script for Jetson
Prevents system hangs by managing resources carefully
"""

import os
import sys
import time
import subprocess
import psutil

def set_process_limits():
    """Set resource limits to prevent system overload"""
    import resource
    
    # Limit CPU time (soft, hard) in seconds
    resource.setrlimit(resource.RLIMIT_CPU, (300, 600))  # 5-10 minutes
    
    # Limit memory usage to 2GB
    memory_limit = 2 * 1024 * 1024 * 1024  # 2GB in bytes
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    
    # Limit number of open files
    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 2048))

def check_system_resources():
    """Check if system has enough resources to start"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"System Check:")
    print(f"  CPU Usage: {cpu_percent}%")
    print(f"  Memory: {memory.percent}% ({memory.available/1024/1024/1024:.1f}GB available)")
    
    if memory.percent > 85:
        print("⚠️  WARNING: High memory usage detected!")
        print("   Consider closing other applications before starting.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    if cpu_percent > 80:
        print("⚠️  WARNING: High CPU usage detected!")
        print("   Waiting for CPU to settle...")
        time.sleep(5)

def kill_existing_processes():
    """Kill any existing API server processes"""
    subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
    subprocess.run(["pkill", "-f", "start_api"], capture_output=True)
    time.sleep(1)

def optimize_jetson_settings():
    """Optimize Jetson settings for better performance"""
    print("Optimizing Jetson settings...")
    
    # Set CPU governor to performance (requires sudo)
    try:
        for i in range(6):  # Jetson has 6 CPU cores
            with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor", "w") as f:
                f.write("performance")
    except:
        print("  Could not set CPU governor (requires sudo)")
    
    # Disable unnecessary services temporarily
    print("  Disabling unnecessary services...")
    subprocess.run(["systemctl", "--user", "stop", "tracker-miner-fs-3.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "stop", "tracker-extract-3.service"], capture_output=True)

def start_api_server():
    """Start the API server with resource limits"""
    print("\nStarting API server with optimizations...")
    
    # Environment variables for optimization
    env = os.environ.copy()
    env.update({
        'PYTHONUNBUFFERED': '1',
        'OMP_NUM_THREADS': '2',  # Limit OpenMP threads
        'MKL_NUM_THREADS': '2',   # Limit MKL threads
        'NUMEXPR_NUM_THREADS': '2',  # Limit NumExpr threads
        'UVICORN_WORKERS': '1',   # Single worker to reduce memory
        'UVICORN_LIMIT_MAX_REQUESTS': '1000',  # Restart worker after N requests
    })
    
    # Command with specific settings
    cmd = [
        sys.executable, '-u',
        '-m', 'uvicorn',
        'src.api.main:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload',
        '--reload-dir', 'src',
        '--limit-concurrency', '10',  # Limit concurrent connections
        '--timeout-keep-alive', '5',   # Shorter keepalive
        '--log-level', 'info'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("\nAPI server starting...")
    print("Access at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop")
    
    try:
        # Start with resource limits
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        print("Cleaning up...")
        subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)

def main():
    print("ISEE Tutor API - Optimized Startup for Jetson")
    print("=" * 50)
    
    # Check if running on Jetson
    is_jetson = os.path.exists("/etc/nv_tegra_release")
    if is_jetson:
        print("✓ Running on NVIDIA Jetson")
    else:
        print("ℹ️  Not running on Jetson - some optimizations disabled")
    
    # Pre-flight checks
    check_system_resources()
    kill_existing_processes()
    
    if is_jetson:
        optimize_jetson_settings()
    
    # Set resource limits
    try:
        set_process_limits()
        print("✓ Resource limits set")
    except:
        print("ℹ️  Could not set all resource limits")
    
    # Start server
    start_api_server()

if __name__ == "__main__":
    main()