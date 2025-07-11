#!/usr/bin/env python3
"""
Download alternative Llama models that don't require authentication
"""

import os
import sys
import subprocess
from pathlib import Path
import requests
from tqdm import tqdm

def download_file(url: str, destination: Path, chunk_size: int = 8192):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destination, 'wb') as file:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=destination.name) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    pbar.update(len(chunk))

def main():
    print("=== Alternative Llama Model Download ===")
    print("\nAvailable models (no authentication required):")
    print("1. Llama 2 7B Chat (Q4_K_M) - 3.8GB - Good for Jetson")
    print("2. Mistral 7B Instruct (Q4_K_M) - 4.1GB - Excellent performance")
    print("3. TinyLlama 1.1B Chat (Q4_K_M) - 0.7GB - Very fast, lower quality")
    print("4. Phi-3 Mini 4k Instruct (Q4_K_M) - 2.2GB - Microsoft's efficient model")
    
    choice = input("\nSelect model (1-4) [default: 2]: ").strip() or "2"
    
    models = {
        "1": {
            "name": "Llama-2-7B-Chat",
            "file": "llama-2-7b-chat.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
            "size": "3.8GB"
        },
        "2": {
            "name": "Mistral-7B-Instruct", 
            "file": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "size": "4.1GB"
        },
        "3": {
            "name": "TinyLlama-1.1B-Chat",
            "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", 
            "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "size": "0.7GB"
        },
        "4": {
            "name": "Phi-3-mini-4k-instruct",
            "file": "Phi-3-mini-4k-instruct-q4.gguf",
            "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
            "size": "2.2GB"
        }
    }
    
    if choice not in models:
        print("Invalid choice, using Mistral")
        choice = "2"
    
    model_info = models[choice]
    model_dir = Path("/mnt/storage/models/llm")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / model_info["file"]
    
    if model_path.exists():
        print(f"\n✅ Model already exists at: {model_path}")
        overwrite = input("Download again? (y/N): ").strip().lower()
        if overwrite != 'y':
            return str(model_path)
    
    print(f"\nDownloading {model_info['name']} ({model_info['size']})...")
    print("This will take some time depending on your internet connection.\n")
    
    try:
        # Try wget first (more reliable for large files)
        cmd = ["wget", "-c", model_info["url"], "-O", str(model_path)]
        subprocess.run(cmd, check=True)
        print(f"\n✅ Model downloaded successfully to: {model_path}")
        
    except:
        print("wget failed, trying direct download...")
        try:
            download_file(model_info["url"], model_path)
            print(f"\n✅ Model downloaded successfully to: {model_path}")
        except Exception as e:
            print(f"\n❌ Error downloading model: {e}")
            print(f"\nYou can manually download from:")
            print(f"URL: {model_info['url']}")
            print(f"Save to: {model_path}")
            return None
    
    # Update environment configuration
    env_file = Path("/home/tutor/iseetutor/.env")
    if env_file.exists():
        # Update MODEL_PATH in .env
        lines = []
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('MODEL_PATH='):
                    lines.append(f'MODEL_PATH={model_path}\n')
                else:
                    lines.append(line)
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        print(f"Updated .env with new model path")
    
    return str(model_path)

if __name__ == "__main__":
    main()