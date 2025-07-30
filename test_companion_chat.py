#!/usr/bin/env python3
"""Test the companion chat API endpoint"""

import requests
import json

# API endpoint
url = "http://localhost:8000/api/companion/chat"

# Test messages
test_messages = [
    {
        "message": "Hello! Can you help me with math?",
        "mode": "tutor",
        "user_context": {"age": 12, "grade": 7}
    },
    {
        "message": "What's your favorite animal?",
        "mode": "friend",
        "user_context": {"age": 10, "grade": 5}
    },
    {
        "message": "I need help with fractions",
        "mode": "hybrid",
        "user_context": {"age": 11, "grade": 6}
    }
]

# Test each message
for test_data in test_messages:
    print(f"\n{'='*60}")
    print(f"Testing {test_data['mode']} mode:")
    print(f"Message: {test_data['message']}")
    print(f"User: Age {test_data['user_context']['age']}, Grade {test_data['user_context']['grade']}")
    print(f"{'='*60}")
    
    try:
        # Send request
        response = requests.post(url, json=test_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse: {data['response']}")
            print(f"\nMetadata:")
            print(f"- Mode: {data['mode']}")
            print(f"- Source: {data['source']}")
            if 'model_metadata' in data:
                print(f"- Model: {data.get('model_metadata', {}).get('model', 'N/A')}")
                print(f"- Tokens: {data.get('model_metadata', {}).get('tokens_used', 'N/A')}")
            if 'suggested_mode' in data and data['suggested_mode']:
                print(f"- Suggested mode switch: {data['suggested_mode']}")
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\nException: {e}")

print("\n\nDone testing!")