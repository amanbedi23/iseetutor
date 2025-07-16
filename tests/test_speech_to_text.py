#!/usr/bin/env python3
"""
Real-time Speech-to-Text test for ReSpeaker
Shows live transcription as you speak
"""

import sounddevice as sd
import numpy as np
import whisper
import torch
import queue
import threading
import time
import sys
from collections import deque

class SpeechToTextTester:
    def __init__(self, model_size="base", device=None):
        """Initialize the speech recognition tester."""
        print("🎤 Real-time Speech-to-Text Test")
        print("=" * 60)
        
        # Load Whisper model
        print(f"Loading Whisper {model_size} model...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if device:
            self.device = device
        print(f"Using device: {self.device}")
        
        try:
            self.model = whisper.load_model(model_size, device=self.device)
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            sys.exit(1)
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 3  # Process 3-second chunks
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        
        # Queues and buffers
        self.audio_queue = queue.Queue()
        self.audio_buffer = np.array([], dtype=np.float32)
        self.is_recording = False
        
        # Find ReSpeaker device
        self.device_index = self.find_respeaker()
        
        # Volume visualization
        self.volume_history = deque(maxlen=30)
        
    def find_respeaker(self):
        """Find the ReSpeaker device."""
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if 'ReSpeaker' in device['name'] or '4 Mic Array' in device['name']:
                print(f"✅ Found ReSpeaker at index {i}: {device['name']}")
                return i
        print("⚠️  ReSpeaker not found, using default microphone")
        return None
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            print(f"⚠️  Audio warning: {status}")
        
        # Add audio to queue
        self.audio_queue.put(indata.copy())
        
        # Calculate volume for visualization
        volume = np.sqrt(np.mean(indata**2))
        self.volume_history.append(volume)
    
    def process_audio(self):
        """Process audio chunks for transcription."""
        print("\n🎙️  Listening... (speak clearly, pause between sentences)")
        print("Press Ctrl+C to stop\n")
        print("-" * 60)
        
        silence_threshold = 0.01
        silence_duration = 0
        
        while self.is_recording:
            try:
                # Get audio chunk from queue
                chunk = self.audio_queue.get(timeout=0.1)
                
                # Add to buffer
                self.audio_buffer = np.concatenate([self.audio_buffer, chunk.flatten()])
                
                # Check if we have enough audio
                if len(self.audio_buffer) >= self.chunk_samples:
                    # Get chunk for processing
                    audio_chunk = self.audio_buffer[:self.chunk_samples]
                    self.audio_buffer = self.audio_buffer[self.chunk_samples:]
                    
                    # Check if chunk has speech
                    volume = np.sqrt(np.mean(audio_chunk**2))
                    
                    if volume > silence_threshold:
                        # Reset silence counter
                        silence_duration = 0
                        
                        # Show volume indicator
                        vol_bar = int(volume * 200)
                        vol_bar = min(vol_bar, 30)
                        indicator = "▁" * vol_bar + " " * (30 - vol_bar)
                        print(f"\r🔊 |{indicator}| Processing...", end="", flush=True)
                        
                        # Transcribe
                        try:
                            result = self.model.transcribe(
                                audio_chunk,
                                language="en",
                                fp16=False,
                                verbose=False
                            )
                            
                            text = result["text"].strip()
                            if text and text not in [".", "Thank you.", "[Music]", "(music)"]:
                                # Clear the line and print transcription
                                print(f"\r{' ' * 60}", end="")
                                print(f"\r💬 {text}")
                                print("-" * 60)
                        
                        except Exception as e:
                            print(f"\r❌ Transcription error: {e}")
                    else:
                        # Show silence indicator
                        silence_duration += self.chunk_duration
                        dots = "." * (int(silence_duration) % 4)
                        print(f"\r🔇 Listening{dots:<4}", end="", flush=True)
                
            except queue.Empty:
                # No audio available
                pass
            except Exception as e:
                print(f"\n❌ Processing error: {e}")
    
    def run_continuous(self):
        """Run continuous speech recognition."""
        self.is_recording = True
        
        # Start processing thread
        process_thread = threading.Thread(target=self.process_audio)
        process_thread.start()
        
        # Start audio stream
        try:
            with sd.InputStream(
                device=self.device_index,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
            ):
                while self.is_recording:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
            self.is_recording = False
            process_thread.join()
            print("✅ Test complete!")
        except Exception as e:
            print(f"\n❌ Audio stream error: {e}")
            self.is_recording = False
    
    def run_single_test(self, duration=5):
        """Run a single recording test."""
        print(f"\n🎙️  Recording for {duration} seconds...")
        print("Speak clearly into the microphone!")
        print("-" * 60)
        
        # Record audio
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device_index,
            dtype=np.float32
        )
        
        # Show progress
        for i in range(duration):
            time.sleep(1)
            print(f"\r⏱️  {i+1}/{duration} seconds...", end="", flush=True)
        
        sd.wait()
        print("\n\n🔄 Processing audio...")
        
        # Transcribe
        try:
            audio = recording.flatten()
            result = self.model.transcribe(audio, language="en", fp16=False)
            
            print("\n📝 Transcription:")
            print("-" * 60)
            print(result["text"])
            print("-" * 60)
            
            # Show segments with timestamps
            if result.get("segments"):
                print("\n⏱️  Segments:")
                for segment in result["segments"]:
                    start = segment["start"]
                    end = segment["end"]
                    text = segment["text"].strip()
                    if text:
                        print(f"  [{start:5.1f}s - {end:5.1f}s] {text}")
        
        except Exception as e:
            print(f"❌ Transcription error: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Speech-to-Text Tester")
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--device",
        choices=["cuda", "cpu"],
        help="Force CPU or CUDA (auto-detect by default)"
    )
    parser.add_argument(
        "--single",
        type=int,
        metavar="SECONDS",
        help="Run single recording test for N seconds"
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = SpeechToTextTester(model_size=args.model, device=args.device)
    
    if args.single:
        # Single recording test
        tester.run_single_test(duration=args.single)
    else:
        # Continuous mode
        print("\n📌 Tips for best results:")
        print("  • Speak clearly and naturally")
        print("  • Pause briefly between sentences")
        print("  • Stay 20-30cm from the microphone")
        print("  • Minimize background noise")
        
        tester.run_continuous()


if __name__ == "__main__":
    main()