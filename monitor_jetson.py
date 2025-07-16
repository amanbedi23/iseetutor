#!/usr/bin/env python3
"""
Jetson Monitoring Script
Monitors system resources and logs when testing frontend/backend
"""

import subprocess
import time
import psutil
import os
import signal
import sys
from datetime import datetime

LOG_FILE = "jetson_monitor.log"
MONITOR_INTERVAL = 2  # seconds

def signal_handler(sig, frame):
    print('\nMonitoring stopped.')
    sys.exit(0)

def get_tegrastats():
    """Get current stats from tegrastats"""
    try:
        result = subprocess.run(['tegrastats', '--interval', '1000'], 
                              capture_output=True, text=True, timeout=1)
        if result.stdout:
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    return None

def get_process_info():
    """Get info about resource-intensive processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            pinfo = proc.info
            if pinfo['cpu_percent'] > 20 or pinfo['memory_info'].rss > 500 * 1024 * 1024:  # 500MB
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'],
                    'memory_mb': pinfo['memory_info'].rss / 1024 / 1024
                })
        except:
            pass
    return sorted(processes, key=lambda x: x['cpu'], reverse=True)[:5]

def monitor():
    """Main monitoring loop"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"Starting Jetson monitoring... (Ctrl+C to stop)")
    print(f"Logging to {LOG_FILE}")
    
    with open(LOG_FILE, 'w') as log:
        log.write(f"Jetson Monitoring Started: {datetime.now()}\n")
        log.write("=" * 80 + "\n\n")
        
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # System stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Tegrastats
            tegra_info = get_tegrastats()
            
            # Top processes
            top_procs = get_process_info()
            
            # Log entry
            log_entry = f"\n[{timestamp}]\n"
            log_entry += f"CPU: {cpu_percent}% | Memory: {memory.percent}% ({memory.used/1024/1024/1024:.1f}GB/{memory.total/1024/1024/1024:.1f}GB)\n"
            
            if tegra_info:
                log_entry += f"Tegrastats: {tegra_info}\n"
            
            if top_procs:
                log_entry += "Top Processes:\n"
                for proc in top_procs:
                    log_entry += f"  - {proc['name']} (PID: {proc['pid']}): CPU {proc['cpu']:.1f}%, Memory {proc['memory_mb']:.0f}MB\n"
            
            # Check for critical conditions
            if cpu_percent > 90:
                log_entry += "⚠️  WARNING: CPU usage critical!\n"
            if memory.percent > 90:
                log_entry += "⚠️  WARNING: Memory usage critical!\n"
            
            # Write to log and print summary
            log.write(log_entry)
            log.flush()
            
            print(f"\r[{timestamp}] CPU: {cpu_percent}%  Memory: {memory.percent}%  ", end='')
            
            time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    monitor()