#!/usr/bin/env python3
"""
Test the complete voice pipeline end-to-end
This test verifies that all components work together correctly
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_voice_pipeline():
    """Test the voice pipeline through WebSocket"""
    uri = "ws://localhost:8000/ws"
    
    print("🔊 Testing Voice Pipeline")
    print("=" * 50)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Test 1: Start voice pipeline
            print("\n📍 Test 1: Starting voice pipeline...")
            await websocket.send(json.dumps({
                "type": "voice_start",
                "mode": "friend"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            assert data["type"] == "voice_started", "Failed to start voice pipeline"
            print("✅ Voice pipeline started")
            
            # Wait for state changes
            print("\n📍 Waiting for voice pipeline states...")
            state_count = 0
            max_states = 5
            
            async def receive_states():
                nonlocal state_count
                while state_count < max_states:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(response)
                        if data["type"] == "voice_state":
                            print(f"State: {data['state']}")
                            state_count += 1
                    except asyncio.TimeoutError:
                        break
            
            # Run state receiver in background
            state_task = asyncio.create_task(receive_states())
            
            # Test 2: Send text input
            print("\n📍 Test 2: Sending text input...")
            await websocket.send(json.dumps({
                "type": "text_input",
                "text": "Hello! What's the weather like today?"
            }))
            
            # Wait for responses
            transcript_received = False
            response_received = False
            
            for _ in range(10):  # Wait up to 10 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data["type"] == "voice_transcript":
                        print(f"✅ Transcript: {data['text']}")
                        transcript_received = True
                    elif data["type"] == "voice_response":
                        print(f"✅ Response: {data['text']}")
                        response_received = True
                    elif data["type"] == "text_response":
                        print(f"✅ Text Response: {data['text']}")
                        response_received = True
                    elif data["type"] == "voice_state":
                        print(f"State changed to: {data['state']}")
                    
                    if response_received:
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for response")
                    break
            
            # Cancel state task
            state_task.cancel()
            
            # Test 3: Change mode
            print("\n📍 Test 3: Changing mode to tutor...")
            await websocket.send(json.dumps({
                "type": "voice_mode",
                "mode": "tutor"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            assert data["type"] == "mode_changed", "Failed to change mode"
            print("✅ Mode changed successfully")
            
            # Test 4: Send educational question
            print("\n📍 Test 4: Testing tutor mode...")
            await websocket.send(json.dumps({
                "type": "text_input",
                "text": "Can you help me understand what a metaphor is?"
            }))
            
            # Wait for response
            for _ in range(10):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data["type"] in ["voice_response", "text_response"]:
                        print(f"✅ Tutor Response: {data['text'][:100]}...")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for tutor response")
                    break
            
            # Test 5: Stop voice pipeline
            print("\n📍 Test 5: Stopping voice pipeline...")
            await websocket.send(json.dumps({
                "type": "voice_stop"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data}")
            assert data["type"] == "voice_stopped", "Failed to stop voice pipeline"
            print("✅ Voice pipeline stopped")
            
            print("\n✅ All tests passed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_voice_hardware():
    """Test voice pipeline with actual hardware (wake word detection)"""
    print("\n🎤 Testing Voice Pipeline with Hardware")
    print("=" * 50)
    print("This test requires:")
    print("- Microphone connected")
    print("- Speaker connected")
    print("- Say 'Hey Jarvis' to activate")
    print("\nPress Ctrl+C to stop")
    
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("\n✅ Connected to WebSocket")
            
            # Start voice pipeline
            await websocket.send(json.dumps({
                "type": "voice_start",
                "mode": "friend"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            if data["type"] == "voice_started":
                print("✅ Voice pipeline started - Say 'Hey Jarvis' to activate!")
            
            # Listen for events
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data["type"] == "voice_state":
                        state = data["state"]
                        if state == "recording":
                            print("🎤 Recording... Speak now!")
                        elif state == "processing":
                            print("🤔 Processing...")
                        elif state == "speaking":
                            print("🔊 Speaking response...")
                        elif state == "listening_for_wake":
                            print("👂 Listening for wake word...")
                            
                    elif data["type"] == "voice_transcript":
                        print(f"📝 You said: {data['text']}")
                        
                    elif data["type"] == "voice_response":
                        print(f"🤖 Assistant: {data['text']}")
                        
                except KeyboardInterrupt:
                    print("\n\nStopping...")
                    break
            
            # Stop pipeline
            await websocket.send(json.dumps({
                "type": "voice_stop"
            }))
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test voice pipeline")
    parser.add_argument("--hardware", action="store_true", 
                       help="Test with actual hardware (microphone/speaker)")
    args = parser.parse_args()
    
    print("🚀 Voice Pipeline Test")
    print("Make sure the API server is running: python3 start_api.py")
    print()
    
    if args.hardware:
        asyncio.run(test_voice_hardware())
    else:
        asyncio.run(test_voice_pipeline())