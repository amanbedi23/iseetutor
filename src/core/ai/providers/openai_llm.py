"""
OpenAI LLM Provider Implementation

Provides GPT-3.5/GPT-4 integration for the ISEE Tutor application.
"""

import os
from typing import Optional, AsyncGenerator, List, Dict, Any
import openai
from openai import AsyncOpenAI
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from ..interfaces import LLMInterface, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLM(LLMInterface):
    """OpenAI GPT implementation for LLM services"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        organization: Optional[str] = None
    ):
        """
        Initialize OpenAI LLM provider
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
            organization: Optional organization ID
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            organization=organization
        )
        
        # System prompts for different modes
        self.system_prompts = {
            "tutor": """You are an expert ISEE tutor helping students prepare for the ISEE test. 
            You are patient, encouraging, and skilled at explaining complex concepts in age-appropriate ways. 
            Focus on ISEE test content including verbal reasoning, quantitative reasoning, reading comprehension, 
            and mathematics achievement. Always provide step-by-step explanations and encourage critical thinking.""",
            
            "friend": """You are a friendly, warm, and supportive companion for children. 
            You speak in an age-appropriate manner, showing genuine interest in their thoughts and feelings. 
            You're encouraging, positive, and help build confidence. Keep responses engaging and fun.""",
            
            "hybrid": """You are an intelligent educational companion that seamlessly blends learning with friendly conversation. 
            You can help with ISEE test preparation when needed, but also engage in general knowledge discussions, 
            answer curious questions, and be a supportive friend. Adapt your tone based on the context."""
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        mode: str = "tutor"
    ) -> LLMResponse:
        """
        Generate text completion using OpenAI
        
        Args:
            prompt: User prompt
            system_prompt: Optional override for system prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            mode: Interaction mode (tutor/friend/hybrid)
            
        Returns:
            LLMResponse with generated text and metadata
        """
        try:
            # Use provided system prompt or default based on mode
            if not system_prompt:
                system_prompt = self.system_prompts.get(mode, self.system_prompts["tutor"])
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,
                stream=False
            )
            
            completion = response.choices[0]
            
            return LLMResponse(
                content=completion.message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                model=response.model,
                finish_reason=completion.finish_reason
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {str(e)}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        mode: str = "tutor"
    ) -> AsyncGenerator[str, None]:
        """
        Generate text completion with streaming
        
        Args:
            prompt: User prompt
            system_prompt: Optional override for system prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            mode: Interaction mode (tutor/friend/hybrid)
            
        Yields:
            Generated text chunks
        """
        try:
            # Use provided system prompt or default based on mode
            if not system_prompt:
                system_prompt = self.system_prompts.get(mode, self.system_prompts["tutor"])
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        model_info = {
            "gpt-3.5-turbo": {
                "max_tokens": 4096,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015
            },
            "gpt-4": {
                "max_tokens": 8192,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06
            },
            "gpt-4-turbo": {
                "max_tokens": 128000,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03
            }
        }
        
        return model_info.get(self.model, {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0005,
            "cost_per_1k_output": 0.0015
        })