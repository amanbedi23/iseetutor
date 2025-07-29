"""
Cloud AI Service Factory

Factory pattern implementation for creating appropriate AI service providers
based on configuration and availability.
"""

import os
from typing import Optional, Dict, Any
import logging
from enum import Enum

from .interfaces import (
    LLMInterface, STTInterface, TTSInterface, VectorDBInterface,
    LLMProvider, STTProvider, TTSProvider, VectorDBProvider
)

# Import providers
from .providers.openai_llm import OpenAILLM
from .providers.google_stt import GoogleSTT
from .providers.aws_tts import AmazonPollyTTS
from .providers.pinecone_vectordb import PineconeVectorDB

logger = logging.getLogger(__name__)


class CloudAIFactory:
    """Factory for creating cloud AI service instances"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize factory with configuration
        
        Args:
            config: Configuration dictionary for providers
        """
        self.config = config or {}
        self._llm_instance = None
        self._stt_instance = None
        self._tts_instance = None
        self._vectordb_instance = None
    
    def create_llm(
        self,
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMInterface:
        """
        Create LLM provider instance
        
        Args:
            provider: Provider name (openai, anthropic, google, local)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            LLM provider instance
        """
        provider = provider or os.getenv("LLM_PROVIDER", "openai")
        
        if provider == LLMProvider.OPENAI:
            return OpenAILLM(
                api_key=kwargs.get("api_key") or os.getenv("OPENAI_API_KEY"),
                model=kwargs.get("model", "gpt-3.5-turbo"),
                organization=kwargs.get("organization")
            )
        elif provider == LLMProvider.ANTHROPIC:
            # Import and create Anthropic provider
            # from .providers.anthropic_llm import AnthropicLLM
            # return AnthropicLLM(**kwargs)
            raise NotImplementedError("Anthropic provider not yet implemented")
        elif provider == LLMProvider.GOOGLE:
            # Import and create Google provider
            # from .providers.google_llm import GoogleLLM
            # return GoogleLLM(**kwargs)
            raise NotImplementedError("Google LLM provider not yet implemented")
        elif provider == LLMProvider.LOCAL:
            # Fall back to local Llama
            from src.core.llm.companion_llm import CompanionLLM
            return CompanionLLM()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def create_stt(
        self,
        provider: Optional[str] = None,
        **kwargs
    ) -> STTInterface:
        """
        Create STT provider instance
        
        Args:
            provider: Provider name (google, aws, azure, local)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            STT provider instance
        """
        provider = provider or os.getenv("STT_PROVIDER", "google")
        
        if provider == STTProvider.GOOGLE:
            return GoogleSTT(
                credentials_path=kwargs.get("credentials_path"),
                language_code=kwargs.get("language_code", "en-US"),
                model=kwargs.get("model", "latest_long")
            )
        elif provider == STTProvider.AWS:
            # Import and create AWS Transcribe provider
            # from .providers.aws_stt import AWSTranscribeSTT
            # return AWSTranscribeSTT(**kwargs)
            raise NotImplementedError("AWS Transcribe provider not yet implemented")
        elif provider == STTProvider.AZURE:
            # Import and create Azure provider
            # from .providers.azure_stt import AzureSTT
            # return AzureSTT(**kwargs)
            raise NotImplementedError("Azure STT provider not yet implemented")
        elif provider == STTProvider.LOCAL:
            # Fall back to local Whisper
            from src.models.speech_to_text import SpeechToText
            return SpeechToText()
        else:
            raise ValueError(f"Unknown STT provider: {provider}")
    
    def create_tts(
        self,
        provider: Optional[str] = None,
        **kwargs
    ) -> TTSInterface:
        """
        Create TTS provider instance
        
        Args:
            provider: Provider name (google, aws_polly, azure, elevenlabs, local)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            TTS provider instance
        """
        provider = provider or os.getenv("TTS_PROVIDER", "aws_polly")
        
        if provider == TTSProvider.AWS_POLLY:
            return AmazonPollyTTS(
                aws_access_key_id=kwargs.get("aws_access_key_id"),
                aws_secret_access_key=kwargs.get("aws_secret_access_key"),
                region_name=kwargs.get("region_name", "us-east-1"),
                voice_id=kwargs.get("voice_id", "Joanna"),
                engine=kwargs.get("engine", "neural")
            )
        elif provider == TTSProvider.GOOGLE:
            # Import and create Google TTS provider
            # from .providers.google_tts import GoogleTTS
            # return GoogleTTS(**kwargs)
            raise NotImplementedError("Google TTS provider not yet implemented")
        elif provider == TTSProvider.AZURE:
            # Import and create Azure TTS provider
            # from .providers.azure_tts import AzureTTS
            # return AzureTTS(**kwargs)
            raise NotImplementedError("Azure TTS provider not yet implemented")
        elif provider == TTSProvider.ELEVENLABS:
            # Import and create ElevenLabs provider
            # from .providers.elevenlabs_tts import ElevenLabsTTS
            # return ElevenLabsTTS(**kwargs)
            raise NotImplementedError("ElevenLabs provider not yet implemented")
        elif provider == TTSProvider.LOCAL:
            # Fall back to local Piper
            from src.core.audio.tts_engine import TTSEngine
            return TTSEngine()
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")
    
    def create_vectordb(
        self,
        provider: Optional[str] = None,
        **kwargs
    ) -> VectorDBInterface:
        """
        Create Vector Database provider instance
        
        Args:
            provider: Provider name (pinecone, weaviate, qdrant, local)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Vector DB provider instance
        """
        provider = provider or os.getenv("VECTORDB_PROVIDER", "pinecone")
        
        if provider == VectorDBProvider.PINECONE:
            return PineconeVectorDB(
                api_key=kwargs.get("api_key"),
                environment=kwargs.get("environment"),
                index_name=kwargs.get("index_name", "iseetutor"),
                dimension=kwargs.get("dimension", 384),
                metric=kwargs.get("metric", "cosine"),
                embedding_function=kwargs.get("embedding_function")
            )
        elif provider == VectorDBProvider.WEAVIATE:
            # Import and create Weaviate provider
            # from .providers.weaviate_vectordb import WeaviateVectorDB
            # return WeaviateVectorDB(**kwargs)
            raise NotImplementedError("Weaviate provider not yet implemented")
        elif provider == VectorDBProvider.QDRANT:
            # Import and create Qdrant provider
            # from .providers.qdrant_vectordb import QdrantVectorDB
            # return QdrantVectorDB(**kwargs)
            raise NotImplementedError("Qdrant provider not yet implemented")
        elif provider == VectorDBProvider.LOCAL:
            # Fall back to local ChromaDB
            from src.core.education.knowledge_retrieval import KnowledgeRetrieval
            return KnowledgeRetrieval()
        else:
            raise ValueError(f"Unknown Vector DB provider: {provider}")
    
    def get_llm(self) -> LLMInterface:
        """Get or create singleton LLM instance"""
        if not self._llm_instance:
            self._llm_instance = self.create_llm()
        return self._llm_instance
    
    def get_stt(self) -> STTInterface:
        """Get or create singleton STT instance"""
        if not self._stt_instance:
            self._stt_instance = self.create_stt()
        return self._stt_instance
    
    def get_tts(self) -> TTSInterface:
        """Get or create singleton TTS instance"""
        if not self._tts_instance:
            self._tts_instance = self.create_tts()
        return self._tts_instance
    
    def get_vectordb(self) -> VectorDBInterface:
        """Get or create singleton Vector DB instance"""
        if not self._vectordb_instance:
            self._vectordb_instance = self.create_vectordb()
        return self._vectordb_instance
    
    @classmethod
    def from_env(cls) -> 'CloudAIFactory':
        """Create factory instance from environment variables"""
        config = {
            'llm_provider': os.getenv('LLM_PROVIDER', 'openai'),
            'stt_provider': os.getenv('STT_PROVIDER', 'google'),
            'tts_provider': os.getenv('TTS_PROVIDER', 'aws_polly'),
            'vectordb_provider': os.getenv('VECTORDB_PROVIDER', 'pinecone'),
            'use_cloud': os.getenv('USE_CLOUD_AI', 'true').lower() == 'true'
        }
        return cls(config)


# Global factory instance
_factory = None


def get_cloud_ai_factory() -> CloudAIFactory:
    """Get global CloudAI factory instance"""
    global _factory
    if _factory is None:
        _factory = CloudAIFactory.from_env()
    return _factory