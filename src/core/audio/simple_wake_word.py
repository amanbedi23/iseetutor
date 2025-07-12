"""
Simple wake word detection using existing audio pipeline
Fallback solution for unsupported hardware
"""

import numpy as np
import logging
from typing import Callable, Optional, List
import threading
import queue
from collections import deque
import speech_recognition as sr

logger = logging.getLogger(__name__)

class SimpleWakeWordDetector:
    """Simple wake word detector using speech recognition"""
    
    def __init__(
        self,
        wake_words: List[str] = None,
        callback: Optional[Callable] = None,
        energy_threshold: int = 4000,
        pause_threshold: float = 0.8
    ):
        """
        Initialize simple wake word detector
        
        Args:
            wake_words: List of wake words to detect
            callback: Function to call when wake word detected
            energy_threshold: Minimum audio energy to consider for speech
            pause_threshold: Seconds of silence to consider speech complete
        """
        self.wake_words = wake_words or ["hey tutor", "computer", "jarvis"]
        self.callback = callback
        self.is_listening = False
        self._stop_event = threading.Event()
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        
        # Audio source
        self.microphone = None
        
        logger.info(f"Simple wake word detector initialized with words: {self.wake_words}")
    
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
        
        logger.info("Simple wake word detection started")
    
    def stop(self):
        """Stop listening for wake words"""
        if not self.is_listening:
            return
        
        self._stop_event.set()
        self.is_listening = False
        
        # Wait for thread to finish
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join(timeout=2.0)
        
        logger.info("Simple wake word detection stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        try:
            with sr.Microphone() as source:
                self.microphone = source
                
                # Adjust for ambient noise
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Listening for wake words...")
                
                while not self._stop_event.is_set():
                    try:
                        # Listen for audio with timeout
                        audio = self.recognizer.listen(
                            source,
                            timeout=0.5,
                            phrase_time_limit=2
                        )
                        
                        # Process in separate thread to avoid blocking
                        threading.Thread(
                            target=self._process_audio,
                            args=(audio,)
                        ).start()
                        
                    except sr.WaitTimeoutError:
                        # Timeout is expected, continue listening
                        pass
                    except Exception as e:
                        logger.error(f"Error in listening loop: {e}")
                        
        except Exception as e:
            logger.error(f"Error initializing microphone: {e}")
            self.is_listening = False
    
    def _process_audio(self, audio):
        """Process audio for wake word detection"""
        try:
            # Try to recognize speech
            text = self.recognizer.recognize_google(audio).lower()
            logger.debug(f"Heard: '{text}'")
            
            # Check for wake words
            for wake_word in self.wake_words:
                if wake_word in text:
                    logger.info(f"Wake word detected: '{wake_word}' in '{text}'")
                    
                    if self.callback:
                        self.callback(wake_word)
                    
                    break
                    
        except sr.UnknownValueError:
            # Speech not understood, ignore
            pass
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")


class VADWakeWordDetector:
    """Wake word detector using VAD from audio pipeline"""
    
    def __init__(
        self,
        wake_words: List[str] = None,
        callback: Optional[Callable] = None
    ):
        """
        Initialize VAD-based wake word detector
        
        This uses the existing AudioProcessor with VAD for efficiency
        """
        from .audio_processor import AudioProcessor
        
        self.wake_words = wake_words or ["hey tutor", "computer"]
        self.callback = callback
        self.is_listening = False
        
        # Create audio processor
        self.audio_processor = AudioProcessor(
            sample_rate=16000,
            channels=1,
            vad_aggressiveness=2
        )
        
        # Buffer for accumulating speech
        self.speech_buffer = deque(maxlen=int(16000 * 3))  # 3 seconds
        self.processing = False
        
        logger.info(f"VAD wake word detector initialized")
    
    def start(self):
        """Start listening"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        def audio_callback(audio_chunk, is_speech):
            if is_speech and not self.processing:
                self.speech_buffer.extend(audio_chunk)
                
                # Check if we have enough audio
                if len(self.speech_buffer) > 16000:  # 1 second
                    self._process_buffer()
        
        self.audio_processor.process_audio_stream(callback=audio_callback)
        logger.info("VAD wake word detection started")
    
    def stop(self):
        """Stop listening"""
        if not self.is_listening:
            return
        
        self.audio_processor.stop_processing()
        self.is_listening = False
        logger.info("VAD wake word detection stopped")
    
    def _process_buffer(self):
        """Process accumulated audio buffer"""
        if self.processing:
            return
        
        self.processing = True
        
        try:
            # Convert buffer to audio data
            audio_data = np.array(self.speech_buffer)
            
            # Here you would use Whisper or another STT engine
            # For now, just simulate detection
            logger.info("Processing audio buffer for wake word...")
            
            # Clear buffer
            self.speech_buffer.clear()
            
        finally:
            self.processing = False


def create_fallback_detector() -> SimpleWakeWordDetector:
    """Create a fallback wake word detector"""
    
    def on_wake_word(wake_word: str):
        logger.info(f"Wake word '{wake_word}' detected!")
        # Trigger main pipeline here
    
    # Try speech_recognition first
    try:
        import speech_recognition as sr
        logger.info("Using speech_recognition for wake word detection")
        return SimpleWakeWordDetector(callback=on_wake_word)
    except ImportError:
        logger.info("speech_recognition not available, using VAD-based detector")
        return VADWakeWordDetector(callback=on_wake_word)