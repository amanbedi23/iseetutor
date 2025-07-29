"""
Google Cloud Speech-to-Text Provider Implementation

Provides Google Cloud Speech API integration for speech recognition.
"""

import os
import asyncio
from typing import AsyncGenerator, Optional
import logging
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
from google.oauth2 import service_account
import numpy as np

from ..interfaces import STTInterface, AudioConfig

logger = logging.getLogger(__name__)


class GoogleSTT(STTInterface):
    """Google Cloud Speech-to-Text implementation"""
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        language_code: str = "en-US",
        model: str = "latest_long",
        enable_automatic_punctuation: bool = True,
        enable_word_confidence: bool = False
    ):
        """
        Initialize Google Cloud STT provider
        
        Args:
            credentials_path: Path to service account JSON (defaults to env var)
            language_code: Language code for recognition
            model: Recognition model to use
            enable_automatic_punctuation: Add punctuation to results
            enable_word_confidence: Include word-level confidence scores
        """
        # Set up credentials
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        else:
            # Use default credentials (from env var GOOGLE_APPLICATION_CREDENTIALS)
            credentials = None
        
        self.client = speech_v1.SpeechAsyncClient(credentials=credentials)
        self.language_code = language_code
        self.model = model
        self.enable_automatic_punctuation = enable_automatic_punctuation
        self.enable_word_confidence = enable_word_confidence
        
        # Configure recognition settings
        self.config = types.RecognitionConfig(
            encoding=types.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=self.language_code,
            model=self.model,
            enable_automatic_punctuation=self.enable_automatic_punctuation,
            enable_word_confidence=self.enable_word_confidence,
            use_enhanced=True,  # Use enhanced models when available
            enable_word_time_offsets=False,
            max_alternatives=1
        )
    
    async def transcribe(
        self,
        audio_data: bytes,
        config: AudioConfig
    ) -> str:
        """
        Transcribe audio to text using Google Cloud Speech
        
        Args:
            audio_data: Audio data as bytes (WAV format expected)
            config: Audio configuration
            
        Returns:
            Transcribed text
        """
        try:
            # Update config if needed
            recognition_config = types.RecognitionConfig(
                encoding=types.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=config.sample_rate,
                language_code=config.language or self.language_code,
                model=self.model,
                enable_automatic_punctuation=self.enable_automatic_punctuation,
                use_enhanced=True
            )
            
            audio = types.RecognitionAudio(content=audio_data)
            
            # Perform the transcription
            response = await self.client.recognize(
                config=recognition_config,
                audio=audio
            )
            
            # Extract transcript
            transcript = ""
            for result in response.results:
                # Use the alternative with the highest confidence
                transcript += result.alternatives[0].transcript
            
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Google STT transcription error: {str(e)}")
            raise
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        config: AudioConfig
    ) -> AsyncGenerator[str, None]:
        """
        Transcribe audio stream in real-time
        
        Args:
            audio_stream: Async generator yielding audio chunks
            config: Audio configuration
            
        Yields:
            Transcribed text chunks
        """
        try:
            # Create streaming config
            streaming_config = types.StreamingRecognitionConfig(
                config=types.RecognitionConfig(
                    encoding=types.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=config.sample_rate,
                    language_code=config.language or self.language_code,
                    model=self.model,
                    enable_automatic_punctuation=self.enable_automatic_punctuation,
                    use_enhanced=True
                ),
                interim_results=True,
                single_utterance=False
            )
            
            # Generator to yield requests
            async def request_generator():
                # First request contains config
                yield types.StreamingRecognizeRequest(
                    streaming_config=streaming_config
                )
                
                # Subsequent requests contain audio
                async for chunk in audio_stream:
                    yield types.StreamingRecognizeRequest(
                        audio_content=chunk
                    )
            
            # Start streaming recognition
            responses = await self.client.streaming_recognize(
                requests=request_generator()
            )
            
            # Process responses
            async for response in responses:
                for result in response.results:
                    if result.is_final:
                        yield result.alternatives[0].transcript
                    elif result.stability > 0.8:
                        # Yield stable interim results
                        yield f"[interim] {result.alternatives[0].transcript}"
                        
        except Exception as e:
            logger.error(f"Google STT streaming error: {str(e)}")
            raise
    
    def preprocess_audio(self, audio_data: np.ndarray, sample_rate: int) -> bytes:
        """
        Preprocess audio for Google Cloud Speech
        
        Args:
            audio_data: Audio as numpy array
            sample_rate: Sample rate
            
        Returns:
            Processed audio as bytes
        """
        # Ensure audio is in the correct format
        if audio_data.dtype != np.int16:
            # Convert to 16-bit PCM
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)
        
        # Convert to bytes
        return audio_data.tobytes()
    
    async def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        # Google Cloud Speech supports many languages
        # This is a subset of commonly used ones
        return [
            {"code": "en-US", "name": "English (US)"},
            {"code": "en-GB", "name": "English (UK)"},
            {"code": "es-ES", "name": "Spanish (Spain)"},
            {"code": "es-MX", "name": "Spanish (Mexico)"},
            {"code": "fr-FR", "name": "French"},
            {"code": "de-DE", "name": "German"},
            {"code": "it-IT", "name": "Italian"},
            {"code": "pt-BR", "name": "Portuguese (Brazil)"},
            {"code": "zh-CN", "name": "Chinese (Simplified)"},
            {"code": "ja-JP", "name": "Japanese"},
            {"code": "ko-KR", "name": "Korean"}
        ]