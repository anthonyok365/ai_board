"""
Configuration module for AI Board of Directors Backend.
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for Language Model providers."""
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class Config:
    """
    Central configuration class.
    Now defaults to Groq with latest stable models.
    """
    PROVIDER_GEMINI = "gemini"
    PROVIDER_GROQ = "groq"

    # Updated with current Groq models (June 2026)
    DEFAULT_CONFIGS = {
        PROVIDER_GEMINI: LLMConfig(
            provider=PROVIDER_GEMINI,
            model="gemini-3.5-flash",
            temperature=0.7,
            max_tokens=2048,
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta"
        ),
        PROVIDER_GROQ: LLMConfig(
            provider=PROVIDER_GROQ,
            model="openai/gpt-oss-20b",          # Fast + reliable (recommended)
            temperature=0.7,
            max_tokens=2048,
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        ),
    }

    # Premium / stronger models
    PREMIUM_CONFIGS = {
        PROVIDER_GEMINI: LLMConfig(
            provider=PROVIDER_GEMINI,
            model="gemini-2.5-flash",   # or gemini-2.5-pro if available
            temperature=0.7,
            max_tokens=4096,
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta"
        ),
        PROVIDER_GROQ: LLMConfig(
            provider=PROVIDER_GROQ,
            model="openai/gpt-oss-120b",   # Stronger reasoning
            temperature=0.7,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        ),
    }

    def __init__(self, use_premium: bool = False):
        self.use_premium = use_premium
        # Default to Groq (much more stable than Gemini)
        self._provider = os.getenv("LLM_PROVIDER", self.PROVIDER_GROQ)
        self._validate_provider()

    def _validate_provider(self) -> None:
        if self._provider not in self.DEFAULT_CONFIGS:
            raise ValueError(
                f"Unsupported LLM provider: {self._provider}. "
                f"Supported: {list(self.DEFAULT_CONFIGS.keys())}"
            )

    @property
    def llm_config(self) -> LLMConfig:
        configs = self.PREMIUM_CONFIGS if self.use_premium else self.DEFAULT_CONFIGS
        return configs[self._provider]

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self.llm_config.model

    @property
    def api_key(self) -> Optional[str]:
        return self.llm_config.api_key

    def get_llm(self):
        config = self.llm_config
        if not config.api_key:
            raise ValueError(
                f"API key not found for {config.provider}. "
                f"Set GEMINI_API_KEY or GROQ_API_KEY in your .env file."
            )

        if config.provider == self.PROVIDER_GEMINI:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config.model,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                google_api_key=config.api_key
            )
        elif config.provider == self.PROVIDER_GROQ:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=config.api_key,
                base_url=config.base_url
            )

        raise ValueError(f"Unsupported provider: {config.provider}")


# Global instance
config = Config()


def get_config() -> Config:
    return config


def set_provider(provider: str, use_premium: bool = False) -> None:
    global config
    config = Config(use_premium=use_premium)
    config._provider = provider
    config._validate_provider()
