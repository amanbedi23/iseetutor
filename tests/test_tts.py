#!/usr/bin/env python3
"""
Test TTS (Text-to-Speech) functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.audio.tts_engine import PiperTTSEngine, synthesize_speech
import sounddevice as sd
import numpy as np
import wave
import io
import time

def play_audio(audio_data: bytes):
    """Play WAV audio data"""
    # Read WAV data
    wav_buffer = io.BytesIO(audio_data)
    with wave.open(wav_buffer, 'rb') as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
        rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        
    # Convert to numpy array
    audio_array = np.frombuffer(frames, dtype=np.int16)
    if channels == 2:
        audio_array = audio_array.reshape(-1, 2)
    
    # Play audio
    sd.play(audio_array, rate)
    sd.wait()

def test_basic_tts():
    """Test basic TTS synthesis"""
    print("\n=== Testing Basic TTS ===")
    
    engine = PiperTTSEngine()
    
    test_phrases = [
        "Hello! I'm your ISEE Tutor. How can I help you today?",
        "Great job! You got the answer correct!",
        "Let's practice some vocabulary. What's a synonym for happy?",
        "Remember, the ISEE test has four sections: verbal reasoning, quantitative reasoning, reading comprehension, and mathematics achievement.",
        "Would you like to try another practice question?"
    ]
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"\n{i}. Synthesizing: '{phrase}'")
        
        start_time = time.time()
        audio_data = engine.synthesize(phrase)
        synthesis_time = time.time() - start_time
        
        print(f"   Synthesis time: {synthesis_time:.3f} seconds")
        print(f"   Audio size: {len(audio_data)} bytes")
        
        if audio_data:
            print("   Playing audio...")
            play_audio(audio_data)
            time.sleep(0.5)

def test_voice_speeds():
    """Test different voice speeds"""
    print("\n=== Testing Voice Speeds ===")
    
    engine = PiperTTSEngine()
    test_text = "The quick brown fox jumps over the lazy dog."
    
    speeds = [0.7, 1.0, 1.3]
    speed_names = ["Slow", "Normal", "Fast"]
    
    for speed, name in zip(speeds, speed_names):
        print(f"\n{name} speed ({speed}x): '{test_text}'")
        
        engine.set_voice_speed(speed)
        audio_data = engine.synthesize(test_text)
        
        if audio_data:
            print("   Playing audio...")
            play_audio(audio_data)
            time.sleep(0.5)

def test_educational_content():
    """Test TTS with educational content"""
    print("\n=== Testing Educational Content ===")
    
    engine = PiperTTSEngine()
    
    educational_texts = [
        "Let's solve this math problem together. If x plus 5 equals 12, what is x?",
        "The word 'benevolent' means showing kindness and goodwill. Can you use it in a sentence?",
        "In this reading passage, the main character faces a difficult decision. Let's discuss what you would do.",
        "Remember to read each question carefully before choosing your answer.",
        "Excellent work! You've completed 5 practice questions. Your accuracy is 80 percent."
    ]
    
    for text in educational_texts:
        print(f"\nEducational: '{text[:60]}...'")
        
        audio_data = engine.synthesize(text)
        
        if audio_data:
            print("   Playing audio...")
            play_audio(audio_data)
            time.sleep(1)

def test_cache_performance():
    """Test TTS caching performance"""
    print("\n=== Testing Cache Performance ===")
    
    engine = PiperTTSEngine()
    test_text = "This is a test of the caching system."
    
    # First synthesis (uncached)
    print(f"\nFirst synthesis (uncached): '{test_text}'")
    start_time = time.time()
    audio_data1 = engine.synthesize(test_text)
    uncached_time = time.time() - start_time
    print(f"   Time: {uncached_time:.3f} seconds")
    
    # Second synthesis (cached)
    print(f"\nSecond synthesis (cached): '{test_text}'")
    start_time = time.time()
    audio_data2 = engine.synthesize(test_text)
    cached_time = time.time() - start_time
    print(f"   Time: {cached_time:.3f} seconds")
    print(f"   Speedup: {uncached_time/cached_time:.1f}x")
    
    # Verify same audio
    assert audio_data1 == audio_data2, "Cached audio should be identical"
    print("   ✓ Cache working correctly")

def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    engine = PiperTTSEngine()
    
    # Empty text
    print("\nEmpty text:")
    audio = engine.synthesize("")
    print(f"   Result: {len(audio)} bytes (should be 0)")
    
    # Very long text
    print("\nVery long text:")
    long_text = "This is a test. " * 100
    audio = engine.synthesize(long_text[:500])  # Limit for testing
    print(f"   Result: {len(audio)} bytes")

def main():
    """Run all TTS tests"""
    print("ISEE Tutor TTS Test Suite")
    print("=" * 50)
    
    try:
        # Check if Piper is installed
        try:
            import piper
            print("✓ Piper TTS Python module is installed")
        except ImportError:
            print("ERROR: Piper Python module is not installed")
            print("Install with: pip install piper-tts")
            return
        
        # Run tests
        test_basic_tts()
        test_voice_speeds()
        test_educational_content()
        test_cache_performance()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("All TTS tests completed successfully!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()