"""
Wake word detection using OpenWakeWord
Open-source alternative that works on ARM/Jetson devices
"""

import os
import numpy as np
import logging
import threading
import queue
from typing import Optional, Callable, List, Dict
from pathlib import Path
import openwakeword
from openwakeword.model import Model
import pyaudio
import time

logger = logging.getLogger(__name__)

class OpenWakeWordDetector:
    """Detects wake words using OpenWakeWord"""
    
    def __init__(
        self,
        model_paths: Optional[List[str]] = None,
        inference_framework: str = "tflite",
        wakeword_callback: Optional[Callable] = None,
        threshold: float = 0.5,
        vad_threshold: float = 0.5,
        enable_vad: bool = True
    ):
        """
        Initialize OpenWakeWord detector
        
        Args:
            model_paths: List of paths to custom model files (optional)
            inference_framework: "tflite" or "onnx" 
            wakeword_callback: Function to call when wake word detected
            threshold: Detection threshold (0.0-1.0)
            vad_threshold: Voice activity detection threshold
            enable_vad: Enable voice activity detection preprocessing
        """
        self.wakeword_callback = wakeword_callback
        self.threshold = threshold
        self.vad_threshold = vad_threshold
        self.enable_vad = enable_vad
        self.is_listening = False
        self._stop_event = threading.Event()
        
        # Download pre-trained models if needed
        logger.info("Initializing OpenWakeWord models...")
        
        # Get list of pre-trained models
        self.available_models = openwakeword.MODELS
        logger.info(f"Available pre-trained models: {list(self.available_models.keys())}")
        
        # Initialize models
        if model_paths:
            # Use custom models (these are actual file paths)
            for path in model_paths:
                model_name = Path(path).stem
                # For custom models, we use the file path directly
                self.model = Model(
                    wakeword_models=[path],
                    inference_framework=inference_framework
                )
                logger.info(f"Loaded custom model: {model_name}")
                break  # OpenWakeWord Model handles multiple models internally
        else:
            # Use pre-trained models (these are model names, not paths)
            wanted_models = ['hey_jarvis', 'alexa', 'hey_mycroft']
            
            # Filter available models
            selected_models = [m for m in wanted_models if m in self.available_models]
            
            if selected_models:
                logger.info(f"Loading pre-trained models: {selected_models}")
                self.model = Model(
                    wakeword_models=selected_models,
                    inference_framework=inference_framework
                )
            else:
                raise ValueError("No suitable pre-trained models found")
        
        # Audio parameters
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1280  # 80ms at 16kHz
        self.format = pyaudio.paInt16
        
        # Audio stream
        self.pa = None
        self.audio_stream = None
        
        logger.info(f"OpenWakeWord initialized successfully")
    
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
        
        logger.info("OpenWakeWord detection started")
    
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
        
        logger.info("OpenWakeWord detection stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        try:
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            
            self.audio_stream = self.pa.open(
                rate=self.sample_rate,
                channels=self.channels,
                format=self.format,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Audio stream opened, listening for wake words...")
            
            while not self._stop_event.is_set():
                # Read audio chunk
                audio_data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convert to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Get prediction from model
                prediction = self.model.predict(audio_array)
                
                # Check all outputs (model may have multiple wake words)
                for wakeword, score in prediction.items():
                    if score > self.threshold:
                        logger.info(f"Wake word detected: {wakeword} (score: {score:.3f})")
                        
                        if self.wakeword_callback:
                            # Call callback in separate thread
                            threading.Thread(
                                target=self.wakeword_callback,
                                args=(wakeword, score)
                            ).start()
                
        except Exception as e:
            logger.error(f"Error in wake word listening loop: {e}")
            self.is_listening = False
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
    
    def __del__(self):
        """Cleanup resources"""
        self.stop()


class HeyTutorOpenWakeWord(OpenWakeWordDetector):
    """Specialized detector for 'Hey Tutor' using OpenWakeWord"""
    
    def __init__(self, wakeword_callback: Optional[Callable] = None):
        """
        Initialize Hey Tutor detector with OpenWakeWord
        
        Note: For a custom "Hey Tutor" model:
        1. Record audio samples of "Hey Tutor"
        2. Train using OpenWakeWord training scripts
        3. Save model as hey_tutor.tflite
        4. Place in data/wake_words/
        """
        # Check for custom Hey Tutor model
        custom_model_dir = Path("data/wake_words")
        custom_model_path = custom_model_dir / "hey_tutor.tflite"
        
        if custom_model_path.exists():
            logger.info("Using custom 'Hey Tutor' OpenWakeWord model")
            super().__init__(
                model_paths=[str(custom_model_path)],
                wakeword_callback=wakeword_callback,
                threshold=0.6
            )
        else:
            logger.info("Custom 'Hey Tutor' model not found, using similar pre-trained models")
            logger.info("Using 'hey_jarvis' as a substitute - say 'Hey Jarvis' to test")
            
            # Create callback wrapper to pretend it's "Hey Tutor"
            def wrapped_callback(wakeword, score):
                if wakeword == "hey_jarvis":
                    logger.info("Treating 'hey_jarvis' as 'hey_tutor' for testing")
                    if wakeword_callback:
                        wakeword_callback("hey_tutor", score)
                elif wakeword_callback:
                    wakeword_callback(wakeword, score)
            
            super().__init__(
                wakeword_callback=wrapped_callback,
                threshold=0.5
            )


def create_openwakeword_detector() -> HeyTutorOpenWakeWord:
    """Factory function to create OpenWakeWord detector"""
    
    def on_wake_word_detected(wakeword: str, score: float):
        """Default callback for wake word detection"""
        logger.info(f"Wake word '{wakeword}' detected with confidence {score:.3f}")
        logger.info("Ready to listen for commands...")
        # Here you would trigger the main speech recognition pipeline
    
    detector = HeyTutorOpenWakeWord(
        wakeword_callback=on_wake_word_detected
    )
    
    return detector


# Continuous listener with OpenWakeWord
class ContinuousOpenWakeWordListener:
    """Manages continuous wake word detection with OpenWakeWord"""
    
    def __init__(self):
        self.detector = None
        self.is_processing = False
        self.command_timeout = 5.0  # seconds to wait for command
        
    def start(self):
        """Start continuous listening"""
        # Create detector
        self.detector = create_openwakeword_detector()
        self.detector.wakeword_callback = self._on_wake_word
        
        # Start listening
        self.detector.start()
        logger.info("Continuous OpenWakeWord listening started")
        logger.info("Say 'Hey Jarvis' to activate (or train custom 'Hey Tutor' model)")
    
    def stop(self):
        """Stop listening"""
        if self.detector:
            self.detector.stop()
        logger.info("Continuous OpenWakeWord listening stopped")
    
    def _on_wake_word(self, wakeword: str, score: float):
        """Handle wake word detection"""
        if self.is_processing:
            logger.info("Already processing, ignoring wake word")
            return
        
        self.is_processing = True
        logger.info(f"Wake word '{wakeword}' detected (confidence: {score:.3f})")
        
        # TODO: Integrate with full pipeline
        # 1. Play acknowledgment sound
        # 2. Start recording command
        # 3. Process with Whisper
        # 4. Send to LLM
        # 5. Respond with TTS
        
        # For now, simulate processing
        time.sleep(2)
        logger.info("Ready for next wake word")
        self.is_processing = False