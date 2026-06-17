"""
Main entry point for the AI Board of Directors Backend.

Provides the primary interface for running board meetings and
managing the LangGraph application.

Usage:
    from main import run_board_meeting
    
    result = run_board_meeting(
        query="Should we invest $800k in expanding our AI product line?",
        thread_id="meeting_20260101_120000"
    )
"""

import logging
from typing import Optional, Generator, Any
from langchain_core.messages import HumanMessage
from langgraph.errors import GraphRecursionError

from state import AgentState, create_initial_state
from graph import get_graph, visualize_graph, MAX_RECURSION_LIMIT, create_graph_config
from utils import (
    format_board_decision,
    format_messages_for_display,
    log_board_meeting_start,
    log_board_meeting_end,
    log_error,
    validate_query,
    create_thread_id,
    extract_sections_from_decision,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Main Board Meeting Function
# ============================================================================

def run_board_meeting(
    query: str,
    thread_id: Optional[str] = None,
    use_premium: bool = False,
    stream: bool = False,
    recursion_limit: int = MAX_RECURSION_LIMIT,
) -> dict[str, Any]:
    """
    Run a complete AI Board of Directors meeting.
    
    This is the primary interface for conducting a board meeting.
    The meeting follows this flow:
    1. Supervisor analyzes the query and routes to strategist
    2. Strategist provides growth/strategy perspective
    3. Financial analyst provides financial modeling
    4. Risk officer identifies and assesses risks
    5. CEO synthesizes all input and makes recommendations
    6. Supervisor may route for additional rounds if needed
    7. Final decision is produced with structured recommendations
    
    Args:
        query: The business question or decision to be discussed.
               Examples:
               - "Should we invest $800k in expanding our AI product line?"
               - "Should we enter the European market next year?"
               - "What's our strategy for competing with new market entrants?"
        thread_id: Unique identifier for this meeting session.
                  If None, a timestamped ID will be generated.
        use_premium: If True, use stronger (but more expensive) LLM models.
        stream: If True, return a generator for streaming responses.
        recursion_limit: Maximum number of steps in the graph.
                        Defaults to MAX_RECURSION_LIMIT.
        
    Returns:
        Dictionary containing:
        - 'success': Boolean indicating if meeting completed successfully
        - 'thread_id': The session thread ID
        - 'messages': List of all messages in the conversation
        - 'decision': The final board decision (if meeting completed)
        - 'error': Error message if meeting failed
        - 'rounds': Number of discussion rounds completed
        
    Raises:
        ValueError: If the query is invalid.
    """
    # Validate query
    is_valid, error_msg = validate_query(query)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Generate thread ID if not provided
    if thread_id is None:
        thread_id = create_thread_id("meeting")
    
    # Log meeting start
    log_board_meeting_start(thread_id, query)
    
    try:
        # Get the compiled graph
        graph = get_graph()
        
        # Create initial state
        initial_state = create_initial_state(query=query, thread_id=thread_id)
        
        # Create graph config
        config = create_graph_config(
            thread_id=thread_id,
            recursion_limit=recursion_limit,
        )
        
        # Run the graph
        logger.info(f"Invoking graph with thread_id: {thread_id}")
        
        if stream:
            # Return a generator for streaming
            return _stream_meeting(graph, initial_state, config, thread_id)
        else:
            # Run synchronously and return final result
            return _run_sync_meeting(graph, initial_state, config, thread_id)
    
    except GraphRecursionError as e:
        logger.warning(f"Recursion limit reached: {e}")
        log_error(e, "Graph recursion limit")
        return {
            "success": False,
            "thread_id": thread_id,
            "messages": [],
            "decision": None,
            "error": f"Meeting exceeded maximum rounds ({recursion_limit}). "
                    "The discussion may need to be simplified.",
            "rounds": 0,
        }
    
    except Exception as e:
        logger.error(f"Error during board meeting: {e}")
        log_error(e, "Board meeting execution")
        return {
            "success": False,
            "thread_id": thread_id,
            "messages": [],
            "decision": None,
            "error": f"An error occurred: {str(e)}",
            "rounds": 0,
        }


def _run_sync_meeting(
    graph,
    initial_state: AgentState,
    config: dict,
    thread_id: str,
) -> dict[str, Any]:
    """
    Run the board meeting synchronously.
    
    Args:
        graph: Compiled LangGraph instance.
        initial_state: Initial state for the meeting.
        config: Graph configuration.
        thread_id: Session identifier.
        
    Returns:
        Result dictionary.
    """
    # Invoke the graph
    result = graph.invoke(initial_state, config=config)
    
    # Extract results
    messages = list(result.get("messages", []))
    decision = result.get("board_decision")
    rounds = result.get("decision_rounds", 0)
    
    # Log meeting end
    log_board_meeting_end(thread_id, rounds, len(messages))
    
    return {
        "success": True,
        "thread_id": thread_id,
        "messages": messages,
        "decision": decision,
        "error": None,
        "rounds": rounds,
    }


def _stream_meeting(
    graph,
    initial_state: AgentState,
    config: dict,
    thread_id: str,
) -> Generator[dict, None, None]:
    """
    Stream the board meeting responses.
    
    Args:
        graph: Compiled LangGraph instance.
        initial_state: Initial state for the meeting.
        config: Graph configuration.
        thread_id: Session identifier.
        
    Yields:
        Partial results as the meeting progresses.
    """
    # This is a simplified streaming implementation
    # Full streaming would require async/await and stream output modes
    result = graph.invoke(initial_state, config=config)
    yield result


# ============================================================================
# Convenience Functions
# ============================================================================

def continue_meeting(
    thread_id: str,
    additional_query: str,
    recursion_limit: int = MAX_RECURSION_LIMIT,
) -> dict[str, Any]:
    """
    Continue an existing board meeting with additional input.
    """
    graph = get_graph()
    config = create_graph_config(thread_id=thread_id, recursion_limit=recursion_limit)

    try:
        existing_state = graph.get_state(config)
        
        if not existing_state or not existing_state.values.get("messages"):
            raise ValueError(f"No meeting found with thread_id: {thread_id}")

        graph.update_state(
            config,
            {"messages": [HumanMessage(content=additional_query)]},
        )

        result = graph.invoke(None, config=config)

        return {
            "success": True,
            "thread_id": thread_id,
            "messages": list(result.get("messages", [])),
            "decision": result.get("board_decision"),
            "error": None,
            "rounds": result.get("decision_rounds", 0),
        }

    except Exception as e:
        logger.error(f"Error continuing meeting: {e}")
        return {
            "success": False,
            "thread_id": thread_id,
            "messages": [],
            "decision": None,
            "error": str(e),
            "rounds": 0,
        }


def get_meeting_history(thread_id: str) -> Optional[dict]:
    """
    Retrieve the history of an existing meeting.
    """
    graph = get_graph()
    config = create_graph_config(thread_id=thread_id)

    try:
        state = graph.get_state(config)
        return state.values if state else None
    except Exception:
        return None


def list_active_meetings() -> list[str]:
    """
    List all active meeting thread IDs.
    
    Note: This requires access to the checkpointer's internal storage.
    For production use, consider implementing a proper session store.
    
    Returns:
        List of thread IDs.
    """
    # This is a placeholder - actual implementation depends on checkpointer
    # For MemorySaver, you would need to access its internal dict
    return []


# ============================================================================
# Example Usage and Testing
# ============================================================================

def run_example_meeting():
    """
    Run an example board meeting with a sample query.
    
    This demonstrates the complete flow of the AI Board of Directors.
    """
    print("\n" + "=" * 70)
    print("AI BOARD OF DIRECTORS - EXAMPLE MEETING")
    print("=" * 70 + "\n")
    
    # Sample query
    sample_query = "Should we invest $800k in expanding our AI product line next quarter?"
    
    print(f"QUERY: {sample_query}\n")
    print("-" * 70)
    print("Running board meeting...")
    print("-" * 70 + "\n")
    
    # Run the meeting
    result = run_board_meeting(
        query=sample_query,
        thread_id="example_meeting",
    )
    
    # Display results
    if result["success"]:
        print("\n" + "=" * 70)
        print("MEETING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nThread ID: {result['thread_id']}")
        print(f"Discussion Rounds: {result['rounds']}")
        print(f"Total Messages: {len(result['messages'])}")
        
        if result["decision"]:
            print("\n" + format_board_decision(result["decision"]))
        else:
            print("\nNo final decision was recorded.")
        
        # Show conversation transcript
        print("\n" + "-" * 70)
        print("FULL CONVERSATION TRANSCRIPT")
        print("-" * 70)
        print(format_messages_for_display(result["messages"]))
    else:
        print("\n" + "=" * 70)
        print("MEETING FAILED")
        print("=" * 70)
        print(f"\nError: {result['error']}")
    
    return result


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run example meeting when script is executed directly
    run_example_meeting()