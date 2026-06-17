"""
Configuration module for AI Board of Directors Backend.

Loads environment variables for API keys and model selection.
Provides sensible defaults and easy configuration switching.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for Language Model providers."""
    
    provider: str  # 'openai', 'anthropic', 'groq'
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key: Optional[str] = None


class Config:
    """
    Central configuration class for the AI Board of Directors application.
    
    Supports multiple LLM providers with environment variable configuration.
    Defaults to cost-effective models for efficiency.
    """
    
    # Supported LLM Providers
    PROVIDER_OPENAI = "openai"
    PROVIDER_ANTHROPIC = "anthropic"
    PROVIDER_GROQ = "groq"
    
    # Default configurations per provider
    DEFAULT_CONFIGS = {
        PROVIDER_OPENAI: LLMConfig(
            provider=PROVIDER_OPENAI,
            model="gpt-4o-mini",  # Fast and cost-effective default
            temperature=0.7,
            max_tokens=2048,
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        PROVIDER_ANTHROPIC: LLMConfig(
            provider=PROVIDER_ANTHROPIC,
            model="claude-sonnet-4-20250514",  # Cost-effective default
            temperature=0.7,
            max_tokens=2048,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        PROVIDER_GROQ: LLMConfig(
            provider=PROVIDER_GROQ,
            model="llama-3.3-70b-versatile",  # Fast and free tier available
            temperature=0.7,
            max_tokens=2048,
            api_key=os.getenv("GROQ_API_KEY")
        ),
    }
    
    # Premium models for when stronger reasoning is needed
    PREMIUM_CONFIGS = {
        PROVIDER_OPENAI: LLMConfig(
            provider=PROVIDER_OPENAI,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4096,
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        PROVIDER_ANTHROPIC: LLMConfig(
            provider=PROVIDER_ANTHROPIC,
            model="claude-opus-4-20250514",
            temperature=0.7,
            max_tokens=4096,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        PROVIDER_GROQ: LLMConfig(
            provider=PROVIDER_GROQ,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY")
        ),
    }
    
    def __init__(self, use_premium: bool = False):
        """
        Initialize configuration.
        
        Args:
            use_premium: If True, use stronger (but more expensive) models.
        """
        self.use_premium = use_premium
        self._provider = os.getenv("LLM_PROVIDER", self.PROVIDER_OPENAI)
        self._validate_provider()
    
    def _validate_provider(self) -> None:
        """Validate that the configured provider is supported."""
        if self._provider not in self.DEFAULT_CONFIGS:
            raise ValueError(
                f"Unsupported LLM provider: {self._provider}. "
                f"Supported providers: {list(self.DEFAULT_CONFIGS.keys())}"
            )
    
    @property
    def llm_config(self) -> LLMConfig:
        """Get the current LLM configuration."""
        configs = self.PREMIUM_CONFIGS if self.use_premium else self.DEFAULT_CONFIGS
        return configs[self._provider]
    
    @property
    def provider(self) -> str:
        """Get the current LLM provider."""
        return self._provider
    
    @property
    def model(self) -> str:
        """Get the current model name."""
        return self.llm_config.model
    
    @property
    def api_key(self) -> Optional[str]:
        """Get the API key for the current provider."""
        return self.llm_config.api_key
    
    def get_llm(self):
        """
        Get a configured LLM instance based on current settings.
        
        Returns:
            Configured LangChain LLM instance.
            
        Raises:
            ValueError: If API key is not configured for the provider.
        """
        config = self.llm_config
        
        if not config.api_key:
            raise ValueError(
                f"API key not found for provider '{config.provider}'. "
                f"Please set the appropriate environment variable."
            )
        
        if config.provider == self.PROVIDER_OPENAI:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key
            )
        
        elif config.provider == self.PROVIDER_ANTHROPIC:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config.model,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                api_key=config.api_key
            )
        
        elif config.provider == self.PROVIDER_GROQ:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key
            )
        
        raise ValueError(f"Unsupported provider: {config.provider}")


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def set_provider(provider: str, use_premium: bool = False) -> None:
    """
    Change the LLM provider at runtime.
    
    Args:
        provider: One of 'openai', 'anthropic', 'groq'.
        use_premium: Whether to use premium models.
    """
    global config
    config = Config(use_premium=use_premium)
    config._provider = provider
    config._validate_provider()