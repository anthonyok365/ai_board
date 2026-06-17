"""
Supabase Database Integration for AI Board Backend.

Provides persistent storage for meetings and messages using Supabase (PostgreSQL).
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)


class Database:
    """Database manager for Supabase integration."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Optional[Client] = None
        
        if SUPABASE_AVAILABLE and self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
        else:
            logger.warning("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY")
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.client is not None
    
    def save_meeting(
        self,
        thread_id: str,
        query: str,
        result: Dict[str, Any],
        messages: List[Dict[str, Any]],
        status: str = "completed"
    ) -> bool:
        """Save or update a meeting."""
        if not self.client:
            return False
        
        try:
            data = {
                "thread_id": thread_id,
                "query": query,
                "result": json.dumps(result),
                "messages": json.dumps(messages),
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Try to insert, or update if exists
            existing = self.get_meeting(thread_id)
            if existing:
                self.client.table("meetings").update(data).eq("thread_id", thread_id).execute()
            else:
                data["created_at"] = datetime.utcnow().isoformat()
                self.client.table("meetings").insert(data).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error saving meeting: {e}")
            return False
    
    def get_meeting(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get a meeting by thread_id."""
        if not self.client:
            return None
        
        try:
            response = self.client.table("meetings").select("*").eq("thread_id", thread_id).execute()
            if response.data:
                data = response.data[0]
                return {
                    "thread_id": data["thread_id"],
                    "query": data["query"],
                    "result": json.loads(data["result"]),
                    "messages": json.loads(data["messages"]),
                    "status": data["status"],
                    "created_at": data["created_at"],
                    "updated_at": data.get("updated_at")
                }
            return None
        except Exception as e:
            logger.error(f"Error getting meeting: {e}")
            return None
    
    def get_meeting_history(self, thread_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get meeting messages for history."""
        meeting = self.get_meeting(thread_id)
        if meeting:
            return meeting.get("messages", [])
        return None
    
    def list_meetings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent meetings."""
        if not self.client:
            return []
        
        try:
            response = self.client.table("meetings").select(
                "thread_id", "query", "status", "created_at"
            ).order("created_at", desc=True).limit(limit).execute()
            
            return [
                {
                    "thread_id": m["thread_id"],
                    "query": m["query"],
                    "status": m["status"],
                    "created_at": m["created_at"]
                }
                for m in response.data
            ]
        except Exception as e:
            logger.error(f"Error listing meetings: {e}")
            return []
    
    def delete_meeting(self, thread_id: str) -> bool:
        """Delete a meeting."""
        if not self.client:
            return False
        
        try:
            self.client.table("meetings").delete().eq("thread_id", thread_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting meeting: {e}")
            return False


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db


# SQL Schema for Supabase
SCHEMA_SQL = """
-- Create meetings table in Supabase SQL Editor
CREATE TABLE IF NOT EXISTS meetings (
    id BIGSERIAL PRIMARY KEY,
    thread_id VARCHAR(255) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    result JSONB,
    messages JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (optional)
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

-- Create policy for all users to read/write their own data
CREATE POLICY "Allow all" ON meetings FOR ALL USING (true) WITH CHECK (true);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_meetings_thread_id ON meetings(thread_id);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at DESC);
"""
