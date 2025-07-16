#!/usr/bin/env python3
"""
Test LLM chat functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import requests
import json
from src.core.llm import get_companion_llm

def test_direct_llm():
    """Test LLM directly"""
    print("\n=== Testing Direct LLM ===")
    
    try:
        llm = get_companion_llm()
        print("✓ LLM loaded successfully")
        
        # Test tutor mode
        print("\n1. Testing TUTOR mode:")
        response, metadata = llm.generate_response(
            "What is a synonym for 'happy'?",
            mode="tutor",
            context={"grade_level": "middle school", "subject": "verbal reasoning"}
        )
        print(f"Response: {response}")
        print(f"Metadata: {metadata}")
        
        # Test friend mode
        print("\n2. Testing FRIEND mode:")
        response, metadata = llm.generate_response(
            "Tell me a fun fact about space!",
            mode="friend",
            context={"age": 10, "interests": "space, science"}
        )
        print(f"Response: {response}")
        print(f"Metadata: {metadata}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def test_api_chat():
    """Test chat via API"""
    print("\n=== Testing API Chat ===")
    
    base_url = "http://localhost:8000"
    
    # Test current mode
    try:
        response = requests.get(f"{base_url}/api/companion/current-mode")
        print(f"Current mode: {response.json()}")
    except Exception as e:
        print(f"Error getting current mode: {e}")
        return
    
    # Test chat in tutor mode
    print("\n1. Testing chat in TUTOR mode:")
    try:
        response = requests.post(
            f"{base_url}/api/companion/chat",
            json={
                "message": "Can you help me with fractions?",
                "mode": "tutor",
                "user_context": {
                    "grade_level": "middle school",
                    "subject": "mathematics"
                }
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['response']}")
            print(f"Source: {data['source']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test chat in friend mode
    print("\n2. Testing chat in FRIEND mode:")
    try:
        response = requests.post(
            f"{base_url}/api/companion/chat",
            json={
                "message": "What's your favorite animal?",
                "mode": "friend",
                "user_context": {
                    "age": 10,
                    "interests": "animals, nature"
                }
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['response']}")
            print(f"Source: {data['source']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run tests"""
    print("ISEE Tutor LLM Chat Test")
    print("=" * 50)
    
    # Test direct LLM first
    test_direct_llm()
    
    # Ask if user wants to test API
    print("\n" + "=" * 50)
    response = input("\nTest API endpoints? (requires API server running) [y/N]: ")
    if response.lower() == 'y':
        test_api_chat()
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()