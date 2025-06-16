"""
LLM Gateway Integration using Portkey
Provides unified access to multiple LLM providers with automatic fallbacks
"""

import os
import json
from typing import Optional, Dict, Any, List
import aiohttp
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers through Portkey"""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    TOGETHER = "together"
    ANYSCALE = "anyscale"


@dataclass
class LLMConfig:
    """Configuration for LLM Gateway"""
    portkey_api_key: str
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "openrouter/anthropic/claude-3-opus"
    fallback_models: List[str] = None
    max_retries: int = 3
    timeout: int = 120
    cache_enabled: bool = True
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = [
                "openrouter/anthropic/claude-3-sonnet",
                "openrouter/openai/gpt-4-turbo",
                "openai/gpt-4-turbo-preview",
                "anthropic/claude-3-sonnet-20240229"
            ]


class PortkeyGateway:
    """
    Unified LLM Gateway using Portkey.ai
    Provides automatic fallbacks, load balancing, and monitoring
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the gateway with configuration"""
        if config is None:
            config = LLMConfig(
                portkey_api_key=os.getenv("PORTKEY_API_KEY", ""),
                openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        
        self.config = config
        self.base_url = "https://api.portkey.ai/v1"
        
        # Configure headers for Portkey
        self.headers = {
            "x-portkey-api-key": self.config.portkey_api_key,
            "Content-Type": "application/json"
        }
        
        # Set up virtual keys for each provider
        self._setup_virtual_keys()
        
    def _setup_virtual_keys(self):
        """Set up virtual keys for each provider in Portkey"""
        self.virtual_keys = {}
        
        # OpenRouter as primary
        if self.config.openrouter_api_key:
            self.headers["x-portkey-virtual-key-openrouter"] = self.config.openrouter_api_key
            self.virtual_keys["openrouter"] = True
            logger.info("OpenRouter configured as primary LLM provider")
        
        # Fallback providers
        if self.config.openai_api_key:
            self.headers["x-portkey-virtual-key-openai"] = self.config.openai_api_key
            self.virtual_keys["openai"] = True
            logger.info("OpenAI configured as fallback provider")
            
        if self.config.anthropic_api_key:
            self.headers["x-portkey-virtual-key-anthropic"] = self.config.anthropic_api_key
            self.virtual_keys["anthropic"] = True
            logger.info("Anthropic configured as fallback provider")
    
    def _create_portkey_config(self) -> Dict[str, Any]:
        """Create Portkey configuration with fallbacks"""
        config = {
            "retry": {
                "attempts": self.config.max_retries,
            },
            "cache": {
                "mode": "semantic" if self.config.cache_enabled else "none"
            }
        }
        
        # Build strategy with OpenRouter as primary
        targets = []
        
        # Primary: OpenRouter
        if "openrouter" in self.virtual_keys:
            targets.append({
                "provider": "openrouter",
                "override_params": {
                    "model": self.config.default_model.replace("openrouter/", "")
                }
            })
        
        # Fallbacks
        for model in self.config.fallback_models:
            if "/" in model:
                provider, model_name = model.split("/", 1)
                if provider in self.virtual_keys and provider != "openrouter":
                    targets.append({
                        "provider": provider,
                        "override_params": {
                            "model": model_name
                        }
                    })
        
        if targets:
            config["strategy"] = {
                "mode": "fallback",
                "on_status_codes": [429, 500, 502, 503],
                "targets": targets
            }
        
        return config
    
    async def complete(self, 
                      messages: List[Dict[str, str]], 
                      model: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: int = 4096,
                      **kwargs) -> Dict[str, Any]:
        """
        Send completion request through Portkey gateway
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override (defaults to config.default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Response from the LLM
        """
        # Create Portkey config
        portkey_config = self._create_portkey_config()
        
        # Add config to headers
        self.headers["x-portkey-config"] = json.dumps(portkey_config)
        
        # Build request
        data = {
            "messages": messages,
            "model": model or self.config.default_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # Log request info
        logger.info(f"Sending request through Portkey gateway: model={data['model']}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        logger.error(f"LLM Gateway error: {response.status} - {result}")
                        raise Exception(f"LLM Gateway error: {result}")
                    
                    # Log which provider was used (from Portkey metadata)
                    if "x-portkey-provider" in response.headers:
                        provider_used = response.headers["x-portkey-provider"]
                        logger.info(f"Request fulfilled by: {provider_used}")
                    
                    return result
                    
            except aiohttp.ClientTimeout:
                logger.error("LLM Gateway request timed out")
                raise Exception("LLM Gateway timeout")
            except Exception as e:
                logger.error(f"LLM Gateway error: {str(e)}")
                raise
    
    async def stream_complete(self,
                            messages: List[Dict[str, str]],
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            **kwargs):
        """
        Stream completion through Portkey gateway
        
        Yields chunks of the response as they arrive
        """
        portkey_config = self._create_portkey_config()
        self.headers["x-portkey-config"] = json.dumps(portkey_config)
        
        data = {
            "messages": messages,
            "model": model or self.config.default_model,
            "temperature": temperature,
            "stream": True,
            **kwargs
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data
            ) as response:
                async for line in response.content:
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            chunk = line[6:]
                            if chunk != "[DONE]":
                                yield json.loads(chunk)
    
    def get_available_models(self) -> List[str]:
        """Get list of available models based on configured providers"""
        models = []
        
        if "openrouter" in self.virtual_keys:
            models.extend([
                "openrouter/anthropic/claude-3-opus",
                "openrouter/anthropic/claude-3-sonnet", 
                "openrouter/openai/gpt-4-turbo",
                "openrouter/google/gemini-pro",
                "openrouter/meta-llama/llama-3-70b"
            ])
        
        if "openai" in self.virtual_keys:
            models.extend([
                "openai/gpt-4-turbo-preview",
                "openai/gpt-4",
                "openai/gpt-3.5-turbo"
            ])
            
        if "anthropic" in self.virtual_keys:
            models.extend([
                "anthropic/claude-3-opus-20240229",
                "anthropic/claude-3-sonnet-20240229",
                "anthropic/claude-2.1"
            ])
        
        return models


# Singleton instance
_gateway_instance: Optional[PortkeyGateway] = None


def get_llm_gateway() -> PortkeyGateway:
    """Get or create the LLM gateway singleton"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = PortkeyGateway()
    return _gateway_instance


# Convenience function for quick completions
async def complete(prompt: str, **kwargs) -> str:
    """
    Simple completion function using the default gateway
    
    Args:
        prompt: The prompt text
        **kwargs: Additional parameters for the completion
        
    Returns:
        The generated text
    """
    gateway = get_llm_gateway()
    
    messages = [{"role": "user", "content": prompt}]
    
    response = await gateway.complete(messages, **kwargs)
    
    return response["choices"][0]["message"]["content"]


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_gateway():
        # Test the gateway
        gateway = get_llm_gateway()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
        
        # Test completion
        response = await gateway.complete(messages)
        print("Response:", response["choices"][0]["message"]["content"])
        
        # Test available models
        models = gateway.get_available_models()
        print("\nAvailable models:", models)
    
    asyncio.run(test_gateway()) 