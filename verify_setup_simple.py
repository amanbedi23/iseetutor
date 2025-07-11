#!/usr/bin/env python3
"""
Simple verification script without pandas dependency
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

print(f"{Colors.BLUE}{'='*50}{Colors.END}")
print(f"{Colors.BLUE}ISEE Tutor Quick Status Check{Colors.END}")
print(f"{Colors.BLUE}{'='*50}{Colors.END}")

# Check critical components
print(f"\n{Colors.BLUE}=== Critical Components ==={Colors.END}")

# PyTorch with CUDA
try:
    import torch
    cuda_status = "available" if torch.cuda.is_available() else "not available"
    print_status(f"PyTorch {torch.__version__} - CUDA {cuda_status}", "OK" if torch.cuda.is_available() else "FAIL")
    if torch.cuda.is_available():
        print_status(f"  GPU: {torch.cuda.get_device_name(0)}", "INFO")
except ImportError:
    print_status("PyTorch not installed", "FAIL")

# Llama-cpp-python
try:
    import llama_cpp
    print_status("llama-cpp-python installed", "OK")
except ImportError:
    print_status("llama-cpp-python not installed", "FAIL")

# LangChain
try:
    import langchain
    print_status(f"LangChain {langchain.__version__}", "OK")
except ImportError:
    print_status("LangChain not installed", "FAIL")

# Transformers
try:
    import transformers
    print_status(f"Transformers {transformers.__version__}", "OK")
except ImportError:
    print_status("Transformers not installed", "FAIL")

# Check models
print(f"\n{Colors.BLUE}=== Model Status ==={Colors.END}")
llama_path = Path("/mnt/storage/models/llm")
if llama_path.exists():
    models = list(llama_path.glob("*.gguf"))
    if models:
        for model in models:
            size_gb = model.stat().st_size / (1024**3)
            print_status(f"Model found: {model.name} ({size_gb:.1f} GB)", "OK")
    else:
        print_status("No Llama models found - run: python3 scripts/download_llama_model.py", "WARN")
else:
    print_status("Model directory not found", "WARN")

# Check databases
print(f"\n{Colors.BLUE}=== Database Status ==={Colors.END}")
try:
    import psycopg2
    import redis
    
    # Test PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname="iseetutor_db",
            user="iseetutor",
            password="iseetutor123",
            host="localhost"
        )
        conn.close()
        print_status("PostgreSQL connection OK", "OK")
    except:
        print_status("PostgreSQL connection failed", "FAIL")
    
    # Test Redis
    try:
        r = redis.Redis()
        r.ping()
        print_status("Redis connection OK", "OK")
    except:
        print_status("Redis connection failed", "FAIL")
except ImportError:
    print_status("Database packages not installed", "FAIL")

print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
print("\nNext steps:")
print("1. If models not found: python3 scripts/download_llama_model.py")
print("2. Start the API: python3 start_api.py")
print("3. Access at: http://localhost:8000/docs")