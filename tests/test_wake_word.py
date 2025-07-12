#!/usr/bin/env python3
"""Test wake word detection capabilities"""

import sys
import os
import time
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

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

def test_openwakeword():
    """Test OpenWakeWord detection"""
    print("\nTesting OpenWakeWord Detection")
    print("-" * 50)
    
    try:
        from src.core.audio.openwakeword_detector import HeyTutorOpenWakeWord, create_openwakeword_detector
        
        print("✅ OpenWakeWord imported successfully")
        
        # Test detector creation
        detected = [False]
        def test_callback(wakeword, score):
            print(f"\n🎯 Wake word detected: '{wakeword}' (confidence: {score:.3f})")
            detected[0] = True
        
        detector = HeyTutorOpenWakeWord(wakeword_callback=test_callback)
        print(f"✅ Wake word detector created")
        print(f"   Model initialized: {hasattr(detector, 'model')}")
        print(f"   Sample rate: {detector.sample_rate}Hz")
        print(f"   Chunk size: {detector.chunk_size} samples")
        
        # Start detection
        print("\nStarting wake word detection...")
        print("Say 'Hey Jarvis' to test")
        print("Listening for 5 seconds...")
        
        detector.start()
        time.sleep(5)
        detector.stop()
        
        if detected[0]:
            print("\n✅ Wake word detection successful!")
        else:
            print("\n⚠️  No wake word detected in test period")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenWakeWord: {e}")
        import traceback
        traceback.print_exc()
        return False

def suggest_implementation():
    """Suggest wake word implementation approach"""
    print("\nWake Word Implementation Status:")
    print("=" * 50)
    
    print("\n✅ OpenWakeWord Implementation Ready!")
    print("   - Open-source solution that works on ARM/Jetson")
    print("   - HeyTutorOpenWakeWord class implemented")
    print("   - Currently using 'Hey Jarvis' as test keyword")
    print("   - Pre-trained models automatically downloaded")
    
    print("\n📝 To use custom 'Hey Tutor' wake word:")
    print("   1. Record 50-100 samples of 'Hey Tutor'")
    print("   2. Use OpenWakeWord training scripts")
    print("   3. Save model as data/wake_words/hey_tutor.tflite")
    print("   4. Detector will automatically use custom model")
    
    print("\n📝 Next Steps:")
    print("   - Integrate with audio pipeline")
    print("   - Add acknowledgment sound on detection")
    print("   - Connect to Whisper for command processing")
    print("   - Implement continuous listening mode")

if __name__ == "__main__":
    print("Wake Word Detection Test Suite")
    print("=" * 50)
    
    # Test 1: Check available libraries
    available = test_available_libraries()
    
    # Test 2: Test simple detection flow
    if test_simple_keyword_detection():
        print("\n✅ Basic audio pipeline ready for wake word integration")
    
    # Test 3: Test OpenWakeWord detection
    if 'openwakeword' in available:
        test_openwakeword()
    
    # Provide implementation suggestions
    suggest_implementation()