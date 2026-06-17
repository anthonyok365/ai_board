"""
Utility functions for the AI Board of Directors backend.

Provides helper functions for formatting output, creating configs,
and common operations used across the application.
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Output Formatting Utilities
# ============================================================================

def format_messages_for_display(messages: list[BaseMessage]) -> str:
    """
    Format a list of messages for human-readable display.
    
    Args:
        messages: List of LangChain messages.
        
    Returns:
        Formatted string representation.
    """
    if not messages:
        return "No messages in conversation."
    
    lines = ["=" * 60, "BOARD MEETING TRANSCRIPT", "=" * 60, ""]
    
    for i, msg in enumerate(messages, 1):
        speaker = getattr(msg, 'name', 'unknown') or 'unknown'
        content = msg.content
        
        # Truncate very long messages for display
        if len(content) > 2000:
            content = content[:2000] + "\n... [truncated]"
        
        lines.append(f"[Message {i}]")
        lines.append(f"Speaker: {speaker.title()}")
        lines.append("-" * 40)
        lines.append(content)
        lines.append("")
    
    lines.append("=" * 60)
    return "\n".join(lines)


def format_board_decision(decision: str) -> str:
    """
    Format a board decision for display with styling.
    
    Args:
        decision: The decision text to format.
        
    Returns:
        Formatted decision string.
    """
    if not decision:
        return "No decision has been made yet."
    
    header = """
╔══════════════════════════════════════════════════════════════════╗
║                    AI BOARD DECISION                            ║
║                    (Official Record)                            ║
╚══════════════════════════════════════════════════════════════════╝
"""
    return f"{header}\n{decision}"


def extract_sections_from_decision(decision: str) -> dict[str, str]:
    """
    Extract sections from a structured board decision.
    
    Args:
        decision: The decision text with markdown sections.
        
    Returns:
        Dictionary mapping section names to their content.
    """
    sections = {}
    
    # Common section headers in board decisions
    section_markers = [
        "EXECUTIVE SUMMARY",
        "KEY RECOMMENDATIONS",
        "ACTION ITEMS",
        "PROJECTED FINANCIAL IMPACT",
        "RISKS & MITIGATIONS",
        "BOARD CONSENSUS",
        "NEXT STEPS",
    ]
    
    lines = decision.split("\n")
    current_section = None
    current_content = []
    
    for line in lines:
        # Check if this line is a section header
        is_header = False
        for marker in section_markers:
            if marker in line.upper():
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = marker
                current_content = []
                is_header = True
                break
        
        if not is_header:
            current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()
    
    return sections


# ============================================================================
# Configuration Utilities
# ============================================================================

def create_graph_config(
    thread_id: str,
    recursion_limit: int = 25,
    metadata: Optional[dict] = None
) -> dict[str, Any]:
    """
    Create a configuration dict for graph invocation.
    
    Args:
        thread_id: Unique identifier for the session.
        recursion_limit: Maximum number of steps in the graph.
        metadata: Optional metadata to attach to the run.
        
    Returns:
        Configuration dictionary for LangGraph.
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": recursion_limit,
    }
    
    if metadata:
        config["metadata"] = metadata
    
    return config


# ============================================================================
# State Utilities
# ============================================================================

def state_to_dict(state: dict) -> dict:
    """
    Convert state to a JSON-serializable dictionary.
    
    Args:
        state: Agent state dictionary.
        
    Returns:
        JSON-serializable dictionary.
    """
    result = {}
    
    for key, value in state.items():
        if key == "messages":
            # Convert messages to serializable format
            result[key] = [
                {
                    "type": type(msg).__name__,
                    "content": msg.content,
                    "name": getattr(msg, 'name', None),
                }
                for msg in value
            ]
        elif key == "meeting_context":
            # Context should already be a dict
            result[key] = value
        elif hasattr(value, 'model_dump'):
            # Pydantic models
            result[key] = value.model_dump()
        else:
            # Primitives and other types
            result[key] = value
    
    return result


