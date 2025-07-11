# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ISEE Tutor is an AI-powered educational companion device for children, featuring ISEE test preparation and general knowledge companion modes. It runs locally on NVIDIA Jetson hardware for privacy and offline operation.

## Common Development Commands

### Starting the System
```bash
# Start the API server (main entry point)
python3 start_api.py

# Quick setup for new installations
python3 setup/quick_setup.py

# Initial system setup (requires sudo)
sudo bash setup/initial-setup.sh
```

**Note**: The API server runs on port 8000 by default. When accessing from another machine, use the Jetson's IP address (e.g., http://192.168.x.x:8000/docs). The start_api.py script was fixed to use the import string "src.api.main:app" for proper reload functionality with uvicorn.

### Testing
```bash
# Run simple companion mode test
python3 tests/test_companion_mode_simple.py

# Run full test suite
pytest

# Test specific component
pytest tests/test_api.py
```

### Dependencies
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# For Jetson-specific dependencies
pip3 install -r requirements-jetson.txt
```

### Verification
```bash
# Verify setup is complete
python3 verify_setup.py

# Simple verification
python3 verify_setup_simple.py
```

## High-Level Architecture

### Core Components

1. **API Layer** (`src/api/`)
   - FastAPI server handling HTTP/WebSocket connections
   - Main entry point: `src/api/main.py`
   - Endpoints for tutor mode, companion mode, and system control

2. **Core Services** (`src/core/`)
   - `audio/`: Audio processing, speech recognition, TTS
   - `companion/`: Companion mode logic and conversation handling
   - `hardware/`: LED control, button handling, hardware interfaces

3. **AI Models** (`src/models/`)
   - LLM interface (Llama 3.2 via llama-cpp-python)
   - Whisper for speech recognition
   - Model loading and management

4. **Data Layer** (`data/`)
   - `content/`: Educational content for ISEE preparation
   - `knowledge/`: Vector databases for RAG
   - `models/`: Stored AI models (7-8GB)
   - `users/`: User data and progress tracking

### Key Architectural Patterns

1. **Event-Driven Communication**
   - Redis for pub/sub between components
   - WebSocket for real-time UI updates
   - Async/await throughout for non-blocking operations

2. **Modular AI Pipeline**
   - Speech → Text (Whisper) → LLM (Llama) → Text → Speech (TTS)
   - Each component can be swapped independently
   - ChromaDB for RAG to enhance responses

3. **Hardware Abstraction**
   - Clean interfaces for LED, audio, buttons
   - Mock implementations for development without hardware
   - Jetson GPIO integration for production

4. **Privacy-First Design**
   - All processing happens locally
   - No cloud dependencies for core functionality
   - User data stays on device

### Development Workflow

1. **API Development**
   - FastAPI auto-reloads on changes
   - API docs at http://localhost:8000/docs
   - WebSocket testing via web interface

2. **Hardware Testing**
   - Use mock hardware classes when developing without Jetson
   - LED patterns defined in `src/core/hardware/led_patterns.py`
   - Audio testing via `tests/test_companion_mode_simple.py`

3. **AI Model Integration**
   - Models download automatically on first run
   - Quantized models for Jetson performance
   - Fallback to CPU if GPU unavailable

### Important Notes

- **Jetson-Specific**: Code assumes NVIDIA Jetson for production but works on any Linux/Mac for development
- **Python 3.10+**: Required for async features and type hints
- **Storage**: Ensure 10GB+ free space for models and knowledge bases
- **Audio**: USB audio devices required (built-in often unreliable)
- **Permissions**: GPIO and audio may require user to be in specific groups

### Environment Variables

Key environment variables (set in `.env`):
- `APP_PORT`: API server port (default: 8000)
- `KNOWLEDGE_PATH`: Path to knowledge bases (default: ./data/knowledge)
- `MODEL_PATH`: Path to AI models (default: ./data/models)
- `WHISPER_MODEL`: Whisper model size (default: base)
- `LLM_MODEL`: Path to Llama model file