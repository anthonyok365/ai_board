"""
Backend client for AI Board Frontend.

Provides a clean interface to communicate with the backend
either via direct Python import or HTTP API.
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, Generator, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MeetingResult:
    """Result of a board meeting."""
    success: bool
    thread_id: str
    messages: list = field(default_factory=list)
    decision: Optional[str] = None
    error: Optional[str] = None
    rounds: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "thread_id": self.thread_id,
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content if hasattr(msg, 'content') else str(msg),
                    "name": getattr(msg, 'name', None),
                }
                for msg in self.messages
            ],
            "decision": self.decision,
            "error": self.error,
            "rounds": self.rounds,
            "timestamp": self.timestamp.isoformat(),
        }


class BackendClient:
    """
    Client for communicating with the AI Board Backend.
    
    Supports two modes:
    1. "import" - Direct Python import of backend module
    2. "api" - HTTP API calls to backend server
    """
    
    def __init__(
        self,
        backend_path: str = "../backend",
        api_url: str = "http://localhost:8000",
        mode: str = "import"
    ):
        """
        Initialize the backend client.
        
        Args:
            backend_path: Path to backend directory (for import mode).
            api_url: Backend API URL (for api mode).
            mode: "import" or "api".
        """
        self.backend_path = os.path.abspath(backend_path)
        self.api_url = api_url
        self.mode = mode
        self._backend_module = None
        
        logger.info(f"BackendClient initialized in '{mode}' mode")
        logger.info(f"Backend path: {self.backend_path}")
    
    def _ensure_backend_imported(self):
        """Ensure the backend module is imported."""
        if self._backend_module is not None:
            return
        
        # Add backend path to sys.path
        if self.backend_path not in sys.path:
            sys.path.insert(0, self.backend_path)
        
        try:
            # Import backend main module
            import main as backend_main
            
            self._backend_module = backend_main
            logger.info("Backend module imported successfully")
        except ImportError as e:
            logger.error(f"Failed to import backend: {e}")
            raise ImportError(
                f"Could not import backend from {self.backend_path}. "
                f"Make sure the backend files exist and are properly installed."
            ) from e
    
    def run_meeting(
        self,
        query: str,
        thread_id: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_rounds: int = 6,
        use_premium: bool = False,
        recursion_limit: int = 25,
    ) -> MeetingResult:
        """
        Run a board meeting.
        
        Args:
            query: The business question to discuss.
            thread_id: Optional session identifier.
            provider: LLM provider (openai, anthropic, groq).
            model: Model name (uses default if not specified).
            temperature: LLM temperature setting.
            max_rounds: Maximum discussion rounds.
            use_premium: Use premium model.
            recursion_limit: Maximum graph recursion depth.
            
        Returns:
            MeetingResult with meeting output.
        """
        # Generate thread_id if not provided
        if thread_id is None:
            thread_id = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting meeting: thread_id={thread_id}, provider={provider}")
        
        if self.mode == "api":
            return self._run_meeting_api(
                query, thread_id, provider, model, temperature, max_rounds
            )
        else:
            return self._run_meeting_import(
                query, thread_id, provider, model, temperature, max_rounds,
                use_premium, recursion_limit
            )
    
    def _run_meeting_import(
        self,
        query: str,
        thread_id: str,
        provider: str,
        model: Optional[str],
        temperature: float,
        max_rounds: int,
        use_premium: bool,
        recursion_limit: int,
    ) -> MeetingResult:
        """Run meeting via direct Python import."""
        self._ensure_backend_imported()
        
        try:
            # Import and configure backend
            from config import set_provider
            
            # Set the provider
            set_provider(provider, use_premium=use_premium)
            
            # Run the meeting
            result = self._backend_module.run_board_meeting(
                query=query,
                thread_id=thread_id,
                recursion_limit=recursion_limit,
            )
            
            # Convert to MeetingResult
            return MeetingResult(
                success=result.get("success", False),
                thread_id=result.get("thread_id", thread_id),
                messages=result.get("messages", []),
                decision=result.get("decision"),
                error=result.get("error"),
                rounds=result.get("rounds", 0),
            )
            
        except Exception as e:
            logger.error(f"Error running meeting: {e}")
            logger.error(traceback.format_exc())
            return MeetingResult(
                success=False,
                thread_id=thread_id,
                error=f"Error: {str(e)}",
            )
    
    def _run_meeting_api(
        self,
        query: str,
        thread_id: str,
        provider: str,
        model: Optional[str],
        temperature: float,
        max_rounds: int,
    ) -> MeetingResult:
        """Run meeting via HTTP API."""
        try:
            response = requests.post(
                f"{self.api_url}/meeting",
                json={
                    "query": query,
                    "thread_id": thread_id,
                    "provider": provider,
                    "model": model,
                    "temperature": temperature,
                    "max_rounds": max_rounds,
                },
                timeout=300,  # 5 minute timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            return MeetingResult(
                success=data.get("success", False),
                thread_id=data.get("thread_id", thread_id),
                messages=data.get("messages", []),
                decision=data.get("decision"),
                error=data.get("error"),
                rounds=data.get("rounds", 0),
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return MeetingResult(
                success=False,
                thread_id=thread_id,
                error=f"API request failed: {str(e)}",
            )
    
    def get_meeting_history(self, thread_id: str) -> Optional[dict]:
        """
        Get history of an existing meeting.
        
        Args:
            thread_id: The meeting thread ID.
            
        Returns:
            Meeting state dictionary or None.
        """
        if self.mode == "api":
            try:
                response = requests.get(
                    f"{self.api_url}/meeting/{thread_id}",
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return None
        else:
            self._ensure_backend_imported()
            return self._backend_module.get_meeting_history(thread_id)
    
    def save_meeting(self, result: MeetingResult, filepath: Optional[str] = None) -> str:
        """
        Save meeting result to a JSON file.
        
        Args:
            result: The meeting result to save.
            filepath: Optional custom filepath.
            
        Returns:
            Path to saved file.
        """
        if filepath is None:
            # Generate filename based on thread_id and timestamp
            filename = f"{result.thread_id}.json"
            filepath = os.path.join(
                os.path.dirname(__file__),
                "..",
                "meeting_history",
                filename
            )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save to JSON
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Meeting saved to {filepath}")
        return filepath
    
    def list_saved_meetings(self) -> list[dict]:
        """
        List all saved meeting files.
        
        Returns:
            List of meeting info dictionaries.
        """
        history_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "meeting_history"
        )
        
        meetings = []
        if os.path.exists(history_dir):
            for filename in os.listdir(history_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(history_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            meetings.append({
                                "filename": filename,
                                "filepath": filepath,
                                "thread_id": data.get("thread_id", filename[:-5]),
                                "timestamp": data.get("timestamp", ""),
                                "success": data.get("success", False),
                            })
                    except (json.JSONDecodeError, IOError):
                        continue
        
        # Sort by timestamp (newest first)
        meetings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return meetings


# Global client instance
_client: Optional[BackendClient] = None


def get_backend_client(
    backend_path: str = "../backend",
    api_url: str = "http://localhost:8000",
    mode: str = "import"
) -> BackendClient:
    """
    Get or create the global backend client instance.
    
    Args:
        backend_path: Path to backend directory.
        api_url: Backend API URL.
        mode: Client mode ("import" or "api").
        
    Returns:
        BackendClient instance.
    """
    global _client
    
    if _client is None:
        _client = BackendClient(
            backend_path=backend_path,
            api_url=api_url,
            mode=mode,
        )
    
    return _client


def reset_backend_client():
    """Reset the global client instance (useful for testing)."""
    global _client
    _client = None