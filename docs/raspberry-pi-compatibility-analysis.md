# Raspberry Pi Compatibility Analysis for ISEE Tutor

## Executive Summary

The ISEE Tutor project has significant hardware dependencies on NVIDIA Jetson that would require substantial modifications for Raspberry Pi deployment. While the core software architecture is well-abstracted, several key components rely on Jetson-specific features.

## Hardware Requirements Analysis

### 1. **GPIO and Hardware Control**
- **Current**: Uses Jetson.GPIO library for LED ring and button control
- **Pi Compatible**: Yes, with modifications
- **Required Changes**:
  - Replace `Jetson.GPIO` with `RPi.GPIO` or `gpiozero`
  - Update pin mappings (Jetson uses different GPIO numbering)
  - The hardware abstraction layer already supports mock mode, making this transition easier

### 2. **LED Ring (WS2812B)**
- **Current**: 16-LED RGB ring requiring 5V logic with level shifter
- **Pi Compatible**: Yes
- **Notes**:
  - Raspberry Pi GPIO outputs 3.3V (same as Jetson)
  - Still needs 74AHCT125 level shifter for 5V LEDs
  - Power requirements (~960mA) within Pi's capabilities

### 3. **Audio Hardware**
- **Current**: ReSpeaker 4-Mic USB Array + USB Speaker
- **Pi Compatible**: Yes
- **Dependencies**: 
  - `pyaudio`, `sounddevice` - standard Python audio libraries
  - WebRTC VAD - CPU-based, no GPU requirement
  - No Jetson-specific audio code found

### 4. **Display Requirements**
- **Current**: 10.1" touchscreen via HDMI
- **Pi Compatible**: Yes
- **Notes**:
  - Pi has native HDMI output (no DisplayPort adapter needed)
  - Touch support via USB is standard
  - Kiosk mode setup would work identically

## Software Dependencies Analysis

### 1. **AI/ML Models** ⚠️ **MAJOR CHALLENGE**
- **LLM (Llama 3.1 8B)**:
  - Current: 4.58GB quantized model
  - Uses CUDA acceleration (`n_gpu_layers=32`)
  - **Pi Issue**: No CUDA support, CPU-only inference would be extremely slow
  - **Solution Options**:
    - Use smaller model (Llama 3.2 3B or smaller)
    - Implement cloud API fallback
    - Use specialized inference engines (llama.cpp optimized for ARM)

- **Whisper STT**:
  - Current: Uses CUDA when available (`torch.cuda.is_available()`)
  - Falls back to CPU automatically
  - **Pi Performance**: Base model (~140MB) might work, but slowly
  - **Solution**: Use tiny model or cloud STT service

- **OpenWakeWord**:
  - TensorFlow Lite based - ARM compatible
  - Should work on Pi with reasonable performance

### 2. **Memory Requirements** ⚠️ **CRITICAL ISSUE**
- **Documented Requirements**:
  - RAM usage: < 4GB (target)
  - GPU memory: < 2GB
  - Current Jetson has 8GB unified memory
- **Pi Limitations**:
  - Pi 4: Max 8GB RAM (no dedicated GPU memory)
  - Pi 5: Max 8GB RAM
  - Loading 4.5GB LLM model would consume >50% of available RAM
  - No memory left for OS, application, and other services

### 3. **Performance Requirements** ❌ **NOT ACHIEVABLE**
- **Target**: < 2.5 second total response time
- **Breakdown**:
  - Wake word: 300ms ✓ (achievable)
  - STT: ~1s on CPU (marginal)
  - LLM inference: 10-30s on Pi CPU ❌
  - TTS: ~500ms ✓ (achievable)
- **Total**: 12-32 seconds (unacceptable for user experience)

### 4. **Storage Requirements**
- **Current**: 
  - Models: 7-8GB
  - ChromaDB: Variable
  - Educational content: ~2GB
  - Total: ~20GB
- **Pi Compatible**: Yes (with adequate SD card or USB storage)

## Software Architecture Compatibility

### ✅ **Compatible Components**
1. **FastAPI Web Server**: Pure Python, fully compatible
2. **React Frontend**: Runs in browser, platform agnostic
3. **PostgreSQL + Redis**: Standard services, ARM builds available
4. **Celery Task Queue**: Pure Python, fully compatible
5. **Hardware Abstraction**: Already has mock mode
6. **WebSocket Communication**: Standard implementation
7. **Audio Pipeline**: Uses platform-agnostic libraries

### ⚠️ **Requires Modification**
1. **GPIO Control**: Change from Jetson.GPIO to RPi.GPIO
2. **Pin Mappings**: Update for Pi's GPIO layout
3. **Power Management**: Different commands for Pi
4. **Boot/Kiosk Setup**: Pi-specific configuration

### ❌ **Major Challenges**
1. **LLM Inference**: Too slow without GPU acceleration
2. **Memory Constraints**: 4.5GB model on 8GB system
3. **Real-time Performance**: Cannot meet <2.5s requirement
4. **Whisper STT**: Degraded performance without CUDA

## Recommended Approach for Raspberry Pi

### Option 1: Hybrid Cloud Architecture
```python
# Modify CompanionLLM to use cloud API
class CompanionLLM:
    def __init__(self, use_cloud=True):
        if use_cloud:
            self.client = OpenAI()  # or other API
        else:
            self.llm = Llama(...)  # Local fallback
```

**Pros**: 
- Maintains performance requirements
- Reduces local resource usage
- Could work on Pi 4 with 4GB RAM

**Cons**:
- Loses offline capability
- Privacy concerns
- Ongoing API costs

### Option 2: Reduced Functionality
1. Use tiny models (Whisper tiny, Llama 3.2 1B)
2. Simplified responses (template-based + small LLM)
3. Reduced educational content
4. Lower quality STT/TTS

**Pros**:
- Maintains offline operation
- Works within Pi constraints

**Cons**:
- Significantly degraded user experience
- May not meet educational quality standards

### Option 3: Specialized Hardware
- Use Raspberry Pi with Coral AI accelerator
- Implement with specialized models (TFLite)
- Custom quantization for ARM NEON

**Pros**:
- Better performance than CPU-only
- Maintains offline operation

**Cons**:
- Requires significant model re-engineering
- Additional hardware cost
- Still won't match Jetson performance

## Conclusion

While the ISEE Tutor codebase has good hardware abstraction and many components would work on Raspberry Pi, the AI/ML requirements make it impractical for the intended use case:

1. **Performance**: Cannot achieve <2.5s response time with local models
2. **Memory**: 8GB Pi insufficient for 4.5GB LLM + system overhead  
3. **User Experience**: Would require 10-30 second response times

### Recommendation
The Raspberry Pi is **not suitable** for the full ISEE Tutor implementation. Consider:
- Staying with Jetson for production devices
- Using Pi only for development/testing with mock AI services
- Creating a "lite" version with cloud API dependencies
- Exploring alternative edge AI hardware (Coral, Hailo, etc.)

The investment in Jetson hardware is justified by the performance requirements and offline AI capabilities essential to the product vision.