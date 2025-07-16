#!/usr/bin/env python3
"""
Quick Speech-to-Text test
Minimal setup, fast testing
"""

import speech_recognition as sr
import time
import sys

print("🎤 Quick Speech-to-Text Test")
print("=" * 50)

# Initialize recognizer
recognizer = sr.Recognizer()

# Find microphone
mic_list = sr.Microphone.list_microphone_names()
mic_index = None

print("\n📋 Available microphones:")
for i, name in enumerate(mic_list):
    if 'ReSpeaker' in name or '4 Mic Array' in name:
        mic_index = i
        print(f"→ [{i}] {name} ✅")
    else:
        print(f"  [{i}] {name}")

if mic_index is None:
    print("\n⚠️  ReSpeaker not found, using default mic")
    mic = sr.Microphone()
else:
    print(f"\n✅ Using ReSpeaker at index {mic_index}")
    mic = sr.Microphone(device_index=mic_index)

print("\n🎙️  Starting continuous recognition...")
print("Speak and see your words appear!")
print("Press Ctrl+C to stop\n")
print("-" * 50)

# Adjust for ambient noise
with mic as source:
    print("🔧 Adjusting for background noise... (1 second)")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("✅ Ready!\n")

# Continuous recognition
try:
    with mic as source:
        while True:
            try:
                # Listen with timeout
                print("🔇 Listening...", end="\r", flush=True)
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                print("🔄 Processing...", end="\r", flush=True)
                
                # Try multiple recognition engines
                try:
                    # Google Speech Recognition (free, no API key needed)
                    text = recognizer.recognize_google(audio)
                    print(f"💬 {text:<50}")
                except sr.UnknownValueError:
                    # Couldn't understand audio
                    print("❓ (couldn't understand)                    ", end="\r", flush=True)
                except sr.RequestError as e:
                    # API error
                    print(f"❌ API Error: {e}")
                    print("Trying offline engine...")
                    
                    # Try offline engine (Sphinx)
                    try:
                        text = recognizer.recognize_sphinx(audio)
                        print(f"💬 [Offline] {text:<50}")
                    except:
                        print("❌ Offline recognition also failed")
                        
            except sr.WaitTimeoutError:
                # No speech detected
                pass
                
except KeyboardInterrupt:
    print("\n\n✅ Test stopped!")
    
print("\n💡 Tips:")
print("  • For better accuracy, install Whisper-based test:")
print("    python3 test_speech_to_text.py")
print("  • This uses Google's free API (requires internet)")
print("  • For offline, install: pip install pocketsphinx")