#!/usr/bin/env python3
"""Test WebSocket connection to the backend."""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test WebSocket connection and basic messaging."""
    uri = "ws://localhost:8000/ws"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Test basic echo
            test_message = {
                "type": "test",
                "data": "Hello from test client"
            }
            
            print(f"\nSending test message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            response = await websocket.recv()
            print(f"Received response: {response}")
            
            # Test voice start
            voice_message = {
                "type": "voice_start",
                "mode": "friend"
            }
            
            print(f"\nSending voice start message: {voice_message}")
            await websocket.send(json.dumps(voice_message))
            
            # Wait for responses
            for _ in range(3):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"Received: {response}")
                except asyncio.TimeoutError:
                    print("No more messages (timeout)")
                    break
            
            print("\n✅ WebSocket test completed successfully!")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False
    
    return True

async def test_cors_preflight():
    """Test CORS preflight request."""
    import aiohttp
    
    print("\nTesting CORS preflight request...")
    
    async with aiohttp.ClientSession() as session:
        # Simulate browser preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
        
        try:
            async with session.options("http://localhost:8000/ws", headers=headers) as response:
                print(f"Preflight response status: {response.status}")
                print("Response headers:")
                for header, value in response.headers.items():
                    if header.lower().startswith('access-control'):
                        print(f"  {header}: {value}")
                        
                if response.status == 200:
                    print("✅ CORS preflight successful")
                else:
                    print("❌ CORS preflight failed")
                    
        except Exception as e:
            print(f"❌ CORS preflight error: {e}")

if __name__ == "__main__":
    print("=== WebSocket Connection Test ===\n")
    
    # Check if backend is running
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"⚠️  Backend returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on port 8000")
        print("Please start the backend with: python3 start_api.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        sys.exit(1)
    
    # Run tests
    loop = asyncio.get_event_loop()
    
    # Test WebSocket
    ws_success = loop.run_until_complete(test_websocket())
    
    # Test CORS
    loop.run_until_complete(test_cors_preflight())
    
    print("\n=== Test Summary ===")
    if ws_success:
        print("✅ WebSocket connection working")
        print("\nIf the frontend still can't connect, check:")
        print("1. Browser console for specific errors")
        print("2. Browser network tab for WebSocket upgrade request")
        print("3. Any browser extensions blocking WebSocket")
        print("4. Firewall or security software")
    else:
        print("❌ WebSocket connection failed")
        print("Fix the backend issues before testing frontend")