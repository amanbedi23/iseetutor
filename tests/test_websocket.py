#!/usr/bin/env python3
"""Test WebSocket functionality"""

import asyncio
import websockets
import json
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_websocket_client():
    """Test WebSocket connection to the API server"""
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Send a test message
            test_message = {
                "type": "test",
                "data": "Hello WebSocket!"
            }
            await websocket.send(json.dumps(test_message))
            print(f"Sent: {test_message}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Test real-time updates
            for i in range(3):
                await asyncio.sleep(1)
                status_message = {
                    "type": "status",
                    "data": f"Test update {i+1}"
                }
                await websocket.send(json.dumps(status_message))
                print(f"Sent: {status_message}")
                
                response = await websocket.recv()
                print(f"Received: {response}")
                
    except (ConnectionRefusedError, OSError) as e:
        print("Connection refused - WebSocket endpoint not available")
        print("This is expected as WebSocket is not yet implemented")
        return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing WebSocket functionality...")
    success = asyncio.run(test_websocket_client())
    
    if success:
        print("\n✅ WebSocket test completed successfully!")
    else:
        print("\n❌ WebSocket test failed - implementation needed")