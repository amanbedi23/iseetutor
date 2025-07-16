#!/usr/bin/env python3
"""
Download Piper TTS voice models for ISEE Tutor
"""

import os
import sys
import requests
import tarfile
from pathlib import Path
import json

def download_file(url, dest_path):
    """Download file with progress indicator"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
    
    print("\nDownload complete!")

def download_piper_voice(voice_name="en_US-amy-medium", model_dir=None):
    """Download Piper voice model"""
    
    if model_dir is None:
        model_dir = Path("/mnt/storage/models/tts")
    else:
        model_dir = Path(model_dir)
    
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Piper model URLs (updated for correct release)
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    
    # Voice configurations
    voices = {
        "en_US-amy-medium": {
            "model": f"{base_url}/en/en_US/amy/medium/en_US-amy-medium.onnx",
            "config": f"{base_url}/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
            "quality": "medium",
            "description": "American English female voice, medium quality"
        },
        "en_US-danny-low": {
            "model": f"{base_url}/en/en_US/danny/low/en_US-danny-low.onnx",
            "config": f"{base_url}/en/en_US/danny/low/en_US-danny-low.onnx.json",
            "quality": "low",
            "description": "American English male voice, low quality (faster)"
        },
        "en_US-libritts_r-medium": {
            "model": f"{base_url}/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx",
            "config": f"{base_url}/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json",
            "quality": "medium",
            "description": "American English neutral voice, medium quality"
        }
    }
    
    if voice_name not in voices:
        print(f"Available voices: {', '.join(voices.keys())}")
        return False
    
    voice_info = voices[voice_name]
    print(f"\nDownloading Piper voice: {voice_name}")
    print(f"Description: {voice_info['description']}")
    
    # Download model
    model_path = model_dir / f"{voice_name}.onnx"
    if not model_path.exists():
        print(f"\nDownloading model to {model_path}")
        try:
            download_file(voice_info["model"], model_path)
        except Exception as e:
            print(f"Error downloading model: {e}")
            return False
    else:
        print(f"Model already exists: {model_path}")
    
    # Download config
    config_path = model_dir / f"{voice_name}.onnx.json"
    if not config_path.exists():
        print(f"\nDownloading config to {config_path}")
        try:
            download_file(voice_info["config"], config_path)
        except Exception as e:
            print(f"Error downloading config: {e}")
            return False
    else:
        print(f"Config already exists: {config_path}")
    
    # Verify files
    if model_path.exists() and config_path.exists():
        print(f"\n✓ Voice model ready: {voice_name}")
        print(f"  Model: {model_path}")
        print(f"  Config: {config_path}")
        
        # Update environment variable
        print(f"\nTo use this voice, set:")
        print(f"export PIPER_MODEL_PATH={model_path}")
        
        return True
    else:
        print("\n✗ Download failed")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Piper TTS voices")
    parser.add_argument("--voice", default="en_US-amy-medium", 
                       help="Voice name to download")
    parser.add_argument("--model-dir", default="/mnt/storage/models/tts",
                       help="Directory to save models")
    parser.add_argument("--list", action="store_true",
                       help="List available voices")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available Piper voices:")
        print("- en_US-amy-medium (recommended)")
        print("- en_US-danny-low")
        print("- en_US-libritts_r-medium")
        return
    
    success = download_piper_voice(args.voice, args.model_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()