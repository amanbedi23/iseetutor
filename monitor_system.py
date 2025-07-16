#!/usr/bin/env python3
"""
System monitoring script to diagnose Jetson Nano Orin crashes
Logs CPU, memory, GPU, temperature, and process information
"""

import psutil
import subprocess
import time
import datetime
import os
import signal
import sys
from pathlib import Path

# Configuration
LOG_DIR = Path("/home/tutor/iseetutor/logs/monitoring")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"system_monitor_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
MONITOR_INTERVAL = 1  # seconds
CRITICAL_TEMP = 80  # Celsius
CRITICAL_MEM_PERCENT = 90
CRITICAL_CPU_PERCENT = 95

# Track high resource processes
HIGH_CPU_THRESHOLD = 50
HIGH_MEM_THRESHOLD = 10  # percent

running = True

def signal_handler(sig, frame):
    global running
    running = False
    log_message("\n=== Monitoring stopped by user ===")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def log_message(message):
    """Log message to both file and console"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, 'a') as f:
        f.write(full_message + '\n')

def get_jetson_stats():
    """Get Jetson-specific stats using tegrastats"""
    stats = {}
    try:
        # Get temperature
        temp_zones = Path("/sys/devices/virtual/thermal/").glob("thermal_zone*/temp")
        temps = []
        for zone in temp_zones:
            try:
                temp = int(zone.read_text().strip()) / 1000.0
                temps.append(temp)
            except:
                pass
        stats['temps'] = temps
        stats['max_temp'] = max(temps) if temps else 0
        
        # Get GPU usage using nvidia-smi if available
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                gpu_util, mem_used, mem_total = result.stdout.strip().split(', ')
                stats['gpu_util'] = float(gpu_util)
                stats['gpu_mem_used'] = float(mem_used)
                stats['gpu_mem_total'] = float(mem_total)
                stats['gpu_mem_percent'] = (float(mem_used) / float(mem_total)) * 100
        except:
            # Try tegrastats as fallback
            try:
                result = subprocess.run(['tegrastats', '--interval', '1000'], 
                                      capture_output=True, text=True, timeout=1)
                # Parse tegrastats output if needed
            except:
                pass
                
        # Get power mode
        try:
            result = subprocess.run(['nvpmodel', '-q'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'NV Power Mode:' in line:
                        stats['power_mode'] = line.split(':')[1].strip()
        except:
            pass
            
    except Exception as e:
        log_message(f"Error getting Jetson stats: {e}")
    
    return stats

def get_top_processes():
    """Get top CPU and memory consuming processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
        try:
            info = proc.info
            if info['cpu_percent'] > HIGH_CPU_THRESHOLD or info['memory_percent'] > HIGH_MEM_THRESHOLD:
                cmd = ' '.join(info['cmdline'][:3]) if info['cmdline'] else info['name']
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'cmd': cmd,
                    'cpu': info['cpu_percent'],
                    'mem': info['memory_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return sorted(processes, key=lambda x: x['cpu'] + x['mem'], reverse=True)[:5]

def check_critical_conditions(cpu_percent, mem_percent, jetson_stats):
    """Check for critical conditions that might cause a crash"""
    warnings = []
    
    if cpu_percent > CRITICAL_CPU_PERCENT:
        warnings.append(f"CRITICAL: CPU usage at {cpu_percent:.1f}%")
    
    if mem_percent > CRITICAL_MEM_PERCENT:
        warnings.append(f"CRITICAL: Memory usage at {mem_percent:.1f}%")
    
    if 'max_temp' in jetson_stats and jetson_stats['max_temp'] > CRITICAL_TEMP:
        warnings.append(f"CRITICAL: Temperature at {jetson_stats['max_temp']:.1f}°C")
    
    if 'gpu_mem_percent' in jetson_stats and jetson_stats['gpu_mem_percent'] > 90:
        warnings.append(f"CRITICAL: GPU memory at {jetson_stats['gpu_mem_percent']:.1f}%")
    
    return warnings

def monitor_system():
    """Main monitoring loop"""
    log_message("=== System Monitoring Started ===")
    log_message(f"Logging to: {LOG_FILE}")
    log_message(f"Monitoring interval: {MONITOR_INTERVAL}s")
    log_message(f"Critical thresholds - CPU: {CRITICAL_CPU_PERCENT}%, Memory: {CRITICAL_MEM_PERCENT}%, Temp: {CRITICAL_TEMP}°C")
    
    # Initial system info
    log_message(f"\nSystem Info:")
    log_message(f"CPU Count: {psutil.cpu_count()}")
    log_message(f"Total Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    # Get initial disk usage
    disk = psutil.disk_usage('/')
    log_message(f"Disk Usage: {disk.percent}% ({disk.used / (1024**3):.1f}/{disk.total / (1024**3):.1f} GB)")
    
    log_message("\n=== Starting Continuous Monitoring ===\n")
    
    iteration = 0
    while running:
        try:
            iteration += 1
            
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Get Jetson-specific stats
            jetson_stats = get_jetson_stats()
            
            # Log summary every iteration
            summary = f"CPU: {cpu_percent:5.1f}% | RAM: {mem.percent:5.1f}% ({mem.used/(1024**3):.1f}/{mem.total/(1024**3):.1f}GB) | Swap: {swap.percent:5.1f}%"
            
            if 'max_temp' in jetson_stats:
                summary += f" | Temp: {jetson_stats['max_temp']:.1f}°C"
            
            if 'gpu_util' in jetson_stats:
                summary += f" | GPU: {jetson_stats['gpu_util']:.0f}%"
            
            if 'gpu_mem_percent' in jetson_stats:
                summary += f" | GPU Mem: {jetson_stats['gpu_mem_percent']:.1f}%"
            
            log_message(summary)
            
            # Check critical conditions
            warnings = check_critical_conditions(cpu_percent, mem.percent, jetson_stats)
            for warning in warnings:
                log_message(f"⚠️  {warning}")
            
            # Log detailed info every 10 iterations
            if iteration % 10 == 0:
                log_message("\n--- Detailed Report ---")
                
                # Per-core CPU usage
                log_message(f"CPU per core: {[f'{c:.1f}%' for c in cpu_per_core]}")
                
                # Top processes
                top_procs = get_top_processes()
                if top_procs:
                    log_message("\nTop Resource Consumers:")
                    for proc in top_procs:
                        log_message(f"  PID {proc['pid']:6} | CPU: {proc['cpu']:5.1f}% | MEM: {proc['mem']:5.1f}% | {proc['cmd']}")
                
                # Network connections (check for too many connections)
                connections = len(psutil.net_connections())
                log_message(f"\nNetwork connections: {connections}")
                
                # Check for zombie processes
                zombies = [p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_ZOMBIE]
                if zombies:
                    log_message(f"⚠️  Zombie processes: {len(zombies)}")
                
                log_message("--- End Report ---\n")
            
            # Check for iseetutor processes
            if iteration % 5 == 0:
                isee_procs = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if 'iseetutor' in cmdline or 'node' in proc.info['name'] or 'python' in proc.info['name']:
                            if 'iseetutor' in cmdline or any(x in cmdline for x in ['frontend', 'api', 'src']):
                                isee_procs.append(proc)
                    except:
                        pass
                
                if isee_procs:
                    log_message("\nISEE Tutor Processes:")
                    for proc in isee_procs:
                        try:
                            cpu = proc.cpu_percent(interval=0.1)
                            mem = proc.memory_info().rss / (1024**2)  # MB
                            cmd = ' '.join(proc.cmdline()[:5]) if proc.cmdline() else proc.name()
                            log_message(f"  PID {proc.pid} | CPU: {cpu:.1f}% | MEM: {mem:.0f}MB | {cmd}")
                        except:
                            pass
            
            time.sleep(MONITOR_INTERVAL)
            
        except Exception as e:
            log_message(f"Error in monitoring loop: {e}")
            time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    try:
        monitor_system()
    except KeyboardInterrupt:
        log_message("\n=== Monitoring stopped by user ===")
    except Exception as e:
        log_message(f"\n=== Monitoring crashed: {e} ===")