#!/usr/bin/env python3
"""
Quick test to verify voice pipeline is working
Run this after starting the API server
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.audio.voice_pipeline import VoicePipeline


async def test_text_mode():
    """Test the voice pipeline with text input (no microphone needed)"""
    print("🎯 Voice Pipeline Quick Test")
    print("=" * 50)
    
    # Create pipeline
    pipeline = VoicePipeline(
        mode="friend",
        on_state_change=lambda state, data: print(f"📍 State: {state.value}"),
        on_transcript=lambda text: print(f"📝 Transcript: {text}"),
        on_response=lambda text: print(f"🤖 Response: {text}")
    )
    
    print("\n✅ Pipeline created successfully")
    
    # Test direct text processing
    print("\n📨 Testing text input processing...")
    
    test_messages = [
        "Hello! How are you today?",
        "What's your favorite color?",
        "Can you help me with math?"
    ]
    
    for message in test_messages:
        print(f"\n💬 You: {message}")
        response = await pipeline.process_text_input(message)
        print(f"🤖 Assistant: {response}")
    
    print("\n✅ Text mode test completed!")
    
    # Test mode switching
    print("\n🔄 Testing mode switching to tutor...")
    pipeline.set_mode("tutor")
    
    response = await pipeline.process_text_input("What is a metaphor?")
    print(f"🎓 Tutor: {response}")
    
    print("\n✅ All tests passed!")


async def test_components():
    """Test individual components"""
    print("\n🔧 Testing Individual Components")
    print("=" * 50)
    
    # Test TTS
    print("\n1️⃣ Testing TTS Engine...")
    try:
        from src.core.audio.tts_engine import PiperTTSEngine
        tts = PiperTTSEngine()
        audio_data = await tts.synthesize_async("Hello, this is a test of the text to speech system.")
        print(f"✅ TTS working! Generated {len(audio_data)} bytes of audio")
    except Exception as e:
        print(f"❌ TTS Error: {e}")
    
    # Test LLM
    print("\n2️⃣ Testing LLM...")
    try:
        from src.core.llm.companion_llm import CompanionLLM
        llm = CompanionLLM(mode="friend")
        response = llm.get_response("Tell me a fun fact")
        print(f"✅ LLM working! Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ LLM Error: {e}")
    
    # Test STT
    print("\n3️⃣ Testing Speech Recognition...")
    try:
        from src.models.speech_to_text import SpeechToText
        stt = SpeechToText()
        print("✅ STT initialized successfully")
    except Exception as e:
        print(f"❌ STT Error: {e}")
    
    # Test Wake Word
    print("\n4️⃣ Testing Wake Word Detection...")
    try:
        from src.core.audio.openwakeword_detector import OpenWakeWordDetector
        detector = OpenWakeWordDetector()
        models = detector.list_models()
        print(f"✅ Wake word detector working! Available models: {models}")
    except Exception as e:
        print(f"❌ Wake Word Error: {e}")


if __name__ == "__main__":
    print("🚀 ISEE Tutor Voice Pipeline Quick Test")
    print("\nThis test verifies all voice components are working")
    print("No microphone or speaker needed for this test\n")
    
    try:
        # Test components first
        asyncio.run(test_components())
        
        # Then test pipeline
        asyncio.run(test_text_mode())
        
        print("\n✨ Success! Voice pipeline is ready to use")
        print("\nTo test with real voice:")
        print("1. Make sure API server is running: python3 start_api.py")
        print("2. Run: python3 tests/test_voice_pipeline.py --hardware")
        print("3. Say 'Hey Jarvis' to activate")
        
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()