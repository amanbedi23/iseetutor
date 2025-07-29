"""
Cloud AI Service Interfaces

This module provides abstract base classes for different AI services,
allowing easy switching between providers (OpenAI, Google, AWS, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"  # Fallback to local Llama


class STTProvider(str, Enum):
    """Supported Speech-to-Text providers"""
    GOOGLE = "google"
    AWS = "aws"
    AZURE = "azure"
    LOCAL = "local"  # Fallback to local Whisper


class TTSProvider(str, Enum):
    """Supported Text-to-Speech providers"""
    GOOGLE = "google"
    AWS_POLLY = "aws_polly"
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"
    LOCAL = "local"  # Fallback to local Piper


class VectorDBProvider(str, Enum):
    """Supported Vector Database providers"""
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    LOCAL = "local"  # Fallback to ChromaDB


@dataclass
class Document:
    """Document structure for vector search results"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    usage: Dict[str, int]  # tokens used
    model: str
    finish_reason: str


@dataclass
class AudioConfig:
    """Audio configuration for STT/TTS"""
    sample_rate: int = 16000
    channels: int = 1
    language: str = "en-US"
    voice: Optional[str] = None
    speed: float = 1.0


class LLMInterface(ABC):
    """Abstract interface for Language Model providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        mode: str = "tutor"
    ) -> LLMResponse:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        mode: str = "tutor"
    ) -> AsyncGenerator[str, None]:
        """Generate text completion with streaming"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        pass


class STTInterface(ABC):
    """Abstract interface for Speech-to-Text providers"""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        config: AudioConfig
    ) -> str:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        config: AudioConfig
    ) -> AsyncGenerator[str, None]:
        """Transcribe audio stream in real-time"""
        pass


class TTSInterface(ABC):
    """Abstract interface for Text-to-Speech providers"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        config: AudioConfig
    ) -> bytes:
        """Synthesize text to audio"""
        pass
    
    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        config: AudioConfig
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize text to audio with streaming"""
        pass
    
    @abstractmethod
    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get available voices"""
        pass


class VectorDBInterface(ABC):
    """Abstract interface for Vector Database providers"""
    
    @abstractmethod
    async def index(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "default"
    ) -> None:
        """Index documents in vector database"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        collection: str = "default",
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        ids: List[str],
        collection: str = "default"
    ) -> None:
        """Delete documents by ID"""
        pass
    
    @abstractmethod
    async def update(
        self,
        id: str,
        document: Dict[str, Any],
        collection: str = "default"
    ) -> None:
        """Update a document"""
        pass