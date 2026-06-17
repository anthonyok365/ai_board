"""
Configuration module for AI Board Frontend.

Loads environment variables and provides application settings.
Supports xAI (Grok) and Groq LLM providers.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    display_name: str
    api_key_env: str
    default_model: str
    premium_model: str
    base_url: str


class Config:
    """
    Central configuration class for the AI Board Frontend.
    
    Manages settings for LLM providers (xAI and Groq),
    backend connection, and application behavior.
    """
    
    # ============================================================================
    # LLM Provider Definitions
    # ============================================================================
    
    PROVIDERS = {
        "xai": LLMProviderConfig(
            name="xai",
            display_name="xAI (Grok)",
            api_key_env="XAI_API_KEY",
            default_model="grok-2",
            premium_model="grok-2",
            base_url="https://api.x.ai/v1",
        ),
        "groq": LLMProviderConfig(
            name="groq",
            display_name="Groq",
            api_key_env="GROQ_API_KEY",
            default_model="meta-llama/llama-4-scout-17b-16e-instruct",
            premium_model="meta-llama/llama-4-scout-17b-16e-instruct",
            base_url="https://api.groq.com/openai/v1",
        ),
    }
    
    # ============================================================================
    # Backend Configuration
    # ============================================================================
    
    # Path to backend directory (relative to frontend)
    BACKEND_PATH = os.getenv("BACKEND_PATH", "../backend")
    
    # Backend API URL (if using HTTP API mode)
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    
    # Mode: "import" (direct Python import) or "api" (HTTP requests)
    BACKEND_MODE = os.getenv("BACKEND_MODE", "import")
    
    # ============================================================================
    # UI Configuration
    # ============================================================================
    
    # Theme settings
    DEFAULT_THEME = os.getenv("THEME", "dark")
    
    # Meeting history directory
    HISTORY_DIR = os.path.join(os.path.dirname(__file__), "meeting_history")
    
    # Maximum meeting history files to keep
    MAX_HISTORY_FILES = 50
    
    # ============================================================================
    # Application Defaults
    # ============================================================================
    
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_ROUNDS = 6
    DEFAULT_RECURSION_LIMIT = 25
    
    def __init__(self):
        """Initialize configuration, creating necessary directories."""
        # Ensure history directory exists
        os.makedirs(self.HISTORY_DIR, exist_ok=True)
    
    def get_provider(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """
        Get provider configuration by name.
        
        Args:
            provider_name: The provider identifier.
            
        Returns:
            Provider config or None if not found.
        """
        return self.PROVIDERS.get(provider_name.lower())
    
    def get_api_key(self, provider_name: str) -> Optional[str]:
        """
        Get API key for a provider from environment.
        
        Args:
            provider_name: The provider identifier.
            
        Returns:
            API key or None if not set.
        """
        provider = self.get_provider(provider_name)
        if provider:
            return os.getenv(provider.api_key_env)
        return None
    
    def get_model(self, provider_name: str, use_premium: bool = False) -> str:
        """
        Get model name for a provider.
        
        Args:
            provider_name: The provider identifier.
            use_premium: Whether to use premium model.
            
        Returns:
            Model name.
        """
        provider = self.get_provider(provider_name)
        if provider:
            return provider.premium_model if use_premium else provider.default_model
        return "llama-3.3-70b-versatile"  # Default fallback
    
    def get_backend_module(self):
        """
        Dynamically import the backend module.
        
        Returns:
            Backend module with run_board_meeting function.
            
        Raises:
            ImportError: If backend cannot be imported.
        """
        import sys
        import os
        
        # Add backend path to sys.path
        backend_path = os.path.abspath(self.BACKEND_PATH)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Import the backend main module
        from main import run_board_meeting, get_meeting_history, continue_meeting
        
        return type('BackendModule', (), {
            'run_board_meeting': run_board_meeting,
            'get_meeting_history': get_meeting_history,
            'continue_meeting': continue_meeting,
        })()


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config