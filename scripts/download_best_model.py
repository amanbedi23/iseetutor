#!/usr/bin/env python3
"""
Download the best models for ISEE Tutor with authentication support
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_huggingface_auth():
    """Set up Hugging Face authentication"""
    print("To download the best models, you need a Hugging Face account.")
    print("\n1. Create a free account at: https://huggingface.co/join")
    print("2. Get your access token from: https://huggingface.co/settings/tokens")
    print("3. Some models require accepting terms at their model page")
    print("")
    
    token = input("Enter your Hugging Face token (or press Enter to skip): ").strip()
    
    if token:
        # Save token
        subprocess.run(["huggingface-cli", "login", "--token", token], check=True)
        return True
    return False

def main():
    print("=== Best Models for ISEE Tutor ===")
    print("\n📚 For educational tutoring, these are the top choices:\n")
    
    print("🏆 RECOMMENDED MODELS:")
    print("\n1. **Llama 3.1 8B Instruct** (Q4_K_M - 4.9GB)")
    print("   ✓ Latest Llama model with excellent reasoning")
    print("   ✓ Great at explaining concepts step-by-step")
    print("   ✓ Strong math and language skills")
    print("   ✓ Child-safe responses")
    
    print("\n2. **Llama 3.2 8B Instruct** (Q4_K_M - 4.9GB)")
    print("   ✓ Newest version with better instruction following")
    print("   ✓ Improved educational explanations")
    print("   ✓ Better at maintaining context")
    print("   Note: May require authentication")
    
    print("\n3. **Mixtral 8x7B Instruct** (Q3_K_M - 18GB)")
    print("   ✓ Excellent for complex reasoning")
    print("   ✓ Best quality responses")
    print("   ⚠️  Very large - may be slow on Jetson")
    
    print("\n4. **Qwen 2.5 7B Instruct** (Q4_K_M - 4.5GB)")
    print("   ✓ Excellent at math and reasoning")
    print("   ✓ Good educational content")
    print("   ✓ Fast and efficient")
    
    print("\n5. **Phi-3 Medium 14B** (Q4_K_M - 7.6GB)")
    print("   ✓ Microsoft's model optimized for reasoning")
    print("   ✓ Great at educational tasks")
    print("   ✓ Good size/performance balance")
    
    print("\n" + "="*50)
    print("For ISEE Tutor, I recommend:")
    print("- **Llama 3.1 8B** for best overall performance")
    print("- **Qwen 2.5 7B** for strong math capabilities")
    print("- **Phi-3 Medium** if you have extra RAM")
    print("="*50 + "\n")
    
    # Model download configurations
    models = {
        "1": {
            "name": "Llama 3.1 8B Instruct",
            "repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
            "file": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "size": "4.9GB",
            "auth": False
        },
        "2": {
            "name": "Llama 3.2 8B Instruct",
            "repo": "bartowski/Llama-3.2-8B-Instruct-GGUF",
            "file": "Llama-3.2-8B-Instruct-Q4_K_M.gguf",
            "size": "4.9GB",
            "auth": True
        },
        "3": {
            "name": "Mixtral 8x7B Instruct",
            "repo": "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF",
            "file": "mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
            "size": "18GB",
            "auth": False
        },
        "4": {
            "name": "Qwen 2.5 7B Instruct",
            "repo": "Qwen/Qwen2.5-7B-Instruct-GGUF",
            "file": "qwen2.5-7b-instruct-q4_k_m.gguf",
            "size": "4.5GB",
            "auth": False
        },
        "5": {
            "name": "Phi-3 Medium 14B",
            "repo": "microsoft/Phi-3-medium-14b-instruct-gguf",
            "file": "Phi-3-medium-14b-instruct-Q4_K_M.gguf",
            "size": "7.6GB",
            "auth": False
        }
    }
    
    choice = input("\nSelect model (1-5) [recommended: 1]: ").strip() or "1"
    
    if choice not in models:
        print("Invalid choice, using Llama 3.1")
        choice = "1"
    
    model_info = models[choice]
    
    # Check if authentication needed
    if model_info["auth"]:
        print(f"\n⚠️  {model_info['name']} requires authentication")
        if not setup_huggingface_auth():
            print("Switching to Llama 3.1 (no auth required)")
            choice = "1"
            model_info = models[choice]
    
    # Create model directory
    model_dir = Path("/mnt/storage/models/llm")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDownloading {model_info['name']} ({model_info['size']})...")
    
    # Download using huggingface-cli
    try:
        cmd = [
            "huggingface-cli", "download",
            model_info["repo"],
            model_info["file"],
            "--local-dir", str(model_dir),
            "--local-dir-use-symlinks", "False"
        ]
        subprocess.run(cmd, check=True)
        
        model_path = model_dir / model_info["file"]
        print(f"\n✅ Model downloaded successfully to: {model_path}")
        
        # Update .env
        env_file = Path("/home/tutor/iseetutor/.env")
        if env_file.exists():
            lines = []
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('MODEL_PATH='):
                        lines.append(f'MODEL_PATH={model_path}\n')
                    else:
                        lines.append(line)
            
            with open(env_file, 'w') as f:
                f.writelines(lines)
            print("Updated .env with new model path")
        
        # Create model config
        config_path = model_dir / "model_config.yaml"
        with open(config_path, 'w') as f:
            f.write(f"""# ISEE Tutor Model Configuration
model:
  name: {model_info['name']}
  path: {model_path}
  type: gguf
  
inference:
  n_gpu_layers: 35  # Adjust based on GPU memory
  n_ctx: 4096       # Context window
  n_batch: 512      # Batch size
  temperature: 0.7  # Default temperature
  max_tokens: 1024  # Max response length
  
modes:
  tutor:
    temperature: 0.3  # More focused for educational content
    top_p: 0.9
    repeat_penalty: 1.1
    system_prompt: |
      You are an expert ISEE tutor helping students prepare for the ISEE test.
      Provide clear, step-by-step explanations for all concepts.
      Use encouraging language and adapt to the student's level.
      Focus on building understanding, not just providing answers.
      
  friend:
    temperature: 0.8  # More creative for general chat
    top_p: 0.95
    repeat_penalty: 1.0
    system_prompt: |
      You are a friendly, knowledgeable companion for children.
      Keep conversations age-appropriate and educational.
      Be encouraging, patient, and engaging.
      Help make learning fun and interesting.
""")
        print(f"Created model configuration at: {config_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error downloading model: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in: huggingface-cli login")
        print("2. Accept model terms at: https://huggingface.co/" + model_info['repo'])
        print("3. Try downloading manually with wget:")
        print(f"   wget https://huggingface.co/{model_info['repo']}/resolve/main/{model_info['file']}")

if __name__ == "__main__":
    main()