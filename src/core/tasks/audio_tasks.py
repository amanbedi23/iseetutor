"""
Audio processing background tasks
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional
import numpy as np
import whisper
from pathlib import Path

from .celery_app import celery_app
from ..audio.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

# Load Whisper model once
WHISPER_MODEL = None

def get_whisper_model():
    """Get or load Whisper model"""
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        model_name = os.getenv('WHISPER_MODEL', 'base')
        logger.info(f"Loading Whisper model: {model_name}")
        WHISPER_MODEL = whisper.load_model(model_name)
    return WHISPER_MODEL

@celery_app.task(name='src.core.tasks.audio_tasks.process_audio_chunk')
def process_audio_chunk(audio_data: bytes, sample_rate: int = 16000) -> Dict[str, Any]:
    """
    Process audio chunk with noise reduction and VAD
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Audio sample rate
        
    Returns:
        Processed audio data and metadata
    """
    try:
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Create processor
        processor = AudioProcessor(
            sample_rate=sample_rate,
            channels=1,
            vad_aggressiveness=2,
            noise_reduction_strength=0.7
        )
        
        # Process audio
        is_speech, processed_audio = processor.process_frame(audio_data)
        
        # Calculate audio statistics
        rms = np.sqrt(np.mean(processed_audio ** 2))
        max_amplitude = np.max(np.abs(processed_audio))
        
        return {
            'is_speech': is_speech,
            'audio_data': processed_audio.tobytes(),
            'rms': float(rms),
            'max_amplitude': float(max_amplitude),
            'duration': len(audio_array) / sample_rate
        }
        
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        raise

@celery_app.task(name='src.core.tasks.audio_tasks.transcribe_audio')
def transcribe_audio(
    audio_data: bytes,
    sample_rate: int = 16000,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe audio using Whisper
    
    Args:
        audio_data: Audio data as bytes
        sample_rate: Sample rate of audio
        language: Optional language code
        
    Returns:
        Transcription result with text and metadata
    """
    try:
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Save to temporary file (Whisper needs file path)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            import wave
            
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            # Load model
            model = get_whisper_model()
            
            # Transcribe
            result = model.transcribe(
                tmp_file.name,
                language=language,
                task='transcribe'
            )
            
            # Clean up
            os.unlink(tmp_file.name)
        
        return {
            'text': result['text'],
            'language': result.get('language', language),
            'segments': result.get('segments', []),
            'duration': len(audio_array) / sample_rate
        }
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise

@celery_app.task(name='src.core.tasks.audio_tasks.process_voice_command')
def process_voice_command(
    audio_data: bytes,
    user_id: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Process complete voice command pipeline
    
    Args:
        audio_data: Raw audio data
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Command processing result
    """
    try:
        # Step 1: Process audio (noise reduction, VAD)
        processed = process_audio_chunk.s(audio_data).apply_async()
        processed_result = processed.get()
        
        if not processed_result['is_speech']:
            return {
                'success': False,
                'reason': 'No speech detected',
                'user_id': user_id,
                'session_id': session_id
            }
        
        # Step 2: Transcribe
        transcription = transcribe_audio.s(
            processed_result['audio_data']
        ).apply_async()
        transcription_result = transcription.get()
        
        # Step 3: Process command (would integrate with LLM)
        command_text = transcription_result['text'].strip()
        
        logger.info(f"Voice command from user {user_id}: {command_text}")
        
        return {
            'success': True,
            'command': command_text,
            'transcription': transcription_result,
            'user_id': user_id,
            'session_id': session_id
        }
        
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        return {
            'success': False,
            'error': str(e),
            'user_id': user_id,
            'session_id': session_id
        }

@celery_app.task(name='src.core.tasks.audio_tasks.generate_tts_audio')
def generate_tts_audio(
    text: str,
    voice: str = 'en_US-ryan-high',
    speed: float = 1.0
) -> Dict[str, Any]:
    """
    Generate text-to-speech audio
    
    Args:
        text: Text to convert to speech
        voice: Voice model to use
        speed: Speech speed multiplier
        
    Returns:
        Generated audio data
    """
    # TODO: Implement when Piper TTS is integrated
    logger.info(f"TTS request: {text[:50]}... with voice {voice}")
    
    return {
        'success': False,
        'reason': 'TTS not yet implemented',
        'text': text,
        'voice': voice
    }