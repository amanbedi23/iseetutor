#!/usr/bin/env python3
"""
Audio handling module for ISEE Tutor
Manages audio input/output, including mic array and speakers
"""

import os
import queue
import threading
import numpy as np
import sounddevice as sd
import logging
from typing import Optional, Callable, Tuple

logger = logging.getLogger(__name__)

class AudioManager:
    """Manages audio input and output for the ISEE Tutor"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 input_device: Optional[int] = None,
                 output_device: Optional[int] = None):
        """
        Initialize audio manager
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks
            input_device: Input device ID (None for default)
            output_device: Output device ID (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.input_device = input_device
        self.output_device = output_device
        
        # Audio queues
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.is_playing = False
        
        # Callbacks
        self.audio_callback: Optional[Callable] = None
        
        # Initialize devices
        self._init_devices()
        
    def _init_devices(self):
        """Initialize and verify audio devices"""
        try:
            # List available devices
            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for i, device in enumerate(devices):
                logger.info(f"  {i}: {device['name']} - {device['channels']} channels")
            
            # Find ReSpeaker if available
            for i, device in enumerate(devices):
                if 'respeaker' in device['name'].lower() and device['max_input_channels'] > 0:
                    self.input_device = i
                    logger.info(f"Found ReSpeaker mic array at index {i}")
                    break
                    
        except Exception as e:
            logger.error(f"Error initializing audio devices: {e}")
    
    def list_devices(self) -> list:
        """List all available audio devices"""
        return sd.query_devices()
    
    def start_recording(self, callback: Optional[Callable] = None) -> None:
        """
        Start recording audio
        
        Args:
            callback: Function to call with audio chunks
        """
        if self.is_recording:
            logger.warning("Already recording")
            return
            
        self.audio_callback = callback
        self.is_recording = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio input status: {status}")
            
            # Copy audio data
            audio_chunk = indata.copy()
            
            # Add to queue
            self.audio_queue.put(audio_chunk)
            
            # Call callback if provided
            if self.audio_callback:
                self.audio_callback(audio_chunk)
        
        # Start recording stream
        self.stream = sd.InputStream(
            device=self.input_device,
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            callback=audio_callback
        )
        self.stream.start()
        logger.info("Started audio recording")
    
    def stop_recording(self) -> np.ndarray:
        """
        Stop recording and return all recorded audio
        
        Returns:
            Numpy array of recorded audio
        """
        if not self.is_recording:
            logger.warning("Not currently recording")
            return np.array([])
        
        self.is_recording = False
        self.stream.stop()
        self.stream.close()
        
        # Collect all audio from queue
        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())
        
        if audio_chunks:
            return np.concatenate(audio_chunks, axis=0)
        return np.array([])
    
    def play_audio(self, audio_data: np.ndarray, blocking: bool = True) -> None:
        """
        Play audio data
        
        Args:
            audio_data: Numpy array of audio data
            blocking: Whether to block until playback completes
        """
        try:
            sd.play(audio_data, self.sample_rate, device=self.output_device)
            if blocking:
                sd.wait()
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def record_for_duration(self, duration: float) -> np.ndarray:
        """
        Record audio for a specific duration
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Numpy array of recorded audio
        """
        logger.info(f"Recording for {duration} seconds...")
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.input_device
        )
        sd.wait()
        return recording
    
    def get_volume_level(self) -> float:
        """
        Get current volume level (0-1)
        
        Returns:
            Current volume level
        """
        if not self.audio_queue.empty():
            chunk = self.audio_queue.queue[-1]  # Get last chunk without removing
            return float(np.sqrt(np.mean(chunk**2)))  # RMS
        return 0.0
    
    def test_audio(self) -> Tuple[bool, bool]:
        """
        Test audio input and output
        
        Returns:
            Tuple of (input_working, output_working)
        """
        input_working = False
        output_working = False
        
        try:
            # Test output with a beep
            duration = 0.5
            frequency = 440  # A4 note
            t = np.linspace(0, duration, int(self.sample_rate * duration))
            beep = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            logger.info("Testing audio output with beep...")
            self.play_audio(beep)
            output_working = True
            
        except Exception as e:
            logger.error(f"Audio output test failed: {e}")
        
        try:
            # Test input
            logger.info("Testing audio input...")
            test_recording = self.record_for_duration(1.0)
            if test_recording.size > 0:
                volume = float(np.sqrt(np.mean(test_recording**2)))
                logger.info(f"Audio input test - volume level: {volume}")
                input_working = True
        except Exception as e:
            logger.error(f"Audio input test failed: {e}")
        
        return input_working, output_working


# Simple test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Audio Manager...")
    audio = AudioManager()
    
    print("\nAvailable devices:")
    for i, device in enumerate(audio.list_devices()):
        print(f"{i}: {device['name']}")
    
    print("\nTesting audio I/O...")
    input_ok, output_ok = audio.test_audio()
    
    print(f"\nResults:")
    print(f"Input working: {input_ok}")
    print(f"Output working: {output_ok}")
    
    if input_ok:
        print("\nRecording 3 seconds of audio...")
        recording = audio.record_for_duration(3.0)
        print(f"Recorded {recording.shape[0]} samples")
        
        print("Playing back recording...")
        audio.play_audio(recording)
        print("Done!")