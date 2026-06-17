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
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class MeetingResult:
    """Structured result from a board meeting."""
    thread_id: str
    query: str
    status: str
    result: Dict[str, Any]
    messages: List[Dict[str, Any]]
    timestamp: str

    def __init__(self, **kwargs):
        self.thread_id = kwargs.get("thread_id", "")
        self.query = kwargs.get("query", "")
        self.status = kwargs.get("status", "")
        self.result = kwargs.get("result", {})
        self.messages = kwargs.get("messages", [])
        self.timestamp = kwargs.get("timestamp", datetime.now().isoformat())

    @property
    def decision(self) -> Optional[str]:
        """Extract the board decision from the result."""
        return self.result.get("board_decision")

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
        self.backend_mode = backend_mode or os.getenv("BACKEND_MODE", "import")
        self.backend_api_url = backend_api_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self.backend_path = backend_path or os.getenv("BACKEND_PATH", "../backend")
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
        provider: Optional[str] = None
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
                result=result,
                messages=result.get("messages", [])
            )
        except Exception as e:
            logger.error(f"Error running meeting: {e}")
            raise

    def _run_meeting_api(self, query, thread_id, use_premium, provider) -> MeetingResult:
        import requests
        url = f"{self.backend_api_url}/meeting"
        payload = {"query": query, "thread_id": thread_id, "use_premium": use_premium, "provider": provider}
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            return MeetingResult(
                thread_id=data.get("thread_id", thread_id or "unknown"),
                query=query,
                status=data.get("status", "completed"),
                result=data.get("result", {}),
                messages=data.get("history", [])
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"API error: {e}")
            raise Exception(f"Failed to connect to backend API: {e}")

    def get_meeting_history(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.backend_mode == "api":
            import requests
            url = f"{self.backend_api_url}/meeting/{thread_id}"
            response = requests.get(url, params={"limit": limit})
            response.raise_for_status()
            return response.json().get("history", [])
        else:
            backend = self._get_backend()
            return backend.get_meeting_history(thread_id, limit)

    def continue_meeting(self, thread_id: str, query: str, use_premium: bool = False) -> MeetingResult:
        if self.backend_mode == "api":
            import requests
            url = f"{self.backend_api_url}/meeting/continue"
            payload = {"thread_id": thread_id, "query": query, "use_premium": use_premium}
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            return MeetingResult(
                thread_id=thread_id,
                query=query,
                status=data.get("status", "continued"),
                result=data.get("result", {}),
                messages=data.get("history", [])
            )
        else:
            backend = self._get_backend()
            result = backend.continue_meeting(thread_id=thread_id, query=query, use_premium=use_premium)
            return MeetingResult(
                thread_id=thread_id,
                query=query,
                status="continued",
                result=result,
                messages=result.get("messages", [])
            )

    def save_meeting(self, thread_id: str, query: str, result: Dict[str, Any]) -> str:
        from pathlib import Path
        history_dir = Path(__file__).parent / "meeting_history"
        history_dir.mkdir(exist_ok=True)
        filepath = history_dir / f"{thread_id}.json"
        with open(filepath, 'w') as f:
            json.dump({"thread_id": thread_id, "query": query, "timestamp": datetime.now().isoformat(), "result": result}, f, indent=2)
        return str(filepath)

    def list_saved_meetings(self) -> List[Dict[str, Any]]:
        from pathlib import Path
        history_dir = Path(__file__).parent / "meeting_history"
        history_dir.mkdir(exist_ok=True)
        meetings = []
        for filepath in sorted(history_dir.glob("*.json"), reverse=True)[:20]:
            with open(filepath) as f:
                data = json.load(f)
                meetings.append({"thread_id": data.get("thread_id", filepath.stem), "query": data.get("query", ""), "timestamp": data.get("timestamp", ""), "filename": filepath.name})
        return meetings


_client: Optional[BackendClient] = None


def get_backend_client() -> BackendClient:
    global _client
    if _client is None:
        _client = BackendClient()
    return _client


def reset_backend_client() -> None:
    global _client
    _client = None
