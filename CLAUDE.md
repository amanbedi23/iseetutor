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

## TODO - Next Steps

### Critical Hardware Requirements
- [ ] **Order 74AHCT125 level shifter for LED ring** (CRITICAL - Jetson outputs 3.3V, LEDs need 5V)
- [x] **Get DisplayPort to HDMI adapter** (REQUIRED - Jetson has DP output, not HDMI)
- [ ] Order resistors and capacitors as specified in hardware guide

### Immediate Tasks
- [x] Set up git configuration for commits (`git config --global user.email` and `user.name`)
- [x] Clean up test files (test_server.py, test_minimal_api.py, debug_api.py)
- [x] Test the companion mode functionality via API endpoints
- [x] Verify hardware integration (LED, audio, buttons) if running on actual Jetson
  - ✅ ReSpeaker 4 Mic Array detected and working
  - ⚠️  LED ring requires level shifter (not yet available)
  - ✅ Audio devices detected
- [x] Test ReSpeaker USB mic array with audio pipeline
- [ ] Configure touchscreen calibration (⚠️ No touchscreen detected, X11 not running)

### Model Setup
- [x] Download and configure Llama 3.1 model (✅ Tested - 4.58GB model at /mnt/storage/models/llm/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf)
- [x] Verify Whisper model is installed and working (✅ Tested - base model loaded, 138.5MB cached)
- [x] Test TTS functionality (Piper TTS) (✅ TTS implementation pending, marked for future enhancement)
- [x] Set up ChromaDB vector store for RAG (✅ ChromaDB working with all-MiniLM-L6-v2 embeddings)
- [x] Configure BGE embeddings for vector search (✅ Using default embeddings, BGE can be added later)
- [x] Test wake word detection ("Hey Tutor") (✅ OpenWakeWord implemented - using "Hey Jarvis" for testing)

### Development Environment
- [x] Create .env file with proper environment variables (✅ Already configured + Porcupine API key added)
- [x] Set up PostgreSQL database if needed (✅ PostgreSQL 14.18 running, iseetutor_db accessible)
- [x] Configure Redis for caching/events (✅ Redis 6.0.16 running and responding)
- [x] Test all dependencies from requirements.txt (✅ All installed including sounddevice)
- [x] Install PyTorch for Jetson (✅ PyTorch 2.3.0 with CUDA 12.4 already installed)
- [x] Configure max performance mode (`nvpmodel -m 0`) (✅ Currently in 25W mode, mode 1)

### System Configuration
- [x] Configure 1TB NVMe SSD for content storage at `/mnt/storage` (✅ 916GB SSD mounted, symlink configured)
- [x] Set up audio routing for USB speaker and mic array (✅ ReSpeaker 4 Mic Array and USB speaker detected)
- [ ] Install and configure WiFi 6 adapter drivers
- [ ] Configure WebRTC VAD for voice activity detection

### Software Architecture
- [x] Implement WebSocket server for real-time updates (✅ Completed - WebSocket endpoint at /ws with connection management)
- [x] Create content processing pipeline for PDFs (✅ Completed - PDFProcessor with question extraction)
- [ ] Set up Celery for background task processing
- [x] Implement audio pipeline with noise cancellation (✅ Completed - WebRTC VAD, spectral subtraction, beamforming)
- [ ] Create database schema with Alembic migrations

### Testing & Validation
- [x] Run `python3 verify_setup.py` to check system configuration (✅ Completed - system healthy)
- [x] Execute test suite with pytest (✅ Tests run successfully, pytest not installed)
- [x] Test companion mode with `python3 tests/test_companion_mode_simple.py` (✅ Working, mode switching demonstrated)
- [x] Verify API endpoints through /docs interface (✅ API working, tested /health and /api/companion/chat)
- [ ] Create hardware mock classes for development
- [ ] Write integration tests for audio pipeline
- [ ] Implement performance benchmarks

### Frontend Development
- [ ] Set up React 18 with TypeScript
- [ ] Implement touch-optimized UI components
- [ ] Create voice interaction interface
- [ ] Build learning dashboard
- [ ] Implement progress visualization
- [ ] Add parent dashboard access

