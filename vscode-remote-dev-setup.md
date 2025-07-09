# VS Code Remote Development Setup for Jetson Orin Nano

## Overview
This guide will help you set up Visual Studio Code on your Mac to remotely develop and test code on your Jetson Orin Nano device.

## Prerequisites
- VS Code installed on your Mac
- Jetson Orin Nano with Ubuntu installed and connected to your network
- SSH access to the Jetson

## Step 1: Initial Jetson Network Setup

### On the Jetson:
1. **Get the Jetson's IP address**
   ```bash
   ip addr show
   # Look for the IP address (usually under eth0 or wlan0)
   ```

2. **Enable SSH (if not already enabled)**
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

3. **Create a development user (if using default)**
   ```bash
   # The default user is usually 'nvidia' or 'jetson'
   # Set a password if not already set
   sudo passwd nvidia
   ```

## Step 2: Mac SSH Setup

### On your Mac:
1. **Generate SSH key (if you don't have one)**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Enter a passphrase (optional but recommended)
   ```

2. **Copy SSH key to Jetson**
   ```bash
   ssh-copy-id nvidia@<JETSON_IP>
   # Replace <JETSON_IP> with actual IP address
   # Enter password when prompted
   ```

3. **Test SSH connection**
   ```bash
   ssh nvidia@<JETSON_IP>
   # Should connect without password
   ```

4. **Create SSH config for easier access**
   ```bash
   nano ~/.ssh/config
   ```
   Add:
   ```
   Host jetson
       HostName <JETSON_IP>
       User nvidia
       Port 22
   ```

## Step 3: VS Code Extensions Setup

### Install Required Extensions:
1. Open VS Code on your Mac
2. Install these extensions:
   - **Remote - SSH** (by Microsoft)
   - **Remote - SSH: Editing Configuration Files** (by Microsoft)
   - **Python** (if developing in Python)
   - **C/C++** (if developing in C/C++)

## Step 4: Connect to Jetson from VS Code

1. **Open Remote Connection**
   - Press `Cmd+Shift+P` to open command palette
   - Type "Remote-SSH: Connect to Host..."
   - Select "jetson" (or enter nvidia@<JETSON_IP>)

2. **Select Platform**
   - Choose "Linux" when prompted
   - VS Code will install VS Code Server on Jetson automatically

3. **Open Project Folder**
   - Once connected, click "Open Folder"
   - Navigate to `/home/nvidia/isee-tutor` (or create it)

## Step 5: Development Environment Setup

### On the Remote Jetson (through VS Code):

1. **Create project structure**
   ```bash
   mkdir -p ~/isee-tutor/{src,tests,docs,config,data}
   cd ~/isee-tutor
   ```

2. **Initialize Git repository**
   ```bash
   git init
   echo "# ISEE Tutor Project" > README.md
   git add README.md
   git commit -m "Initial commit"
   ```

3. **Set up Python environment**
   ```bash
   # Install Python and venv
   sudo apt update
   sudo apt install python3-pip python3-venv python3-dev
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install initial packages
   pip install --upgrade pip
   pip install numpy torch torchvision torchaudio --index-url https://developer.download.nvidia.com/compute/redist/jp/v511/pytorch/
   ```

## Step 6: Configure VS Code for Remote Development

### Create VS Code workspace settings:
1. In VS Code (connected to Jetson), create `.vscode/settings.json`:
   ```json
   {
       "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
       "python.terminal.activateEnvironment": true,
       "editor.formatOnSave": true,
       "python.linting.enabled": true,
       "python.linting.pylintEnabled": true,
       "files.watcherExclude": {
           "**/venv/**": true,
           "**/__pycache__/**": true
       }
   }
   ```

### Create launch configuration:
2. Create `.vscode/launch.json`:
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Python: ISEE Tutor",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/src/main.py",
               "console": "integratedTerminal",
               "env": {
                   "PYTHONPATH": "${workspaceFolder}"
               }
           }
       ]
   }
   ```

## Step 7: Enable GPU Access in VS Code

### For CUDA development:
1. **Install CUDA toolkit on Jetson**
   ```bash
   # Usually pre-installed with JetPack
   nvcc --version  # Verify CUDA installation
   ```

2. **Add CUDA paths to VS Code**
   Add to `.vscode/settings.json`:
   ```json
   {
       "terminal.integrated.env.linux": {
           "PATH": "/usr/local/cuda/bin:${env:PATH}",
           "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:${env:LD_LIBRARY_PATH}"
       }
   }
   ```

## Step 8: Real-time Testing Setup

### Create a test script:
1. Create `src/test_hardware.py`:
   ```python
   #!/usr/bin/env python3
   import subprocess
   import torch
   
   def test_gpu():
       print(f"CUDA available: {torch.cuda.is_available()}")
       if torch.cuda.is_available():
           print(f"GPU: {torch.cuda.get_device_name(0)}")
   
   def test_audio():
       # List audio devices
       result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
       print("Audio input devices:")
       print(result.stdout)
   
   if __name__ == "__main__":
       test_gpu()
       test_audio()
   ```

### Port Forwarding for Web UIs:
2. If developing web interfaces, forward ports in VS Code:
   - Click on "Ports" tab in VS Code terminal panel
   - Click "Forward a Port"
   - Enter port number (e.g., 8080)
   - Access from Mac browser at `localhost:8080`

## Step 9: Useful VS Code Remote Features

1. **Terminal Access**
   - Use integrated terminal (`Ctrl+``) for Jetson command line
   - Multiple terminals for different tasks

2. **File Transfer**
   - Drag and drop files in VS Code explorer
   - Use VS Code's upload/download functionality

3. **Remote Debugging**
   - Set breakpoints in VS Code
   - Debug runs on Jetson, controlled from Mac

4. **Extensions on Remote**
   - Some extensions need to be installed on remote
   - VS Code will prompt when needed

## Step 10: Development Workflow

### Recommended workflow:
1. **Edit code** on Mac through VS Code
2. **Save files** - automatically synced to Jetson
3. **Run/Debug** directly on Jetson hardware
4. **View output** in VS Code terminal
5. **Commit changes** using VS Code's Git integration

### Quick Commands:
- `Cmd+Shift+P` → "Remote-SSH: Connect to Host"
- `Cmd+S` → Save and sync to Jetson
- `F5` → Run/Debug on Jetson
- `Cmd+J` → Toggle terminal

## Troubleshooting

### Connection Issues:
- Ensure Jetson and Mac are on same network
- Check firewall settings
- Verify SSH service is running

### Performance Issues:
- Use ethernet instead of WiFi for better stability
- Exclude large directories in file watcher
- Consider using Jetson's NVMe for project files

### VS Code Server Issues:
- Delete `~/.vscode-server` on Jetson and reconnect
- Check disk space on Jetson
- Ensure compatible VS Code version