"""
LLM integration service for communicating with various LLM providers.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.models import LLMConfiguration
from app.schemas.chat import ChatErrorResponse

settings = get_settings()


class LLMIntegrationError(Exception):
    """Base exception for LLM integration errors."""
    pass


class LLMProviderError(LLMIntegrationError):
    """Exception for LLM provider-specific errors."""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None, details: Optional[Dict] = None):
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class LLMQuotaExceededError(LLMIntegrationError):
    """Exception for quota exceeded errors."""
    pass


class LLMService:
    """Service for integrating with various LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': self._handle_openai_request,
            'anthropic': self._handle_anthropic_request,
            'ollama': self._handle_ollama_request,
            'azure_openai': self._handle_azure_openai_request,
        }
        self.timeout = 120  # 2 minutes timeout for LLM requests
    
    async def send_message(
        self, 
        message: str, 
        llm_config: LLMConfiguration
    ) -> Tuple[str, int, int, float]:
        """
        Send a message to the specified LLM and return response with usage info.
        
        Args:
            message: User message to send
            llm_config: LLM configuration object
            
        Returns:
            Tuple of (response_text, prompt_tokens, completion_tokens, estimated_cost)
            
        Raises:
            LLMProviderError: For provider-specific errors
            LLMIntegrationError: For general integration errors
        """
        if not llm_config.enabled:
            raise LLMIntegrationError(f"LLM configuration '{llm_config.model_name}' is disabled")
        
        provider = llm_config.provider.lower()
        if provider not in self.providers:
            raise LLMIntegrationError(f"Unsupported LLM provider: {provider}")
        
        try:
            handler = self.providers[provider]
            result = await handler(message, llm_config)
            return result
        except httpx.TimeoutException:
            raise LLMProviderError(
                f"Request to {provider} timed out after {self.timeout} seconds",
                provider=provider,
                error_code="timeout"
            )
        except httpx.HTTPStatusError as e:
            raise LLMProviderError(
                f"HTTP error from {provider}: {e.response.status_code}",
                provider=provider,
                error_code=str(e.response.status_code),
                details={"response_text": e.response.text}
            )
        except Exception as e:
            raise LLMIntegrationError(f"Unexpected error communicating with {provider}: {str(e)}")
    
    async def _handle_openai_request(
        self, 
        message: str, 
        llm_config: LLMConfiguration
    ) -> Tuple[str, int, int, float]:
        """Handle OpenAI API requests."""
        config = llm_config.config_json or {}
        api_key = self._get_api_key(llm_config)
        
        # Default OpenAI configuration
        model = config.get("model", "gpt-3.5-turbo")
        max_tokens = config.get("max_tokens", 1000)
        temperature = config.get("temperature", 0.7)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False  # Start with non-streaming for simplicity
        }
        
        base_url = llm_config.base_url or "https://api.openai.com/v1"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response and usage info
            assistant_message = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Estimate cost (rough estimates for GPT-3.5-turbo)
            estimated_cost = self._estimate_openai_cost(model, prompt_tokens, completion_tokens)
            
            return assistant_message, prompt_tokens, completion_tokens, estimated_cost
    
    async def _handle_anthropic_request(
        self, 
        message: str, 
        llm_config: LLMConfiguration
    ) -> Tuple[str, int, int, float]:
        """Handle Anthropic Claude API requests."""
        # Placeholder for Anthropic implementation
        raise LLMProviderError(
            "Anthropic provider not yet implemented",
            provider="anthropic",
            error_code="not_implemented"
        )
    
    async def _handle_ollama_request(
        self, 
        message: str, 
        llm_config: LLMConfiguration
    ) -> Tuple[str, int, int, float]:
        """Handle Ollama local model requests."""
        config = llm_config.config_json or {}
        model = config.get("model", "llama2")
        
        base_url = llm_config.base_url or settings.OLLAMA_BASE_URL
        
        payload = {
            "model": model,
            "prompt": message,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            assistant_message = data.get("response", "")
            
            # Ollama doesn't provide token counts, so we estimate
            prompt_tokens = len(message.split()) * 1.3  # Rough token estimation
            completion_tokens = len(assistant_message.split()) * 1.3
            estimated_cost = 0.0  # Local models are free
            
            return assistant_message, int(prompt_tokens), int(completion_tokens), estimated_cost
    
    async def _handle_azure_openai_request(
        self, 
        message: str, 
        llm_config: LLMConfiguration
    ) -> Tuple[str, int, int, float]:
        """Handle Azure OpenAI API requests."""
        # Placeholder for Azure OpenAI implementation
        raise LLMProviderError(
            "Azure OpenAI provider not yet implemented",
            provider="azure_openai",
            error_code="not_implemented"
        )
    
    def _get_api_key(self, llm_config: LLMConfiguration) -> str:
        """Get API key for the LLM configuration."""
        # First try the encrypted API key from config
        if llm_config.api_key_encrypted:
            # In a real implementation, this would be decrypted
            # For now, we assume it's an environment variable reference
            if llm_config.api_key_encrypted.startswith("$"):
                env_var = llm_config.api_key_encrypted[1:]
                api_key = os.getenv(env_var)
                if not api_key:
                    raise LLMProviderError(
                        f"API key environment variable '{env_var}' not found",
                        provider=llm_config.provider,
                        error_code="missing_api_key"
                    )
                return api_key
            else:
                # Assume it's the actual key (not recommended for production)
                return llm_config.api_key_encrypted
        
        # Try configuration settings first
        provider = llm_config.provider.lower()
        if provider == "openai" and settings.OPENAI_API_KEY:
            return settings.OPENAI_API_KEY
        elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            return settings.ANTHROPIC_API_KEY
        elif provider == "azure_openai" and settings.AZURE_OPENAI_API_KEY:
            return settings.AZURE_OPENAI_API_KEY
        
        # Fallback to environment variables
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure_openai": "AZURE_OPENAI_API_KEY"
        }
        
        env_var = env_vars.get(provider)
        if env_var:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key
        
        raise LLMProviderError(
            f"No API key found for provider '{provider}'. Please configure API key in admin settings or environment variables.",
            provider=provider,
            error_code="missing_api_key"
        )
    
    def _estimate_openai_cost(
        self, 
        model: str, 
        prompt_tokens: int, 
        completion_tokens: int
    ) -> float:
        """Estimate cost for OpenAI models (rough estimates)."""
        # Pricing as of 2024 (approximate)
        pricing = {
            "gpt-4": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
            "gpt-4-turbo": {"prompt": 0.01 / 1000, "completion": 0.03 / 1000},
            "gpt-3.5-turbo": {"prompt": 0.001 / 1000, "completion": 0.002 / 1000},
            "gpt-3.5-turbo-16k": {"prompt": 0.003 / 1000, "completion": 0.004 / 1000}
        }
        
        # Default to GPT-3.5-turbo pricing if model not found
        model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
        
        prompt_cost = prompt_tokens * model_pricing["prompt"]
        completion_cost = completion_tokens * model_pricing["completion"]
        
        return round(prompt_cost + completion_cost, 6)
    
    def is_provider_supported(self, provider: str) -> bool:
        """Check if a provider is supported."""
        return provider.lower() in self.providers
    
    def get_supported_providers(self) -> List[str]:
        """Get list of supported providers."""
        return list(self.providers.keys())


# Global LLM service instance
llm_service = LLMService()
