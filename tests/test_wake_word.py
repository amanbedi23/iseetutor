#!/usr/bin/env python3
"""Test wake word detection capabilities"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_available_libraries():
    """Test which wake word detection libraries are available"""
    print("Checking available wake word detection libraries...")
    print("-" * 50)
    
    libraries = {
        "pvporcupine": "Picovoice Porcupine",
        "openwakeword": "OpenWakeWord",
        "snowboy": "Snowboy (deprecated)",
        "pocketsphinx": "PocketSphinx",
        "vosk": "Vosk Speech Recognition"
    }
    
    available = []
    
    for lib, name in libraries.items():
        try:
            if lib == "pvporcupine":
                import pvporcupine
                print(f"✅ {name}: Available (version {pvporcupine.__version__})")
                available.append(lib)
            elif lib == "openwakeword":
                import openwakeword
                print(f"✅ {name}: Available")
                available.append(lib)
            elif lib == "snowboy":
                import snowboydecoder
                print(f"✅ {name}: Available (deprecated)")
                available.append(lib)
            elif lib == "pocketsphinx":
                import pocketsphinx
                print(f"✅ {name}: Available")
                available.append(lib)
            elif lib == "vosk":
                import vosk
                print(f"✅ {name}: Available (version {vosk.VERSION})")
                available.append(lib)
        except ImportError:
            print(f"❌ {name}: Not installed")
        except Exception as e:
            print(f"⚠️  {name}: Error - {e}")
    
    return available

def test_simple_keyword_detection():
    """Test simple keyword detection using existing audio pipeline"""
    print("\nTesting simple keyword detection with audio pipeline...")
    print("-" * 50)
    
    try:
        from src.core.audio.audio_processor import AudioProcessor
        import numpy as np
        
        # Create audio processor
        processor = AudioProcessor(
            sample_rate=16000,
            channels=1,
            vad_aggressiveness=2
        )
        
        print("Audio processor created successfully")
        print("This can be extended with wake word detection")
        
        # Simulate checking for wake word in audio buffer
        # In real implementation, this would use a wake word library
        def simple_keyword_check(audio_data, keyword="hey tutor"):
            """Placeholder for wake word detection"""
            # Real implementation would use:
            # - Porcupine for efficient wake word detection
            # - OpenWakeWord for open-source alternative
            # - Custom model trained on "Hey Tutor"
            return False
        
        print("\nWake word detection flow:")
        print("1. Continuous audio monitoring with VAD")
        print("2. Buffer audio when speech detected")  
        print("3. Check buffer for wake word")
        print("4. Trigger action if wake word detected")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def suggest_implementation():
    """Suggest wake word implementation approach"""
    print("\nRecommended Wake Word Implementation:")
    print("=" * 50)
    
    print("\n1. Picovoice Porcupine (Recommended for production)")
    print("   - High accuracy, low latency")
    print("   - Supports custom wake words")
    print("   - Free tier available")
    print("   - Install: pip install pvporcupine")
    print("   - Requires access key from Picovoice Console")
    
    print("\n2. OpenWakeWord (Open source alternative)")
    print("   - Completely free and open source")
    print("   - Good accuracy with pre-trained models")
    print("   - Can train custom models")
    print("   - Install: pip install openwakeword")
    
    print("\n3. Vosk + Custom Logic")
    print("   - Use Vosk for continuous speech recognition")
    print("   - Check transcriptions for wake word")
    print("   - Higher resource usage but very flexible")
    print("   - Install: pip install vosk")
    
    print("\n4. Custom Implementation")
    print("   - Use existing audio pipeline with VAD")
    print("   - Implement simple pattern matching")
    print("   - Or train small neural network for wake word")

if __name__ == "__main__":
    print("Wake Word Detection Test Suite")
    print("=" * 50)
    
    # Test 1: Check available libraries
    available = test_available_libraries()
    
    # Test 2: Test simple detection flow
    if test_simple_keyword_detection():
        print("\n✅ Basic audio pipeline ready for wake word integration")
    
    # Provide implementation suggestions
    suggest_implementation()
    
    if not available:
        print("\n⚠️  No wake word libraries currently installed")
        print("Install one of the recommended libraries to proceed")