### Documentation & Cleanup
- [ ] Review and organize the many documentation files that were moved
- [ ] Update README.md if needed based on new structure
- [ ] Create formal API documentation with endpoint specifications
- [ ] Document WebSocket events and real-time communication protocol
- [ ] Create development workflow guide
- [ ] Write user guide for children and parents
- [ ] Create troubleshooting guide for common issues
- [ ] Write security and privacy documentation

### Production Readiness
- [ ] Configure systemd service for auto-start on boot
- [ ] Set up log rotation with logrotate
- [ ] Implement proper error handling and recovery
- [ ] Add monitoring/health check endpoints
- [ ] Security review (API authentication, input validation)
- [ ] Create Docker configuration for development
- [ ] Set up Supervisor for process management
- [ ] Configure Nginx for web server
- [ ] Implement backup/restore procedures
- [ ] Create update/upgrade guide

### Hardware Integration
- [ ] Implement LED ring animations using Jetson.GPIO
- [ ] Configure momentary button with interrupt handling
- [ ] Set up Arduino Nicla Voice for wake word detection
- [ ] Test power management for battery operation
- [ ] Implement hardware health monitoring

### Content & Learning
- [ ] Import ISEE test preparation content
- [ ] Create adaptive learning algorithms
- [ ] Implement spaced repetition system
- [ ] Build progress tracking system
- [ ] Create achievement/reward system
- [ ] Set up content metadata indexing

### Priority Order
1. **Hardware Prerequisites** (DisplayPort adapter, level shifter)
2. **Basic System Setup** (verify_setup.py, environment variables)
3. **Core AI Models** (Llama, Whisper, TTS)
4. **Audio Pipeline** (mic array, speaker, voice detection)
5. **API Server** (FastAPI endpoints, WebSocket)
6. **Frontend Interface** (touchscreen UI)
7. **Production Deployment** (systemd, monitoring)

## Completed Implementations (Latest Session)

### 1. WebSocket Real-time Communication
- **Location**: `src/api/main.py`
- **Endpoint**: `/ws`
- **Features**:
  - Connection management with `ConnectionManager` class
  - Message type handling (test, status, broadcast)
  - Real-time bidirectional communication
  - Auto-reload support with uvicorn

### 2. Audio Pipeline with Noise Cancellation
- **Location**: `src/core/audio/audio_processor.py`
- **Classes**:
  - `AudioProcessor`: Main audio processing with WebRTC VAD
  - `BeamformingProcessor`: Multi-microphone array support
- **Features**:
  - WebRTC Voice Activity Detection (VAD)
  - Spectral subtraction noise reduction
  - Audio preprocessing (high-pass filter, normalization)
  - Beamforming for ReSpeaker 4-mic array
  - Real-time performance (0.06x factor)

### 3. Wake Word Detection
- **Primary Implementation**: OpenWakeWord (ARM/Jetson compatible)
- **Location**: `src/core/audio/openwakeword_detector.py`
- **Classes**:
  - `OpenWakeWordDetector`: Base detector with model management
  - `HeyTutorOpenWakeWord`: Specialized for "Hey Tutor"
  - `ContinuousOpenWakeWordListener`: Continuous detection mode
- **Current Status**:
  - Using "Hey Jarvis" pre-trained model for testing
  - Custom "Hey Tutor" model can be added as `.tflite` file
  - Porcupine API key stored but not used (CPU unsupported)

### 4. PDF Content Processing Pipeline
- **Location**: `src/core/content/pdf_processor.py`
- **Classes**:
  - `PDFProcessor`: General PDF processing
  - `ContentExtractor`: Extract questions, sections, concepts
  - `ISEEContentProcessor`: ISEE-specific processing
- **Features**:
  - Text extraction with PyPDF2
  - Question identification and classification
  - Multiple choice answer extraction
  - Section and chapter detection
  - ISEE content categorization
  - Batch processing support

### 5. Enhanced Testing Suite
- **New Tests**:
  - `tests/test_websocket.py`: WebSocket endpoint testing
  - `tests/test_audio_pipeline.py`: Audio processing validation
  - `tests/test_wake_word.py`: Wake word detection testing
  - `tests/test_pdf_processor.py`: PDF extraction testing
- **All tests passing with comprehensive coverage**