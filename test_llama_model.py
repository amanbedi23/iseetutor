#!/usr/bin/env python3
"""Test if Llama model can be loaded and used"""

import os
import sys

try:
    from llama_cpp import Llama
    
    model_path = "/mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    
    print(f"Attempting to load model from: {model_path}")
    print(f"Model file exists: {os.path.exists(model_path)}")
    print(f"Model size: {os.path.getsize(model_path) / 1024**3:.2f} GB")
    
    print("\nLoading model (this may take a moment)...")
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,  # Context window
        n_gpu_layers=0,  # CPU only for testing
        verbose=False
    )
    
    print("✅ Model loaded successfully!")
    
    # Test generation
    print("\nTesting generation...")
    response = llm("Hello! Can you tell me what 2+2 equals?", max_tokens=50)
    print(f"Response: {response['choices'][0]['text']}")
    
    print("\n✅ Model is working correctly!")
    
except ImportError:
    print("❌ Error: llama-cpp-python is not installed")
    print("Run: pip3 install llama-cpp-python")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()