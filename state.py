"""
State management for AI Board of Directors using LangGraph patterns.

Defines the AgentState TypedDict with proper reducers for message accumulation.
Supports thread-based sessions and human-in-the-loop workflows.
"""

from typing import Annotated, Sequence, TypedDict, Optional
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class AgentState(TypedDict):
    """
    Central state definition for the AI Board of Directors graph.
    
    Uses Annotated with add_messages reducer for automatic message accumulation.
    Supports thread-based sessions for persistent conversations.
    
    Attributes:
        messages: List of conversation messages (automatically accumulated).
        next: The next agent to route to ('strategist', 'financial', 'risk', 'ceo', 'final_decision').
        board_decision: Final synthesized decision from the board.
        thread_id: Unique identifier for the conversation thread.
        current_query: The original user query being discussed.
        meeting_context: Additional context gathered during the meeting.
        agent_iterations: Track which agents have spoken to prevent infinite loops.
        decision_rounds: Number of complete board discussion rounds completed.
    """
    
    # Messages are accumulated using the add_messages reducer
    # This allows multiple agents to add messages while preserving history
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Routing decision - which agent should speak next
    next: str
    
    # Final board decision (populated when meeting concludes)
    board_decision: Optional[str]
    
    # Session identifier for thread-based persistence
    thread_id: str
    
    # Original user query
    current_query: str
    
    # Additional context gathered during discussion
    meeting_context: dict
    
    # Track agent participation to ensure balanced discussion
    agent_iterations: dict
    
    # Count of complete discussion rounds
    decision_rounds: int


def create_initial_state(
    query: str,
    thread_id: str = "default"
) -> AgentState:
    """
    Create an initial state for starting a new board meeting.
    
    Args:
        query: The business question or decision to be discussed.
        thread_id: Unique identifier for this meeting session.
        
    Returns:
        AgentState: Initial state with all required fields set.
    """
    return AgentState(
        messages=[],
        next="supervisor",  # Start with supervisor to route appropriately
        board_decision=None,
        thread_id=thread_id,
        current_query=query,
        meeting_context={},
        agent_iterations={
            "strategist": 0,
            "financial": 0,
            "risk": 0,
            "ceo": 0,
        },
        decision_rounds=0,
    )


def add_user_message(state: AgentState, message: str) -> AgentState:
    """
    Add a user message to the state.
    
    Args:
        state: Current agent state.
        message: Message content from the user.
        
    Returns:
        Updated state with the new user message.
    """
    new_message = HumanMessage(content=message)
    return {
        "messages": [new_message],
    }


def get_conversation_history(state: AgentState) -> list[BaseMessage]:
    """
    Extract conversation history from state.
    
    Args:
        state: Current agent state.
        
    Returns:
        List of all messages in the conversation.
    """
    return list(state["messages"])


def format_state_summary(state: AgentState) -> str:
    """
    Create a human-readable summary of the current state.
    
    Args:
        state: Current agent state.
        
    Returns:
        Formatted string summary.
    """
    lines = [
        f"=== Board Meeting State ===",
        f"Thread ID: {state['thread_id']}",
        f"Query: {state['current_query']}",
        f"Current Agent: {state['next']}",
        f"Decision Rounds: {state['decision_rounds']}",
        f"Agent Iterations: {state['agent_iterations']}",
        f"Messages: {len(state['messages'])}",
    ]
    return "\n".join(lines)