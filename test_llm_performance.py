#!/usr/bin/env python3
import time
import psutil
import GPUtil
from llama_cpp import Llama

print("Testing LLM on Jetson...")

# Monitor resources
start_memory = psutil.virtual_memory().used / 1024 / 1024 / 1024

# Load model with GPU
print("Loading model with GPU acceleration...")
start_time = time.time()

llm = Llama(
    model_path="/mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
    n_ctx=2048,
    n_batch=512,
    n_threads=4,
    n_gpu_layers=35,  # Adjust this value
    use_mlock=True,
    verbose=True
)

load_time = time.time() - start_time
print(f"\nModel loaded in {load_time:.2f} seconds")

# Check memory usage
current_memory = psutil.virtual_memory().used / 1024 / 1024 / 1024
print(f"Memory used: {current_memory - start_memory:.2f} GB")

# Test inference
print("\nTesting inference...")
start_time = time.time()

response = llm(
    "Explain photosynthesis to a 10-year-old in 2 sentences.",
    max_tokens=100,
    temperature=0.7,
    stop=["\n\n"]
)

inference_time = time.time() - start_time
print(f"\nInference time: {inference_time:.2f} seconds")
print(f"Response: {response['choices'][0]['text']}")

# Calculate tokens per second
token_count = response['usage']['completion_tokens']
print(f"\nTokens per second: {token_count / inference_time:.2f}")
