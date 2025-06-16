"""
Unified LLM Client for Sophia AI Agents
Automatically uses the configured gateway or falls back to direct APIs
"""

from typing import List, Dict, Any, Optional
import logging
from backend.config.settings import settings
from backend.integrations.llm_gateway import get_llm_gateway, PortkeyGateway

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client that abstracts the underlying provider
    Uses Portkey gateway when available, falls back to direct APIs
    """
    
    def __init__(self):
        self.gateway = None
        self._setup_client()
    
    def _setup_client(self):
        """Set up the appropriate LLM client based on configuration"""
        # Try to use Portkey gateway first
        if settings.api_keys.llm_gateway == "portkey" and settings.api_keys.portkey_api_key:
            try:
                self.gateway = get_llm_gateway()
                logger.info("Using Portkey LLM gateway with OpenRouter as primary")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Portkey gateway: {e}")
        
        # Fallback to direct APIs
        if settings.api_keys.openai_api_key:
            logger.info("Using OpenAI API directly")
            self._setup_openai()
        elif settings.api_keys.anthropic_api_key:
            logger.info("Using Anthropic API directly")
            self._setup_anthropic()
        else:
            logger.error("No LLM provider configured!")
            raise ValueError("No LLM provider configured. Please set up Portkey or direct API keys.")
    
    def _setup_openai(self):
        """Set up direct OpenAI client"""
        try:
            import openai
            openai.api_key = settings.api_keys.openai_api_key
            self.provider = "openai"
        except ImportError:
            logger.error("OpenAI library not installed. Run: pip install openai")
            raise
    
    def _setup_anthropic(self):
        """Set up direct Anthropic client"""
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.api_keys.anthropic_api_key
            )
            self.provider = "anthropic"
        except ImportError:
            logger.error("Anthropic library not installed. Run: pip install anthropic")
            raise
    
    async def complete(self,
                      messages: List[Dict[str, str]],
                      model: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: int = 4096,
                      **kwargs) -> str:
        """
        Get completion from LLM
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model name (auto-selected if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text content
        """
        # Use gateway if available
        if self.gateway:
            response = await self.gateway.complete(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response["choices"][0]["message"]["content"]
        
        # Direct API fallbacks
        if self.provider == "openai":
            return await self._complete_openai(messages, model, temperature, max_tokens, **kwargs)
        elif self.provider == "anthropic":
            return await self._complete_anthropic(messages, model, temperature, max_tokens, **kwargs)
        
        raise ValueError("No LLM provider available")
    
    async def _complete_openai(self, messages, model, temperature, max_tokens, **kwargs):
        """Direct OpenAI completion"""
        import openai
        
        response = await openai.ChatCompletion.acreate(
            model=model or "gpt-4-turbo-preview",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def _complete_anthropic(self, messages, model, temperature, max_tokens, **kwargs):
        """Direct Anthropic completion"""
        # Convert messages to Anthropic format
        system_message = ""
        conversation = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = await self.anthropic_client.messages.create(
            model=model or "claude-3-sonnet-20240229",
            system=system_message,
            messages=conversation,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.content[0].text
    
    async def complete_with_context(self,
                                  prompt: str,
                                  context: str = "",
                                  system_prompt: Optional[str] = None,
                                  **kwargs) -> str:
        """
        Convenience method for completion with context
        
        Args:
            prompt: User prompt
            context: Additional context to include
            system_prompt: System message (uses default if not provided)
            
        Returns:
            Generated response
        """
        messages = []
        
        # System prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system", 
                "content": "You are Sophia AI, an intelligent assistant for Pay Ready company. "
                          "You help with business intelligence, data analysis, and operational insights."
            })
        
        # Add context if provided
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
        
        # Add main prompt
        messages.append({"role": "user", "content": prompt})
        
        return await self.complete(messages, **kwargs)
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if self.gateway:
            return self.gateway.get_available_models()
        
        if self.provider == "openai":
            return ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]
        elif self.provider == "anthropic":
            return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-2.1"]
        
        return []


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# Example usage for agents
async def analyze_text(text: str, analysis_type: str = "general") -> str:
    """
    Example function showing how agents can use the LLM client
    
    Args:
        text: Text to analyze
        analysis_type: Type of analysis (general, sentiment, summary, etc.)
        
    Returns:
        Analysis result
    """
    client = get_llm_client()
    
    prompts = {
        "general": "Analyze the following text and provide key insights:",
        "sentiment": "Analyze the sentiment of the following text:",
        "summary": "Provide a concise summary of the following text:",
        "action_items": "Extract action items from the following text:"
    }
    
    prompt = prompts.get(analysis_type, prompts["general"])
    
    return await client.complete_with_context(
        prompt=prompt,
        context=text,
        temperature=0.3,  # Lower temperature for analysis tasks
        max_tokens=1000
    ) 