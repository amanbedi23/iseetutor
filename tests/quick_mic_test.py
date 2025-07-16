#!/usr/bin/env python3
"""
Quick and simple microphone test
Just shows if the mic is picking up sound
"""

import sounddevice as sd
import numpy as np
import time

print("🎤 Quick Microphone Test")
print("Speak into the mic - you should see the bars move!")
print("Press Ctrl+C to stop\n")

# Find ReSpeaker or use default
devices = sd.query_devices()
device = None
for i, d in enumerate(devices):
    if 'ReSpeaker' in d['name'] and d['max_input_channels'] > 0:
        device = i
        print(f"✅ Using ReSpeaker: {d['name']}")
        break

if device is None:
    print("⚠️  ReSpeaker not found, using default mic")

print("\nSound Level:")
print("-" * 52)

def callback(indata, frames, time, status):
    # Get volume level
    volume = np.sqrt(np.mean(indata**2)) * 100
    
    # Create visual bar
    bar = int(volume)
    if bar > 50: bar = 50
    
    # Show the bar
    visual = "█" * bar + "░" * (50 - bar)
    
    # Color the output based on volume
    if volume < 1:
        status = "🔇"
    elif volume < 10:
        status = "🔈"  
    elif volume < 30:
        status = "🔉"
    else:
        status = "🔊"
    
    print(f"\r{status} |{visual}|", end="", flush=True)

# Start listening
try:
    with sd.InputStream(device=device, channels=1, callback=callback, samplerate=16000):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n✅ Test complete!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check if ReSpeaker is connected: lsusb")
    print("2. Check audio devices: python3 -c 'import sounddevice; print(sounddevice.query_devices())'")
    print("3. Try running with sudo")
    print("4. Check alsamixer settings")