# UI Testing Guide for ISEE Tutor

## Prerequisites
1. **API Server**: Running on http://localhost:8000
   ```bash
   python3 start_api.py
   ```

2. **Frontend**: Running on http://localhost:3000
   ```bash
   cd frontend
   npm start
   ```

## Testing the UI Features

### 1. **Voice Interaction Component**
   - Navigate to http://localhost:3000
   - Look for the voice interaction interface
   - Features to test:
     - **Mode Switching**: Toggle between Tutor/Friend/Hybrid modes
     - **Voice Button**: Click to start voice interaction (requires microphone)
     - **Text Input**: Type messages to test without voice
     - **Real-time Transcription**: Should show what you're saying
     - **Voice Visualizer**: Animated particles when speaking

### 2. **WebSocket Connection**
   - The top of the UI shows connection status
   - Should show "Connected" in green when working
   - If showing "Disconnected":
     1. Check API server is running
     2. Check browser console for errors (F12)
     3. Try refreshing the page

### 3. **Quick WebSocket Test**
   Open http://localhost:8000/test_websocket.html in your browser
   - Should show "Connected!" in green
   - Click "Send Test Message" to verify bidirectional communication

### 4. **API Documentation**
   - Visit http://localhost:8000/docs for interactive API testing
   - Test endpoints:
     - `/health` - System health check
     - `/api/companion/chat` - Text chat endpoint
     - `/ws` - WebSocket endpoint (use test page above)

### 5. **Testing Voice Pipeline**
   Without hardware:
   ```bash
   python3 test_voice_quickstart.py
   ```
   
   This tests:
   - Wake word detection simulation
   - Speech-to-text simulation
   - LLM response generation
   - Text-to-speech simulation

### 6. **Troubleshooting Connection Issues**

If WebSocket shows disconnected:

1. **Check CORS**: Browser console should not show CORS errors
2. **Check Network**: 
   - Open browser DevTools (F12)
   - Go to Network tab
   - Look for WebSocket connection to ws://localhost:8000/ws
   - Status should be 101 (Switching Protocols)

3. **Test Direct Connection**:
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" \
        -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
        http://localhost:8000/ws
   ```

4. **Check Logs**:
   - API server console for connection attempts
   - Browser console for JavaScript errors

## Current UI Features Status

✅ **Working**:
- Voice interaction interface
- Mode switching (Tutor/Friend/Hybrid)
- WebSocket connection infrastructure
- Voice visualizer with particle effects
- Text input for testing without voice

⚠️ **Requires Hardware**:
- Actual voice recording (needs microphone)
- Wake word detection (needs "Hey Jarvis" spoken)
- Audio playback (needs speakers)

❌ **Not Yet Implemented**:
- User profiles/login
- Learning dashboard
- Progress tracking visualization
- Parent portal
- Achievement system

## Development Tips

1. **Hot Reload**: Both frontend and backend support hot reload
2. **Mock Mode**: Use text input to test without voice hardware
3. **Browser Console**: Essential for debugging WebSocket issues
4. **Network Tab**: Monitor API calls and WebSocket frames

## Next Steps
1. Test voice features with actual microphone/speakers
2. Implement user authentication flow
3. Build learning dashboard components
4. Add progress tracking visualizations