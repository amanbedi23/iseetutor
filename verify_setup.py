#!/usr/bin/env python3
"""
ISEE Tutor System Verification Script
Checks all components and dependencies
"""

import sys
import subprocess
import os
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(message, status):
    """Print colored status message"""
    if status == "OK":
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == "FAIL":
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == "WARN":
        print(f"{Colors.YELLOW}!{Colors.END} {message}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def check_system_info():
    """Display system information"""
    print(f"\n{Colors.BLUE}=== System Information ==={Colors.END}")
    
    # OS info
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('PRETTY_NAME'):
                    os_name = line.split('=')[1].strip().strip('"')
                    print_status(f"OS: {os_name}", "INFO")
    except:
        pass
    
    # Jetson info
    try:
        with open('/etc/nv_tegra_release') as f:
            jetson_info = f.readline().strip()
            print_status(f"Jetson: {jetson_info}", "INFO")
    except:
        print_status("Not running on Jetson", "WARN")
    
    # Python version
    python_version = sys.version.split()[0]
    print_status(f"Python: {python_version}", "INFO")

def check_storage():
    """Check storage setup"""
    print(f"\n{Colors.BLUE}=== Storage Configuration ==={Colors.END}")
    
    # Check SSD mount
    ssd_path = Path("/mnt/ssd")
    storage_path = Path("/mnt/storage")
    
    if ssd_path.exists():
        # Get disk usage
        result = subprocess.run(['df', '-h', '/mnt/ssd'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if '/mnt/ssd' in line:
                parts = line.split()
                size = parts[1]
                used = parts[2]
                avail = parts[3]
                print_status(f"SSD mounted: {size} total, {used} used, {avail} available", "OK")
    else:
        print_status("SSD not mounted at /mnt/ssd", "FAIL")
    
    # Check symlink
    if storage_path.is_symlink():
        target = os.readlink(storage_path)
        print_status(f"Storage symlink: /mnt/storage → {target}", "OK")
    else:
        print_status("Storage symlink not configured", "FAIL")
    
    # Check directories
    required_dirs = [
        "/mnt/storage/models",
        "/mnt/storage/knowledge",
        "/mnt/storage/content",
        "/mnt/storage/user_data"
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_status(f"Directory exists: {dir_path}", "OK")
        else:
            print_status(f"Directory missing: {dir_path}", "FAIL")

def check_databases():
    """Check database connections"""
    print(f"\n{Colors.BLUE}=== Database Status ==={Colors.END}")
    
    # PostgreSQL
    try:
        result = subprocess.run(['systemctl', 'is-active', 'postgresql'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print_status("PostgreSQL service: active", "OK")
            
            # Test connection
            import psycopg2
            try:
                conn = psycopg2.connect(
                    dbname="iseetutor_db",
                    user="iseetutor",
                    password="iseetutor123",
                    host="localhost"
                )
                conn.close()
                print_status("PostgreSQL connection: successful", "OK")
            except Exception as e:
                print_status(f"PostgreSQL connection failed: {str(e)}", "FAIL")
        else:
            print_status("PostgreSQL service: not running", "FAIL")
    except:
        print_status("PostgreSQL not installed", "FAIL")
    
    # Redis
    try:
        result = subprocess.run(['systemctl', 'is-active', 'redis-server'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print_status("Redis service: active", "OK")
            
            # Test connection
            import redis
            try:
                r = redis.Redis(host='localhost', port=6379)
                r.ping()
                print_status("Redis connection: successful", "OK")
            except:
                print_status("Redis connection failed", "FAIL")
        else:
            print_status("Redis service: not running", "FAIL")
    except:
        print_status("Redis not installed", "FAIL")

def check_python_packages():
    """Check required Python packages"""
    print(f"\n{Colors.BLUE}=== Python Packages ==={Colors.END}")
    
    packages = {
        # Core
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "sqlalchemy": "Database ORM",
        "redis": "Redis client",
        "psycopg2": "PostgreSQL adapter",
        
        # AI/ML
        "torch": "PyTorch",
        "langchain": "LangChain",
        "transformers": "Hugging Face Transformers",
        "whisper": "OpenAI Whisper",
        "chromadb": "Vector database",
        "llama_cpp": "Llama.cpp Python",
        
        # Utils
        "numpy": "NumPy",
        "pandas": "Pandas",
        "pydantic": "Data validation",
    }
    
    for package, description in packages.items():
        try:
            __import__(package)
            print_status(f"{description} ({package})", "OK")
            
            # Special check for PyTorch CUDA
            if package == "torch":
                import torch
                cuda_status = "available" if torch.cuda.is_available() else "not available"
                cuda_color = "OK" if torch.cuda.is_available() else "WARN"
                print_status(f"  PyTorch {torch.__version__}, CUDA {cuda_status}", cuda_color)
                
        except ImportError:
            print_status(f"{description} ({package})", "FAIL")

def check_models():
    """Check for downloaded models"""
    print(f"\n{Colors.BLUE}=== AI Models ==={Colors.END}")
    
    # Check for Llama model
    llama_models = list(Path("/mnt/storage/models/llm").glob("*.gguf")) if Path("/mnt/storage/models/llm").exists() else []
    
    if llama_models:
        for model in llama_models:
            size = model.stat().st_size / (1024**3)  # GB
            print_status(f"Llama model: {model.name} ({size:.1f} GB)", "OK")
    else:
        print_status("No Llama models found in /mnt/storage/models/llm/", "WARN")
    
    # Check for Whisper model
    whisper_path = Path("/mnt/storage/models/whisper")
    if whisper_path.exists() and any(whisper_path.iterdir()):
        print_status("Whisper models found", "OK")
    else:
        print_status("No Whisper models found", "WARN")

def check_api():
    """Check if API can start"""
    print(f"\n{Colors.BLUE}=== API Status ==={Colors.END}")
    
    # Check if API module exists
    api_path = Path("src/api/main.py")
    if api_path.exists():
        print_status("API module found", "OK")
        
        # Try to import
        try:
            sys.path.insert(0, str(Path.cwd()))
            from src.api.main import app
            print_status("API module imports successfully", "OK")
        except Exception as e:
            print_status(f"API import error: {str(e)}", "FAIL")
    else:
        print_status("API module not found", "FAIL")

def check_knowledge_bases():
    """Check knowledge databases"""
    print(f"\n{Colors.BLUE}=== Knowledge Bases ==={Colors.END}")
    
    kb_path = Path("/mnt/storage/knowledge/databases")
    if kb_path.exists():
        dbs = list(kb_path.glob("*.db"))
        if dbs:
            for db in dbs:
                size = db.stat().st_size / (1024**2)  # MB
                print_status(f"Knowledge DB: {db.name} ({size:.1f} MB)", "OK")
        else:
            print_status("No knowledge databases found", "WARN")
    else:
        print_status("Knowledge database directory not found", "FAIL")

def main():
    """Run all checks"""
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}ISEE Tutor System Verification{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    
    check_system_info()
    check_storage()
    check_databases()
    check_python_packages()
    check_models()
    check_knowledge_bases()
    check_api()
    
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}Verification Complete{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")
    
    print("\nNext steps:")
    print("1. If any components show FAIL, address those issues")
    print("2. Download models if not present: python3 scripts/download_llama_model.py")
    print("3. Start the API: python3 start_api.py")
    print("4. Access the API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()