"""
Wake word detection using Picovoice Porcupine
"""

import os
import struct
import pyaudio
import pvporcupine
import numpy as np
import logging
from typing import Optional, Callable, List
import threading
import queue
from pathlib import Path

logger = logging.getLogger(__name__)

class WakeWordDetector:
    """Detects wake words using Porcupine"""
    
    def __init__(
        self,
        access_key: str,
        keywords: Optional[List[str]] = None,
        keyword_paths: Optional[List[str]] = None,
        sensitivities: Optional[List[float]] = None,
        callback: Optional[Callable] = None
    ):
        """
        Initialize wake word detector
        
        Args:
            access_key: Porcupine access key
            keywords: List of built-in keywords to detect
            keyword_paths: Paths to custom keyword model files
            sensitivities: Detection sensitivity for each keyword (0.0-1.0)
            callback: Function to call when wake word detected
        """
        self.access_key = access_key
        self.callback = callback
        self.is_listening = False
        self._stop_event = threading.Event()
        
        # Default to built-in keywords if none specified
        if keywords is None and keyword_paths is None:
            keywords = ['jarvis', 'computer']  # Default built-in keywords
            logger.info("No keywords specified, using defaults: jarvis, computer")
        
        # Initialize Porcupine
        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=keywords,
                keyword_paths=keyword_paths,
                sensitivities=sensitivities or [0.5] * (len(keywords or []) + len(keyword_paths or []))
            )
            
            logger.info(f"Porcupine initialized with {self.porcupine.num_keywords} keywords")
            logger.info(f"Sample rate: {self.porcupine.sample_rate}Hz")
            logger.info(f"Frame length: {self.porcupine.frame_length} samples")
            
        except pvporcupine.PorcupineError as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            raise
        
        # Audio stream parameters
        self.pa = None
        self.audio_stream = None
        
    def start(self):
        """Start listening for wake words"""
        if self.is_listening:
            logger.warning("Already listening for wake words")
            return
        
        self._stop_event.clear()
        self.is_listening = True
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.start()
        
        logger.info("Wake word detection started")
    
    def stop(self):
        """Stop listening for wake words"""
        if not self.is_listening:
            return
        
        self._stop_event.set()
        self.is_listening = False
        
        # Wait for thread to finish
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=2.0)
        
        # Close audio stream
        if self.audio_stream:
            self.audio_stream.close()
        
        if self.pa:
            self.pa.terminate()
        
        logger.info("Wake word detection stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        try:
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                stream_callback=self._audio_callback
            )
            
            self.audio_stream.start_stream()
            
            # Keep thread alive
            while not self._stop_event.is_set():
                self._stop_event.wait(0.1)
                
        except Exception as e:
            logger.error(f"Error in wake word listening loop: {e}")
            self.is_listening = False
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process audio frames for wake word detection"""
        if status:
            logger.warning(f"Audio stream status: {status}")
        
        try:
            # Convert bytes to int16
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, in_data)
            
            # Process frame
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                logger.info(f"Wake word detected! Index: {keyword_index}")
                
                if self.callback:
                    # Call callback in separate thread to avoid blocking audio
                    threading.Thread(target=self.callback, args=(keyword_index,)).start()
        
        except Exception as e:
            logger.error(f"Error processing audio frame: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def __del__(self):
        """Cleanup resources"""
        self.stop()
        
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()


class HeyTutorDetector(WakeWordDetector):
    """Specialized detector for 'Hey Tutor' wake word"""
    
    def __init__(self, access_key: str, callback: Optional[Callable] = None):
        """
        Initialize Hey Tutor detector
        
        Note: For production, you would need to:
        1. Train a custom wake word model for "Hey Tutor" at console.picovoice.ai
        2. Download the .ppn file
        3. Pass the path to keyword_paths
        
        For now, we'll use similar built-in keywords for testing
        """
        # Check if custom model exists
        custom_model_path = Path("data/wake_words/hey_tutor.ppn")
        
        if custom_model_path.exists():
            logger.info("Using custom 'Hey Tutor' model")
            super().__init__(
                access_key=access_key,
                keyword_paths=[str(custom_model_path)],
                sensitivities=[0.6],
                callback=callback
            )
        else:
            logger.warning("Custom 'Hey Tutor' model not found, using 'computer' as substitute")
            logger.info("To use 'Hey Tutor', train a model at https://console.picovoice.ai")
            
            # Use 'computer' as a substitute for testing
            super().__init__(
                access_key=access_key,
                keywords=['computer'],
                sensitivities=[0.6],
                callback=lambda idx: callback(idx) if callback else None
            )


def create_wake_word_detector(access_key: str) -> HeyTutorDetector:
    """Factory function to create wake word detector"""
    
    def on_wake_word_detected(keyword_index: int):
        """Default callback for wake word detection"""
        logger.info(f"Wake word detected! Starting listening...")
        # Here you would trigger the main speech recognition pipeline
        # For example:
        # - Start recording audio
        # - Process with Whisper
        # - Send to LLM
        # - Respond with TTS
    
    detector = HeyTutorDetector(
        access_key=access_key,
        callback=on_wake_word_detected
    )
    
    return detector


# Example usage for continuous wake word listening
class ContinuousWakeWordListener:
    """Manages continuous wake word detection with audio pipeline integration"""
    
    def __init__(self, access_key: str):
        self.access_key = access_key
        self.detector = None
        self.audio_processor = None
        self.is_processing = False
        
    def start(self):
        """Start continuous listening"""
        # Create wake word detector
        self.detector = create_wake_word_detector(self.access_key)
        self.detector.callback = self._on_wake_word
        
        # Start listening
        self.detector.start()
        logger.info("Continuous wake word listening started")
    
    def stop(self):
        """Stop listening"""
        if self.detector:
            self.detector.stop()
        logger.info("Continuous wake word listening stopped")
    
    def _on_wake_word(self, keyword_index: int):
        """Handle wake word detection"""
        if self.is_processing:
            logger.info("Already processing, ignoring wake word")
            return
        
        self.is_processing = True
        logger.info("Wake word detected! Ready to listen to command...")
        
        # TODO: Integrate with audio pipeline
        # 1. Play acknowledgment sound
        # 2. Start recording with timeout
        # 3. Process with speech recognition
        # 4. Handle command
        # 5. Respond with TTS
        
        # For now, just reset flag after delay
        import time
        time.sleep(2)
        self.is_processing = False