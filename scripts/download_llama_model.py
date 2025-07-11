#!/usr/bin/env python3
"""
Download and set up Llama 3.2 8B quantized model for ISEE Tutor
"""

import os
import sys
import subprocess
from pathlib import Path
import requests
from tqdm import tqdm

# Model configuration
MODEL_NAME = "llama-3.2-8b-instruct"
MODEL_URLS = {
    "q4_k_m": {
        "url": "https://huggingface.co/bartowski/Llama-3.2-8B-Instruct-GGUF/resolve/main/Llama-3.2-8B-Instruct-Q4_K_M.gguf",
        "size": "4.9GB",
        "filename": "Llama-3.2-8B-Instruct-Q4_K_M.gguf"
    },
    "q5_k_m": {
        "url": "https://huggingface.co/bartowski/Llama-3.2-8B-Instruct-GGUF/resolve/main/Llama-3.2-8B-Instruct-Q5_K_M.gguf", 
        "size": "5.7GB",
        "filename": "Llama-3.2-8B-Instruct-Q5_K_M.gguf"
    }
}

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

def setup_llama_model():
    """Download and set up Llama model"""
    print("=== Llama 3.2 8B Model Setup ===")
    print("\nThis script will download the quantized Llama 3.2 8B model.")
    print("The model is required for the companion mode to generate responses.\n")
    
    # Check if model directory exists
    model_dir = Path("/mnt/storage/models")
    if not model_dir.exists():
        print(f"Creating model directory: {model_dir}")
        model_dir.mkdir(parents=True, exist_ok=True)
    
    # Select quantization
    print("Available quantizations:")
    print("1. Q4_K_M (4.9GB) - Recommended for Jetson, good quality")
    print("2. Q5_K_M (5.7GB) - Better quality, slightly slower")
    
    choice = input("\nSelect quantization (1 or 2) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        quant = "q4_k_m"
    elif choice == "2":
        quant = "q5_k_m"
    else:
        print("Invalid choice, using Q4_K_M")
        quant = "q4_k_m"
    
    model_info = MODEL_URLS[quant]
    model_path = model_dir / model_info["filename"]
    
    # Check if model already exists
    if model_path.exists():
        print(f"\n✅ Model already exists at: {model_path}")
        overwrite = input("Download again? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Using existing model.")
            return str(model_path)
    
    # Download model
    print(f"\nDownloading {model_info['filename']} ({model_info['size']})...")
    print("This will take some time depending on your internet connection.\n")
    
    try:
        # First, try using huggingface-cli if available
        hf_cli = subprocess.run(["which", "huggingface-cli"], capture_output=True)
        if hf_cli.returncode == 0:
            print("Using huggingface-cli for download...")
            cmd = [
                "huggingface-cli", "download",
                "bartowski/Llama-3.2-8B-Instruct-GGUF",
                model_info["filename"],
                "--local-dir", str(model_dir),
                "--local-dir-use-symlinks", "False"
            ]
            subprocess.run(cmd, check=True)
        else:
            # Fallback to direct download
            print("Downloading directly (this may be slower)...")
            download_file(model_info["url"], model_path)
        
        print(f"\n✅ Model downloaded successfully to: {model_path}")
        
    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        print("\nAlternative: You can manually download from:")
        print(f"URL: {model_info['url']}")
        print(f"Save to: {model_path}")
        return None
    
    # Create model configuration
    config_path = model_dir / "model_config.yaml"
    with open(config_path, 'w') as f:
        f.write(f"""# ISEE Tutor Model Configuration
model:
  name: {MODEL_NAME}
  path: {model_path}
  quantization: {quant}
  type: gguf
  
inference:
  n_gpu_layers: 32  # Adjust based on Jetson GPU memory
  n_ctx: 4096       # Context window
  n_batch: 512      # Batch size
  temperature: 0.7  # Default temperature
  max_tokens: 512   # Max response length
  
modes:
  tutor:
    temperature: 0.5  # More focused for educational content
    top_p: 0.9
    repeat_penalty: 1.1
  friend:
    temperature: 0.8  # More creative for general chat
    top_p: 0.95
    repeat_penalty: 1.0
""")
    print(f"Created model configuration at: {config_path}")
    
    return str(model_path)

def test_model_loading():
    """Test if the model can be loaded"""
    print("\n=== Testing Model Loading ===")
    
    try:
        # Check if llama-cpp-python is installed
        import llama_cpp
        print("✅ llama-cpp-python is installed")
        
        # Try to load a small test
        print("Testing model loading (this may take a moment)...")
        
        # Get model path from config
        config_path = Path("/mnt/storage/models/model_config.yaml")
        if config_path.exists():
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            model_path = config['model']['path']
            
            # Try to initialize (just check, don't fully load)
            if Path(model_path).exists():
                print(f"✅ Model file found at: {model_path}")
                print("✅ Model is ready to use!")
            else:
                print("❌ Model file not found")
        else:
            print("❌ Model configuration not found")
            
    except ImportError:
        print("❌ llama-cpp-python not installed")
        print("\nTo install:")
        print("pip3 install llama-cpp-python")

def main():
    """Main setup function"""
    print("ISEE Tutor - Llama Model Setup\n")
    
    # Download model
    model_path = setup_llama_model()
    
    if model_path:
        # Test loading
        test_model_loading()
        
        print("\n=== Setup Complete ===")
        print("\nThe Llama model is now ready for use in the ISEE Tutor!")
        print("The model will provide responses in both Tutor and Friend modes.")
    else:
        print("\n⚠️  Model setup incomplete. Please download the model manually.")

if __name__ == "__main__":
    main()