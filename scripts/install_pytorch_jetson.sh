#!/bin/bash
# Install PyTorch for Jetson with CUDA support

echo "=== Installing PyTorch for Jetson ==="

# Clean up old installations
echo "Removing old PyTorch installations..."
pip3 uninstall torch torchvision torchaudio -y

# Set CUDA environment
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=/usr/local/cuda

# Option 1: Try dusty-nv's prebuilt wheels (most reliable for Jetson)
echo "Attempting to install PyTorch from dusty-nv's builds..."
cd /tmp

# For JetPack 6.0 (L4T R36.x)
TORCH_URL="https://nvidia.box.com/shared/static/i8pukc49h3lhak4kkn67tg9j4goqm0m7.whl"
wget $TORCH_URL -O torch-2.2.0-cp310-cp310-linux_aarch64.whl

if [ -f torch-2.2.0-cp310-cp310-linux_aarch64.whl ]; then
    echo "Installing PyTorch..."
    pip3 install torch-2.2.0-cp310-cp310-linux_aarch64.whl
    
    # Install torchvision
    echo "Installing torchvision..."
    pip3 install torchvision==0.17.0 --no-deps
    
    # Verify installation
    python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'Device: {torch.cuda.get_device_name(0)}')
"
else
    echo "Failed to download PyTorch wheel"
    echo "Trying alternative method..."
    
    # Alternative: Use pip with specific index
    pip3 install torch==2.0.0 torchvision==0.15.0 --index-url https://download.pytorch.org/whl/cu118
fi

echo "=== PyTorch installation complete ==="