def get_conversation_summary(messages: list[BaseMessage]) -> str:
    """
    Generate a brief summary of the conversation.
    
    Args:
        messages: List of conversation messages.
        
    Returns:
        Summary string.
    """
    if not messages:
        return "No conversation yet."
    
    # Count messages by type/name
    speaker_counts = {}
    for msg in messages:
        name = getattr(msg, 'name', 'unknown') or 'unknown'
        speaker_counts[name] = speaker_counts.get(name, 0) + 1
    
    # Format summary
    lines = ["Conversation Summary:"]
    for speaker, count in sorted(speaker_counts.items()):
        lines.append(f"  - {speaker.title()}: {count} message(s)")
    
    return "\n".join(lines)


# ============================================================================
# Logging Utilities
# ============================================================================

def log_board_meeting_start(thread_id: str, query: str) -> None:
    """
    Log the start of a board meeting.
    
    Args:
        thread_id: Session identifier.
        query: The business question being discussed.
    """
    logger.info("=" * 60)
    logger.info("BOARD MEETING STARTED")
    logger.info("=" * 60)
    logger.info(f"Thread ID: {thread_id}")
    logger.info(f"Query: {query}")
    logger.info("=" * 60)


def log_board_meeting_end(thread_id: str, rounds: int, message_count: int) -> None:
    """
    Log the end of a board meeting.
    
    Args:
        thread_id: Session identifier.
        rounds: Number of discussion rounds completed.
        message_count: Total number of messages in the conversation.
    """
    logger.info("=" * 60)
    logger.info("BOARD MEETING CONCLUDED")
    logger.info("=" * 60)
    logger.info(f"Thread ID: {thread_id}")
    logger.info(f"Discussion Rounds: {rounds}")
    logger.info(f"Total Messages: {message_count}")
    logger.info("=" * 60)


def log_error(error: Exception, context: str = "") -> None:
    """
    Log an error with context.
    
    Args:
        error: The exception that occurred.
        context: Additional context about where the error occurred.
    """
    logger.error("=" * 60)
    logger.error("ERROR OCCURRED")
    logger.error("=" * 60)
    logger.error(f"Context: {context}")
    logger.error(f"Error Type: {type(error).__name__}")
    logger.error(f"Error Message: {str(error)}")
    logger.error("=" * 60)


# ============================================================================
# Session Management Utilities
# ============================================================================

def create_thread_id(prefix: str = "meeting") -> str:
    """
    Create a unique thread ID for a new meeting.
    
    Args:
        prefix: Prefix for the thread ID.
        
    Returns:
        Unique thread ID string.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime for display.
    
    Args:
        dt: Datetime to format (defaults to now).
        
    Returns:
        Formatted timestamp string.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_query(query: str) -> tuple[bool, Optional[str]]:
    """
    Validate a board meeting query.
    
    Args:
        query: The query to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."
    
    if len(query) < 10:
        return False, "Query is too short. Please provide more context."
    
    if len(query) > 5000:
        return False, "Query is too long. Please summarize the key question."
    
    return True, None


# ============================================================================
# Export Utilities
# ============================================================================

def export_decision_to_json(decision: str, metadata: Optional[dict] = None) -> str:
    """
    Export a board decision to JSON format.
    
    Args:
        decision: The board decision text.
        metadata: Optional metadata to include.
        
    Returns:
        JSON string representation.
    """
    data = {
        "decision": decision,
        "sections": extract_sections_from_decision(decision),
        "timestamp": format_timestamp(),
    }
    
    if metadata:
        data["metadata"] = metadata
    
    return json.dumps(data, indent=2)


def export_conversation_to_dict(messages: list[BaseMessage]) -> list[dict]:
    """
    Export conversation messages to a list of dictionaries.
    
    Args:
        messages: List of conversation messages.
        
    Returns:
        List of message dictionaries.
    """
    return [
        {
            "type": type(msg).__name__,
            "content": msg.content,
            "name": getattr(msg, 'name', None),
            "timestamp": format_timestamp(),
        }
        for msg in messages
    ]