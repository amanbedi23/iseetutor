#!/usr/bin/env python3
"""Test audio pipeline with noise cancellation"""

import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.audio.audio_processor import AudioProcessor, BeamformingProcessor

def visualize_audio(original, processed, sample_rate):
    """Visualize original vs processed audio"""
    plt.figure(figsize=(12, 8))
    
    # Time axis
    time_orig = np.arange(len(original)) / sample_rate
    time_proc = np.arange(len(processed)) / sample_rate
    
    # Plot waveforms
    plt.subplot(2, 1, 1)
    plt.plot(time_orig, original, label='Original', alpha=0.7)
    plt.plot(time_proc, processed, label='Processed', alpha=0.7)
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Audio Waveform Comparison')
    plt.legend()
    plt.grid(True)
    
    # Plot spectrograms
    plt.subplot(2, 1, 2)
    plt.specgram(original, Fs=sample_rate, scale='dB', cmap='viridis')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Original Audio Spectrogram')
    plt.colorbar(label='Power (dB)')
    
    plt.tight_layout()
    plt.savefig(f'audio_pipeline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    print("Visualization saved")

def test_basic_audio_processor():
    """Test basic audio processor with noise cancellation"""
    print("Testing Basic Audio Processor")
    print("-" * 50)
    
    # Create processor
    processor = AudioProcessor(
        sample_rate=16000,
        channels=1,
        vad_aggressiveness=2,
        noise_reduction_strength=0.7
    )
    
    # Simulate audio instead of recording (for testing without mic)
    print("Simulating audio with noise and speech...")
    
    sample_rate = 16000
    duration = 5  # seconds
    t = np.linspace(0, duration, duration * sample_rate)
    
    # Create synthetic audio: noise + speech
    # First 2 seconds: just noise
    noise = np.random.randn(len(t)) * 0.05
    
    # Next 3 seconds: speech-like signal (varying frequency)
    speech_envelope = np.zeros_like(t)
    speech_start = 2 * sample_rate
    speech_envelope[speech_start:] = np.sin(2 * np.pi * 0.5 * t[speech_start:]) * 0.5 + 0.5
    
    # Speech signal (modulated sine waves)
    speech = np.zeros_like(t)
    for freq in [200, 300, 400, 500]:  # Fundamental frequencies
        speech += np.sin(2 * np.pi * freq * t) * speech_envelope * 0.2
    
    # Combined signal
    audio_signal = noise + speech
    
    # Process in frames
    recorded_audio = []
    processed_frames = []
    speech_detected = []
    
    frame_size = processor.frame_size
    for i in range(0, len(audio_signal) - frame_size, frame_size):
        frame = audio_signal[i:i + frame_size]
        frame_bytes = (frame * 32768).astype(np.int16).tobytes()
        
        is_speech, processed = processor.process_frame(frame_bytes)
        
        recorded_audio.extend(frame)
        processed_frames.extend(processed)
        speech_detected.append(is_speech)
        
        if is_speech:
            print("*", end="", flush=True)
        else:
            print(".", end="", flush=True)
    
    print("\nProcessing complete!")
    
    processed_audio = np.array(processed_frames)
    
    print(f"\nResults:")
    print(f"- Total frames processed: {len(speech_detected)}")
    print(f"- Speech frames detected: {sum(speech_detected)}")
    print(f"- Speech percentage: {sum(speech_detected) / len(speech_detected) * 100:.1f}%")
    print(f"- Audio buffer size: {len(processed_audio)} samples")
    
    return audio_signal[:len(processed_audio)], processed_audio

def test_beamforming_processor():
    """Test beamforming processor for ReSpeaker 4-mic array"""
    print("\nTesting Beamforming Processor")
    print("-" * 50)
    
    # ReSpeaker 4-mic array positions (approximate, in meters)
    # Square configuration with 65mm spacing
    mic_positions = [
        (-0.0325, -0.0325, 0),  # Mic 1
        (0.0325, -0.0325, 0),   # Mic 2
        (0.0325, 0.0325, 0),    # Mic 3
        (-0.0325, 0.0325, 0),   # Mic 4
    ]
    
    # Create beamforming processor
    processor = BeamformingProcessor(
        mic_positions=mic_positions,
        sample_rate=16000,
        channels=4,  # 4 microphones
        vad_aggressiveness=3,
        noise_reduction_strength=0.8
    )
    
    print(f"Beamforming processor configured for {processor.num_mics} microphones")
    print(f"Target direction: {processor.target_direction}")
    
    # Calculate delays
    delays = processor.calculate_delays(processor.target_direction)
    print(f"Calculated delays (ms): {delays * 1000}")
    
    # Simulate multi-channel audio (for testing without actual 4-mic input)
    duration = 2  # seconds
    sample_rate = 16000
    t = np.linspace(0, duration, duration * sample_rate)
    
    # Create test signals with different delays
    test_signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    multi_channel = np.zeros((len(t), 4))
    
    for i in range(4):
        # Add slight delay to each channel
        delay_samples = int(i * sample_rate * 0.0001)  # 0.1ms increments
        if delay_samples < len(t):
            multi_channel[delay_samples:, i] = test_signal[:-delay_samples if delay_samples > 0 else None]
    
    # Apply beamforming
    beamformed = processor.apply_beamforming(multi_channel)
    
    print(f"Beamforming applied: {len(beamformed)} samples output")
    print(f"Signal energy ratio: {np.sum(beamformed**2) / np.sum(test_signal**2):.3f}")
    
    return test_signal, beamformed

def test_realtime_performance():
    """Test real-time performance metrics"""
    print("\nTesting Real-time Performance")
    print("-" * 50)
    
    processor = AudioProcessor(
        sample_rate=16000,
        frame_duration_ms=30
    )
    
    # Generate test frames
    frame_size = processor.frame_size
    num_frames = 100
    
    processing_times = []
    
    for i in range(num_frames):
        # Generate random audio frame
        frame = np.random.randn(frame_size) * 0.1
        frame_bytes = (frame * 32768).astype(np.int16).tobytes()
        
        # Measure processing time
        start_time = time.time()
        is_speech, processed = processor.process_frame(frame_bytes)
        end_time = time.time()
        
        processing_times.append(end_time - start_time)
    
    # Calculate statistics
    avg_time = np.mean(processing_times) * 1000  # Convert to ms
    max_time = np.max(processing_times) * 1000
    min_time = np.min(processing_times) * 1000
    
    print(f"Frame duration: {processor.frame_duration_ms} ms")
    print(f"Average processing time: {avg_time:.2f} ms")
    print(f"Max processing time: {max_time:.2f} ms")
    print(f"Min processing time: {min_time:.2f} ms")
    print(f"Real-time factor: {avg_time / processor.frame_duration_ms:.2f}x")
    
    if avg_time < processor.frame_duration_ms:
        print("✅ Real-time processing achieved!")
    else:
        print("❌ Processing too slow for real-time")

if __name__ == "__main__":
    print("Audio Pipeline Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Basic audio processing
        original, processed = test_basic_audio_processor()
        
        # Test 2: Beamforming
        test_signal, beamformed = test_beamforming_processor()
        
        # Test 3: Performance
        test_realtime_performance()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()