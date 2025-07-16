"""
Speech to Text module using OpenAI Whisper
"""

import logging
import numpy as np
import whisper
import torch
from typing import Optional, Dict, Any
import tempfile
import soundfile as sf
import os

logger = logging.getLogger(__name__)


class SpeechToText:
    """Speech to text using Whisper model"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper model
        
        Args:
            model_name: Model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading Whisper model '{model_name}' on {self.device}")
        try:
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            # Fallback to tiny model if specified model fails
            logger.info("Falling back to 'tiny' model")
            self.model = whisper.load_model("tiny", device=self.device)
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio (default 16000)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize if needed
            if np.abs(audio_data).max() > 1.0:
                audio_data = audio_data / 32768.0
            
            # Save to temporary file (Whisper requires file input)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, sample_rate)
                tmp_path = tmp_file.name
            
            try:
                # Transcribe
                result = self.model.transcribe(
                    tmp_path,
                    language="en",
                    task="transcribe"
                )
                
                text = result["text"].strip()
                logger.info(f"Transcribed: {text}")
                return text
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def transcribe_with_timestamps(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio with word timestamps
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            Dict with text and segments with timestamps
        """
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize if needed
            if np.abs(audio_data).max() > 1.0:
                audio_data = audio_data / 32768.0
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, sample_rate)
                tmp_path = tmp_file.name
            
            try:
                # Transcribe with timestamps
                result = self.model.transcribe(
                    tmp_path,
                    language="en",
                    task="transcribe",
                    word_timestamps=True
                )
                
                return {
                    "text": result["text"].strip(),
                    "segments": result["segments"],
                    "language": result["language"]
                }
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Transcription with timestamps error: {e}")
            return None


# Simple test function
if __name__ == "__main__":
    import time
    
    # Test initialization
    print("Initializing Speech to Text...")
    stt = SpeechToText(model_name="base")
    
    # Generate test audio (sine wave)
    sample_rate = 16000
    duration = 2  # seconds
    frequency = 440  # Hz
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    print("\nTesting transcription with generated audio...")
    start_time = time.time()
    result = stt.transcribe(test_audio, sample_rate)
    elapsed = time.time() - start_time
    
    print(f"Transcription took: {elapsed:.2f} seconds")
    print(f"Result: {result}")