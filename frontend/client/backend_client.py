"""
Backend client for AI Board Frontend.

Provides two modes:
1. Import mode: Directly imports backend Python module (default)
2. API mode: Communicates via HTTP REST API
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class MeetingResult:
    """Structured result from a board meeting."""
    thread_id: str
    query: str
    status: str
    success: bool
    result: Dict[str, Any]
    messages: List[Any]
    error: Optional[str] = None
    rounds: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def decision(self) -> Optional[str]:
        """Extract the board decision from the result."""
        return self.result.get("decision") or self.result.get("board_decision")

    @property
    def executive_summary(self) -> Optional[str]:
        """Extract executive summary from the decision."""
        decision = self.decision
        if not decision:
            return None
        if "Executive Summary" in decision:
            parts = decision.split("##")
            for part in parts:
                if "Executive Summary" in part:
                    return part.strip()
        return decision[:500] + "..." if len(decision) > 500 else decision

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "thread_id": self.thread_id,
            "query": self.query,
            "status": self.status,
            "success": self.success,
            "result": self.result,
            "messages": [
                {"name": getattr(m, "name", ""), "content": getattr(m, "content", str(m))}
                for m in self.messages
            ],
            "error": self.error,
            "rounds": self.rounds,
            "timestamp": self.timestamp,
        }


class BackendClient:
    """
    Client for communicating with the AI Board backend.
    """

    def __init__(
        self,
        backend_mode: str = None,
        backend_api_url: str = None,
        backend_path: str = None
    ):
        # Always use API mode - import mode is not supported in production
        self.backend_mode = "api"
        self.backend_api_url = backend_api_url or os.getenv("BACKEND_API_URL", "https://ai-board-backend-fp0x.onrender.com")
        self.backend_path = backend_path
        self._backend_module = None

    def _get_backend(self):
        """Lazy load the backend module."""
        if self._backend_module is None:
            import os
            backend_path = os.path.abspath(self.backend_path)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            from main import run_board_meeting, get_meeting_history, continue_meeting
            self._backend_module = type('Backend', (), {
                'run_board_meeting': run_board_meeting,
                'get_meeting_history': get_meeting_history,
                'continue_meeting': continue_meeting,
            })()
        return self._backend_module

    def run_meeting(
        self,
        query: str,
        thread_id: Optional[str] = None,
        use_premium: bool = False,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_rounds: int = 10,
        recursion_limit: int = 50,
    ) -> MeetingResult:
        if self.backend_mode == "api":
            return self._run_meeting_api(query, thread_id, use_premium, provider)
        else:
            return self._run_meeting_import(query, thread_id, use_premium, provider)

    def _run_meeting_import(self, query, thread_id, use_premium, provider) -> MeetingResult:
        try:
            backend = self._get_backend()
            if provider:
                from config import set_provider
                set_provider(provider, use_premium)
            result = backend.run_board_meeting(query=query, thread_id=thread_id, use_premium=use_premium)
            return MeetingResult(
                thread_id=result.get("thread_id", thread_id or "unknown"),
                query=query,
                status="completed",
                success=result.get("success", True),
                result=result,
                messages=result.get("messages", []),
                error=result.get("error"),
                rounds=result.get("rounds", 0),
            )
        except Exception as e:
            logger.error(f"Error running meeting: {e}")
            raise

    def _run_meeting_api(self, query, thread_id, use_premium, provider) -> MeetingResult:
        import requests
        url = f"{self.backend_api_url}/meeting"
        payload = {
            "query": query,
            "thread_id": thread_id,
            "use_premium": use_premium,
            "provider": provider,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            
            # Extract result data
            result_data = data.get("result", {})
            
            return MeetingResult(
                thread_id=data.get("thread_id", thread_id or "unknown"),
                query=query,
                status=data.get("status", "completed"),
                success=result_data.get("success", True),
                result=result_data,
                messages=result_data.get("messages", data.get("messages", [])),
                error=result_data.get("error"),
                rounds=result_data.get("rounds", 0),
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"API error: {e}")
            raise Exception(f"Failed to connect to backend API: {e}")

    def get_meeting(self, thread_id: str) -> Optional[MeetingResult]:
        """Get a meeting by thread_id."""
        if self.backend_mode == "api":
            import requests
            url = f"{self.backend_api_url}/meeting/{thread_id}"
            response = requests.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            result_data = data.get("result", {})
            return MeetingResult(
                thread_id=data.get("thread_id", thread_id),
                query=data.get("query", ""),
                status=data.get("status", "found"),
                success=True,
                result=result_data,
                messages=result_data.get("messages", data.get("messages", [])),
                rounds=0,
            )
        else:
            backend = self._get_backend()
            result = backend.get_meeting_history(thread_id)
            if result:
                return MeetingResult(
                    thread_id=thread_id,
                    query="",
                    status="found",
                    success=True,
                    result={"messages": result},
                    messages=result,
                )
            return None

    def continue_meeting(self, thread_id: str, query: str, use_premium: bool = False) -> MeetingResult:
        if self.backend_mode == "api":
            import requests
            url = f"{self.backend_api_url}/meeting/continue"
            payload = {"thread_id": thread_id, "query": query}
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            result_data = data.get("result", {})
            return MeetingResult(
                thread_id=thread_id,
                query=query,
                status=data.get("status", "continued"),
                success=result_data.get("success", True),
                result=result_data,
                messages=result_data.get("messages", data.get("messages", [])),
                error=result_data.get("error"),
                rounds=result_data.get("rounds", 0),
            )
        else:
            backend = self._get_backend()
            result = backend.continue_meeting(thread_id=thread_id, additional_query=query, use_premium=use_premium)
            return MeetingResult(
                thread_id=thread_id,
                query=query,
                status="continued",
                success=result.get("success", True),
                result=result,
                messages=result.get("messages", []),
                error=result.get("error"),
                rounds=result.get("rounds", 0),
            )

    def list_meetings(self) -> List[Dict[str, Any]]:
        """List all meetings from the backend."""
        if self.backend_mode == "api":
            import requests
            url = f"{self.backend_api_url}/meetings"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        else:
            # Fall back to local file-based storage
            return self._list_local_meetings()

    def _list_local_meetings(self) -> List[Dict[str, Any]]:
        from pathlib import Path
        history_dir = Path(__file__).parent / "meeting_history"
        history_dir.mkdir(exist_ok=True)
        meetings = []
        for filepath in sorted(history_dir.glob("*.json"), reverse=True)[:20]:
            with open(filepath) as f:
                data = json.load(f)
                meetings.append({
                    "thread_id": data.get("thread_id", filepath.stem),
                    "query": data.get("query", ""),
                    "timestamp": data.get("timestamp", ""),
                    "filename": filepath.name
                })
        return meetings

    def save_meeting(self, result: MeetingResult) -> str:
        from pathlib import Path
        history_dir = Path(__file__).parent / "meeting_history"
        history_dir.mkdir(exist_ok=True)
        filepath = history_dir / f"{result.thread_id}.json"
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        return str(filepath)


_client: Optional[BackendClient] = None


def get_backend_client() -> BackendClient:
    global _client
    if _client is None:
        _client = BackendClient()
    return _client


def reset_backend_client() -> None:
    global _client
    _client = None
