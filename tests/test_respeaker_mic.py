#!/usr/bin/env python3
"""
Simple test script for ReSpeaker 4-Mic Array
Tests if the microphone can hear and record audio
"""

import numpy as np
import sounddevice as sd
import time
import sys
from collections import deque

def find_respeaker_device():
    """Find the ReSpeaker device index."""
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if 'ReSpeaker' in device['name'] or '4 Mic Array' in device['name']:
            return i, device
    return None, None

def test_audio_input(device_index=None, duration=10):
    """Test audio input from the microphone."""
    print("🎤 ReSpeaker Microphone Test")
    print("=" * 50)
    
    # Find device if not specified
    if device_index is None:
        device_index, device_info = find_respeaker_device()
        if device_index is None:
            print("❌ ReSpeaker device not found!")
            print("\nAvailable devices:")
            print(sd.query_devices())
            return
        else:
            print(f"✅ Found ReSpeaker at index {device_index}: {device_info['name']}")
            print(f"   Channels: {device_info['max_input_channels']}")
            print(f"   Sample Rate: {device_info['default_samplerate']} Hz")
    
    # Audio parameters
    samplerate = 16000  # 16kHz is good for speech
    channels = 1  # Use mono for simplicity
    
    print(f"\n📊 Recording for {duration} seconds...")
    print("🗣️  Please speak into the microphone!")
    print("\nVolume meter:")
    print("-" * 50)
    
    # Volume level history for visualization
    volume_history = deque(maxlen=50)
    
    def audio_callback(indata, frames, time, status):
        """Process audio in real-time."""
        if status:
            print(f"⚠️  {status}")
        
        # Calculate RMS (volume level)
        volume = np.sqrt(np.mean(indata**2))
        volume_db = 20 * np.log10(max(volume, 1e-10))  # Convert to dB
        
        # Add to history
        volume_history.append(volume)
        
        # Create volume bar
        bar_length = int(volume * 500)  # Scale for display
        bar_length = min(bar_length, 50)  # Cap at 50 chars
        
        # Color coding based on volume
        if volume < 0.01:
            level = "🔇 Silent  "
            bar_char = "░"
        elif volume < 0.05:
            level = "🔈 Quiet   "
            bar_char = "▒"
        elif volume < 0.1:
            level = "🔉 Normal  "
            bar_char = "▓"
        else:
            level = "🔊 Loud    "
            bar_char = "█"
        
        # Print volume bar
        bar = bar_char * bar_length
        spaces = " " * (50 - bar_length)
        print(f"\r{level} |{bar}{spaces}| {volume_db:+6.1f} dB", end="", flush=True)
    
    # Start recording
    try:
        with sd.InputStream(
            device=device_index,
            channels=channels,
            samplerate=samplerate,
            callback=audio_callback
        ):
            time.sleep(duration)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return
    
    # Analysis
    print("\n\n" + "=" * 50)
    print("📈 Recording Analysis:")
    
    if volume_history:
        avg_volume = np.mean(list(volume_history))
        max_volume = max(volume_history)
        
        print(f"   Average Volume: {avg_volume:.4f}")
        print(f"   Peak Volume: {max_volume:.4f}")
        
        if avg_volume < 0.001:
            print("\n⚠️  No audio detected! Check:")
            print("   - Is the ReSpeaker plugged in?")
            print("   - Are you speaking loud enough?")
            print("   - Try: alsamixer (and unmute/increase volume)")
        elif avg_volume < 0.01:
            print("\n⚠️  Very low audio level detected.")
            print("   - Try speaking louder")
            print("   - Check microphone gain in alsamixer")
        else:
            print("\n✅ Microphone is working properly!")

def test_all_channels(device_index=None):
    """Test all 4 channels of the ReSpeaker."""
    print("\n🎤 Testing all 4 channels...")
    
    if device_index is None:
        device_index, device_info = find_respeaker_device()
        if device_index is None:
            print("❌ ReSpeaker device not found!")
            return
    
    print("Recording 2 seconds from each channel...")
    
    for ch in range(4):
        print(f"\nChannel {ch + 1}:", end=" ", flush=True)
        
        def callback(indata, frames, time, status):
            volume = np.sqrt(np.mean(indata**2))
            if volume > 0.01:
                print("✅ Active", end="")
            else:
                print("🔇 Silent", end="")
        
        try:
            with sd.InputStream(
                device=device_index,
                channels=4,
                samplerate=16000,
                callback=callback
            ):
                time.sleep(2)
        except Exception as e:
            print(f"❌ Error: {e}")

def continuous_monitor(device_index=None):
    """Continuously monitor audio input (press Ctrl+C to stop)."""
    print("\n🎤 Continuous Audio Monitor")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    if device_index is None:
        device_index, _ = find_respeaker_device()
        if device_index is None:
            print("❌ ReSpeaker device not found!")
            return
    
    def callback(indata, frames, time, status):
        volume = np.sqrt(np.mean(indata**2))
        bar_length = int(volume * 100)
        bar = "█" * min(bar_length, 50)
        print(f"\r|{bar:<50}| Level: {volume:.4f}", end="", flush=True)
    
    try:
        with sd.InputStream(
            device=device_index,
            channels=1,
            samplerate=16000,
            callback=callback
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopped.")

if __name__ == "__main__":
    print("🎙️  ReSpeaker 4-Mic Array Test Tool")
    print("=" * 50)
    
    # List all audio devices
    print("\n📋 Available Audio Devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            marker = "→" if 'ReSpeaker' in device['name'] else " "
            print(f"{marker} [{i}] {device['name']} ({device['max_input_channels']} channels)")
    
    print("\n" + "=" * 50)
    
    # Run tests
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            continuous_monitor()
        elif sys.argv[1] == "--channels":
            test_all_channels()
        else:
            device_index = int(sys.argv[1])
            test_audio_input(device_index)
    else:
        # Default test
        test_audio_input()
        
        print("\n💡 Other options:")
        print("   python3 test_respeaker_mic.py --continuous  # Continuous monitoring")
        print("   python3 test_respeaker_mic.py --channels    # Test all 4 channels")
        print("   python3 test_respeaker_mic.py [device_id]   # Use specific device")