#!/usr/bin/env python3
"""
Test the ISEE Tutor API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API is {data['status']}")
        print(f"   Knowledge bases: {data['knowledge_bases']['databases']}")
        print(f"   Model available: {data['model']['available']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    print()

def test_modes():
    """Test mode functionality"""
    print("=== Testing Modes ===")
    
    # Get current mode
    response = requests.get(f"{BASE_URL}/api/companion/current-mode")
    if response.status_code == 200:
        data = response.json()
        print(f"Current mode: {data['mode']}")
        print(f"Personality: {data['config']['personality']}")
    
    # Get available modes
    response = requests.get(f"{BASE_URL}/api/companion/modes")
    if response.status_code == 200:
        data = response.json()
        print(f"Available modes: {list(data['modes'].keys())}")
    print()

def test_chat():
    """Test chat functionality"""
    print("=== Testing Chat ===")
    
    # Test tutor mode
    print("1. Testing Tutor Mode:")
    response = requests.post(f"{BASE_URL}/api/companion/chat", json={
        "message": "Can you help me with synonyms?",
        "mode": "tutor",
        "user_context": {"grade_level": 7}
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data['response'][:100]}...")
        print(f"   Mode: {data['mode']}")
    
    # Test friend mode
    print("\n2. Testing Friend Mode:")
    response = requests.post(f"{BASE_URL}/api/companion/chat", json={
        "message": "Tell me a fun fact about animals!",
        "mode": "friend",
        "user_context": {"age": 10}
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data['response'][:100]}...")
        print(f"   Mode: {data['mode']}")
    
    # Test mode switching suggestion
    print("\n3. Testing Mode Switch Suggestion:")
    response = requests.post(f"{BASE_URL}/api/companion/chat", json={
        "message": "I'm tired of studying",
        "mode": "tutor",
        "user_context": {"study_time": 45, "fatigue_level": "high"}
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data['response'][:100]}...")
        print(f"   Suggested mode: {data.get('suggested_mode', 'None')}")
    print()

def test_knowledge_query():
    """Test knowledge base queries"""
    print("=== Testing Knowledge Query ===")
    
    response = requests.post(f"{BASE_URL}/api/companion/knowledge/query", json={
        "query": "fraction",
        "limit": 3
    })
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} results for 'fraction':")
        for result in data['results']:
            print(f"   - Type: {result['type']}")
            if result['type'] == 'isee_question':
                print(f"     Q: {result['content']['question'][:50]}...")
    print()

def test_mode_switch():
    """Test explicit mode switching"""
    print("=== Testing Mode Switch ===")
    
    response = requests.post(f"{BASE_URL}/api/companion/switch-mode", json={
        "new_mode": "friend",
        "reason": "User requested break"
    })
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        print(f"   New mode: {data['new_mode']}")
    print()

def main():
    """Run all tests"""
    print("ISEE Tutor API Test Client")
    print("=" * 50)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print()
    
    try:
        test_health()
        test_modes()
        test_chat()
        test_knowledge_query()
        test_mode_switch()
        
        print("✅ All tests completed!")
        print("\nTo start the API server, run:")
        print("  python3 start_api.py")
        print("\nThen visit http://localhost:8000/docs for interactive API docs")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
        print("Start it with: python3 start_api.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()