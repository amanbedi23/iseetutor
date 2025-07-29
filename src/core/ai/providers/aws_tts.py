"""
Amazon Polly Text-to-Speech Provider Implementation

Provides Amazon Polly integration for text-to-speech synthesis.
"""

import os
import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any
import logging
import boto3
from botocore.exceptions import BotoCore3Error
import io
import wave

from ..interfaces import TTSInterface, AudioConfig

logger = logging.getLogger(__name__)


class AmazonPollyTTS(TTSInterface):
    """Amazon Polly Text-to-Speech implementation"""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        voice_id: str = "Joanna",
        engine: str = "neural"
    ):
        """
        Initialize Amazon Polly TTS provider
        
        Args:
            aws_access_key_id: AWS access key (defaults to env var)
            aws_secret_access_key: AWS secret key (defaults to env var)
            region_name: AWS region
            voice_id: Default voice to use
            engine: TTS engine (standard or neural)
        """
        # Initialize AWS client
        self.client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=region_name
        )
        
        self.voice_id = voice_id
        self.engine = engine
        
        # Child-friendly voices mapping
        self.child_voices = {
            "en-US": {
                "female": ["Ivy", "Joanna", "Kendra", "Kimberly"],
                "male": ["Justin", "Kevin", "Matthew"],
                "child": ["Ivy", "Justin"]  # These sound younger
            },
            "en-GB": {
                "female": ["Amy", "Emma"],
                "male": ["Arthur", "Brian"],
                "child": ["Amy"]
            }
        }
    
    async def synthesize(
        self,
        text: str,
        config: AudioConfig
    ) -> bytes:
        """
        Synthesize text to audio using Amazon Polly
        
        Args:
            text: Text to synthesize
            config: Audio configuration
            
        Returns:
            Audio data as bytes (WAV format)
        """
        try:
            # Select voice based on config
            voice_id = config.voice or self.voice_id
            
            # Adjust speech rate
            speed_percentage = int(config.speed * 100)
            ssml_text = f'<speak><prosody rate="{speed_percentage}%">{text}</prosody></speak>'
            
            # Run synthesis in thread pool (boto3 is sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.synthesize_speech(
                    Engine=self.engine,
                    OutputFormat='pcm',
                    SampleRate=str(config.sample_rate),
                    Text=ssml_text,
                    TextType='ssml',
                    VoiceId=voice_id
                )
            )
            
            # Convert PCM to WAV
            pcm_data = response['AudioStream'].read()
            wav_data = self._pcm_to_wav(
                pcm_data,
                config.sample_rate,
                config.channels
            )
            
            return wav_data
            
        except Exception as e:
            logger.error(f"Amazon Polly synthesis error: {str(e)}")
            raise
    
    async def synthesize_stream(
        self,
        text: str,
        config: AudioConfig
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize text to audio with streaming
        
        Args:
            text: Text to synthesize
            config: Audio configuration
            
        Yields:
            Audio data chunks
        """
        try:
            # For streaming, we'll chunk the synthesized audio
            audio_data = await self.synthesize(text, config)
            
            # Yield in chunks
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i:i + chunk_size]
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
                
        except Exception as e:
            logger.error(f"Amazon Polly streaming error: {str(e)}")
            raise
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices from Amazon Polly
        
        Returns:
            List of voice information
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.describe_voices()
            )
            
            voices = []
            for voice in response['Voices']:
                # Filter for child-friendly voices
                is_child_friendly = (
                    voice['Id'] in self.child_voices.get(
                        voice['LanguageCode'], {}
                    ).get('child', []) or
                    voice['Id'] in self.child_voices.get(
                        voice['LanguageCode'], {}
                    ).get('female', []) or
                    voice['Id'] in self.child_voices.get(
                        voice['LanguageCode'], {}
                    ).get('male', [])
                )
                
                voices.append({
                    'id': voice['Id'],
                    'name': voice['Name'],
                    'language': voice['LanguageCode'],
                    'language_name': voice['LanguageName'],
                    'gender': voice['Gender'],
                    'engine': voice['SupportedEngines'],
                    'child_friendly': is_child_friendly,
                    'sample_rate': 16000
                })
            
            # Sort child-friendly voices first
            voices.sort(key=lambda x: (not x['child_friendly'], x['name']))
            
            return voices
            
        except Exception as e:
            logger.error(f"Amazon Polly get voices error: {str(e)}")
            raise
    
    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int, channels: int) -> bytes:
        """
        Convert PCM audio data to WAV format
        
        Args:
            pcm_data: Raw PCM audio data
            sample_rate: Sample rate
            channels: Number of channels
            
        Returns:
            WAV formatted audio data
        """
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def get_voice_for_age(self, age: int, gender: str = "female") -> str:
        """
        Select appropriate voice based on child's age
        
        Args:
            age: Child's age
            gender: Preferred voice gender
            
        Returns:
            Voice ID
        """
        if age <= 8:
            # Younger children - use child voices
            return "Ivy" if gender == "female" else "Justin"
        elif age <= 12:
            # Pre-teens - use younger adult voices
            return "Kimberly" if gender == "female" else "Matthew"
        else:
            # Teens - use standard voices
            return "Joanna" if gender == "female" else "Matthew"