# Browser Audio Integration Guide

## Overview

The ISEE Tutor voice interaction currently has a limitation where the wake word detection and audio processing run on the server, not in the browser. This guide explains the current state and how to test voice functionality.

## Current Implementation Status

### ✅ What's Working
1. **WebSocket Connection** - Browser connects to backend successfully
2. **Voice Pipeline** - Backend voice processing pipeline starts correctly
3. **Text Input** - Text-based interaction works perfectly
4. **Audio Context** - Browser can capture microphone audio
5. **UI Feedback** - Visual states update correctly

### ⚠️ Current Limitation
The main issue is that the voice pipeline expects audio from the server's microphone (connected to the Jetson), not from the browser. The wake word detection (OpenWakeWord) runs server-side.

## How to Test Voice Features

### Method 1: Text Input (Recommended for Testing)
1. Navigate to the voice interaction page
2. Double-click the microphone button to show text input
3. Type your message and press Enter
4. The system will respond using the LLM with RAG

### Method 2: Browser Audio Test Page
1. Open `test_browser_audio.html` in your browser
2. Click "Connect to WebSocket"
3. Click "Start Audio Capture" (grant microphone permission)
4. Click "Test Voice Pipeline"
5. Check the debug log for audio capture status

### Method 3: Direct API Testing
```bash
# Start the API server
python3 start_api.py

# In another terminal, test text input via WebSocket
python3 test_websocket_connection.py
```

## Architecture Explanation

### Current Flow (Server-Side Audio)
```
Microphone (USB) → Jetson → Voice Pipeline → Wake Word → STT → LLM → TTS → Response
```

### Browser Integration (Partial)
```
Browser Mic → WebSocket → Server → ??? → Voice Pipeline
                ↑                    ↑
                └─ Audio chunks ─────┘ (Not connected)
```

## Required Changes for Full Browser Support

### Option 1: Browser-Side Wake Word (Recommended)
1. Implement wake word detection in JavaScript using TensorFlow.js
2. Only send audio to server after wake word detected
3. Use Web Audio API for continuous monitoring

### Option 2: Stream All Audio to Server
1. Modify `VoicePipeline` to accept WebSocket audio streams
2. Convert WebM audio to format expected by OpenWakeWord
3. Handle network latency and buffering

### Option 3: Hybrid Approach
1. Use push-to-talk in browser (current implementation)
2. Server processes audio without wake word requirement
3. More reliable but less hands-free

## Testing Voice Components Individually

### Test STT (Speech-to-Text)
```python
python3 tests/test_stt.py
```

### Test TTS (Text-to-Speech)
```python
python3 tests/test_tts.py
```

### Test Voice Pipeline
```python
python3 test_voice_quickstart.py
```

## Troubleshooting

### Microphone Permission Denied
- Check browser settings
- Ensure HTTPS or localhost
- Try different browser

### WebSocket Connection Failed
- Verify API server is running on port 8000
- Check firewall settings
- Use correct IP address if not localhost

### No Audio Visualization
- Verify microphone is working in system
- Check browser console for errors
- Ensure AudioContext is not blocked

## Next Steps

To fully enable browser-based voice interaction:

1. **Implement Browser Wake Word Detection**
   - Use pre-trained TensorFlow.js model
   - Or use Web Speech API for "Hey Tutor"

2. **Modify Voice Pipeline**
   - Accept audio streams from WebSocket
   - Handle format conversion (WebM → PCM)

3. **Add Audio Streaming Protocol**
   - Implement chunked audio transfer
   - Add compression for bandwidth

4. **Update Frontend**
   - Add continuous audio monitoring
   - Show wake word detection status
   - Handle network interruptions

## Current Workaround

For now, the best user experience is:
1. Click the microphone button to start recording
2. Speak your question
3. Click again to stop and process
4. Or use double-click for text input

This provides a functional voice interface while the full wake word integration is being developed.