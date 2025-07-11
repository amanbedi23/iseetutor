# ISEE Tutor Setup Guide

## Quick Setup Instructions

### 1. Install System Dependencies (Requires sudo)

```bash
sudo bash scripts/install_dependencies.sh
```

This installs:
- Python pip and development tools
- PostgreSQL and Redis databases
- Audio libraries (portaudio, ffmpeg)
- Node.js and npm for the web interface

### 2. Download the Llama Model

```bash
python3 scripts/download_llama_model.py
```

Choose option 1 (Q4_K_M) for the best balance of quality and performance on Jetson.
This downloads a 4.9GB model file to `/mnt/storage/models/`

### 3. Set Up Knowledge Bases

```bash
python3 scripts/setup_knowledge_bases.py
```

This creates local databases with:
- ISEE test content and questions
- General knowledge facts for friend mode
- Science experiments and math tricks
- Study tips and strategies

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

### 5. Test the System

```bash
# Test companion mode switching
python3 tests/test_companion_mode_simple.py

# Test with actual model (once downloaded)
python3 tests/test_companion_mode.py
```

## What You Get

### Tutor Mode
- Focused ISEE test preparation
- Step-by-step explanations
- Practice questions in ISEE format
- Progress tracking

### Friend Mode  
- General knowledge companion
- Fun facts and stories
- Science experiments
- Casual conversation

### Smart Features
- Automatic mode switching suggestions
- Child-safe content filtering
- Age-appropriate responses
- Offline operation (no internet needed)

## Running the Full System

Once setup is complete:

```bash
# Terminal 1: Start the API server
python3 src/api/main.py

# Terminal 2: Start the web interface
cd web
npm install
npm start

# Access at http://localhost:3000
```

## Troubleshooting

### If pip is not found:
```bash
sudo apt update
sudo apt install python3-pip
```

### If you get permission errors:
```bash
sudo chown -R $USER:$USER /mnt/storage
```

### If model download fails:
Download manually from: https://huggingface.co/bartowski/Llama-3.2-8B-Instruct-GGUF
Save to: `/mnt/storage/models/`

## Storage Usage

After full setup:
- Models: ~5-6GB
- Knowledge bases: ~1GB  
- System files: ~500MB
- Total: ~7-8GB (plenty of room on your 1TB SSD)

## Next Steps

1. Connect your hardware (microphone, speaker, LED ring)
2. Configure wake word ("Hey Tutor")
3. Add ISEE practice PDFs to process
4. Create user profiles for your kids
5. Start tutoring!

The system is designed to work completely offline while maintaining privacy and providing both educational and companion features.