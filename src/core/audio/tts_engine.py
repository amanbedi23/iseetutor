"""
Text-to-Speech (TTS) engine using Piper for ISEE Tutor.
Provides fast, local TTS with child-friendly voices.
"""

import os
import sys
import io
import wave
import json
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, Union, List, Dict
import logging
import requests
import tarfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PiperTTSEngine:
    """Piper TTS engine for local text-to-speech synthesis."""
    
    def __init__(self, model_path: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize Piper TTS engine.
        
        Args:
            model_path: Path to Piper voice model (onnx file)
            cache_dir: Directory for caching audio files
        """
        self.model_path = model_path or os.getenv("PIPER_MODEL_PATH", 
                                                  "/mnt/storage/models/tts/en_US-amy-medium.onnx")
        self.cache_dir = Path(cache_dir or os.getenv("TTS_CACHE_DIR", "/mnt/storage/cache/tts"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice configuration
        self.voice_config = {
            "speaker_id": 0,
            "length_scale": 1.0,  # Speed control (0.5 = faster, 2.0 = slower)
            "noise_scale": 0.667,
            "noise_w_scale": 0.8,
        }
        
        # Thread pool for async synthesis
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Download model if not exists
        self._ensure_model()
        
        logger.info(f"Piper TTS initialized with model: {self.model_path}")
    
    def _ensure_model(self):
        """Download Piper model if not already present."""
        model_path = Path(self.model_path)
        config_path = model_path.with_suffix(".onnx.json")
        
        if model_path.exists() and config_path.exists():
            logger.info("Piper model already downloaded")
            return
        
        logger.info("Checking for Piper voice model...")
        
        # Check if the model was already downloaded by the download script
        if model_path.exists() and config_path.exists():
            logger.info(f"Using existing Piper model at {model_path}")
            return
        
        # If not, run the download script
        logger.info("Model not found. Running download script...")
        try:
            script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "download_piper_voice.py"
            if script_path.exists():
                import subprocess
                result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Download script failed: {result.stderr}")
                    raise RuntimeError("Failed to download Piper model")
                logger.info("Model downloaded successfully")
            else:
                logger.error(f"Download script not found at {script_path}")
                raise FileNotFoundError("Download script not found")
        except Exception as e:
            logger.error(f"Failed to download Piper model: {e}")
            raise
    
    def synthesize(self, text: str, voice_params: Optional[Dict] = None) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_params: Optional voice parameters (speed, pitch, etc.)
            
        Returns:
            WAV audio data as bytes
        """
        if not text:
            return b""
        
        # Clean text for synthesis
        text = self._clean_text(text)
        
        # Check cache first
        cache_key = self._get_cache_key(text, voice_params)
        cached_audio = self._get_from_cache(cache_key)
        if cached_audio:
            logger.debug(f"Using cached audio for: {text[:50]}...")
            return cached_audio
        
        # Merge voice parameters
        params = self.voice_config.copy()
        if voice_params:
            params.update(voice_params)
        
        try:
            # Use Piper Python API
            from piper import PiperVoice
            from piper.config import SynthesisConfig
            
            # Load voice if not already loaded
            if not hasattr(self, '_voice'):
                logger.info(f"Loading Piper voice from {self.model_path}")
                self._voice = PiperVoice.load(str(self.model_path))
            
            # Create synthesis config
            syn_config = SynthesisConfig(
                speaker_id=params.get("speaker_id", None),
                length_scale=params.get("length_scale", None),
                noise_scale=params.get("noise_scale", None),
                noise_w_scale=params.get("noise_w_scale", None)
            )
            
            # Synthesize audio
            audio_chunks = []
            sample_rate = 22050  # Default
            
            for audio_chunk in self._voice.synthesize(text, syn_config):
                # AudioChunk has audio_float_array attribute with numpy array
                audio_chunks.append(audio_chunk.audio_float_array)
                sample_rate = audio_chunk.sample_rate
            
            # Combine chunks
            if audio_chunks:
                # Concatenate numpy arrays
                combined_audio = np.concatenate(audio_chunks)
                
                # Convert float32 to int16
                audio_int16 = (combined_audio * 32767).astype(np.int16)
                
                # Convert to WAV
                wav_audio = self._raw_to_wav(audio_int16.tobytes(), sample_rate)
                
                # Cache the result
                self._save_to_cache(cache_key, wav_audio)
                
                return wav_audio
            else:
                return b""
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            # Fallback to subprocess method if Python API fails
            try:
                return self._synthesize_subprocess(text, params)
            except Exception as e2:
                logger.error(f"Subprocess fallback also failed: {e2}")
                raise
    
    def _synthesize_subprocess(self, text: str, params: Dict) -> bytes:
        """Fallback synthesis using subprocess."""
        try:
            # Run Piper synthesis via CLI
            cmd = [
                "piper",
                "--model", str(self.model_path),
                "--output-raw"
            ]
            
            # Run synthesis
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            raw_audio, error = process.communicate(input=text.encode())
            
            if process.returncode != 0:
                logger.error(f"Piper synthesis failed: {error.decode()}")
                raise RuntimeError(f"TTS synthesis failed: {error.decode()}")
            
            # Convert raw audio to WAV
            return self._raw_to_wav(raw_audio)
            
        except Exception as e:
            logger.error(f"Subprocess TTS synthesis error: {e}")
            raise
    
    async def synthesize_async(self, text: str, voice_params: Optional[Dict] = None) -> bytes:
        """Async version of synthesize."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.synthesize, text, voice_params)
    
    def synthesize_batch(self, texts: List[str], voice_params: Optional[Dict] = None) -> List[bytes]:
        """
        Synthesize multiple texts in batch.
        
        Args:
            texts: List of texts to synthesize
            voice_params: Optional voice parameters
            
        Returns:
            List of WAV audio data
        """
        results = []
        for text in texts:
            try:
                audio = self.synthesize(text, voice_params)
                results.append(audio)
            except Exception as e:
                logger.error(f"Failed to synthesize: {text[:50]}... - {e}")
                results.append(b"")
        
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean text for TTS synthesis."""
        # Remove special characters that might cause issues
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Handle common abbreviations
        replacements = {
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Dr.": "Doctor",
            "St.": "Street",
            "vs.": "versus",
            "etc.": "et cetera",
        }
        
        for abbr, full in replacements.items():
            text = text.replace(abbr, full)
        
        return text.strip()
    
    def _raw_to_wav(self, raw_audio: bytes, sample_rate: int = 22050) -> bytes:
        """Convert raw PCM audio to WAV format."""
        # Convert bytes to numpy array (assuming int16)
        audio_array = np.frombuffer(raw_audio, dtype=np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)   # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def _get_cache_key(self, text: str, voice_params: Optional[Dict]) -> str:
        """Generate cache key for audio."""
        import hashlib
        
        key_parts = [text]
        if voice_params:
            key_parts.append(json.dumps(voice_params, sort_keys=True))
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Get audio from cache."""
        cache_file = self.cache_dir / f"{cache_key}.wav"
        if cache_file.exists():
            try:
                return cache_file.read_bytes()
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, audio_data: bytes):
        """Save audio to cache."""
        cache_file = self.cache_dir / f"{cache_key}.wav"
        try:
            cache_file.write_bytes(audio_data)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def clear_cache(self):
        """Clear the TTS cache."""
        try:
            for cache_file in self.cache_dir.glob("*.wav"):
                cache_file.unlink()
            logger.info("TTS cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def set_voice_speed(self, speed: float):
        """
        Set voice speed.
        
        Args:
            speed: Speed multiplier (0.5 = half speed, 2.0 = double speed)
        """
        self.voice_config["length_scale"] = 1.0 / speed
    
    def set_voice_params(self, **kwargs):
        """Set voice parameters."""
        self.voice_config.update(kwargs)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Global TTS instance
_tts_engine: Optional[PiperTTSEngine] = None

def get_tts_engine() -> PiperTTSEngine:
    """Get or create global TTS engine instance."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = PiperTTSEngine()
    return _tts_engine

def synthesize_speech(text: str, speed: float = 1.0) -> bytes:
    """
    Convenience function to synthesize speech.
    
    Args:
        text: Text to synthesize
        speed: Speech speed (0.5-2.0)
        
    Returns:
        WAV audio data
    """
    engine = get_tts_engine()
    engine.set_voice_speed(speed)
    return engine.synthesize(text)

async def synthesize_speech_async(text: str, speed: float = 1.0) -> bytes:
    """Async version of synthesize_speech."""
    engine = get_tts_engine()
    engine.set_voice_speed(speed)
    return await engine.synthesize_async(text)