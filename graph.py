"""
LangGraph StateGraph for AI Board of Directors.

Implements a production-grade multi-agent system with:
- Conditional routing based on supervisor decisions
- Cycle management (Strategist → Financial → Risk → CEO → back if needed)
- MemorySaver for persistence and checkpointing
- Thread-based session support
- Recursion limit handling and graceful error recovery
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.errors import GraphRecursionError

from state import AgentState, create_initial_state
from agents import (
    strategist_node,
    financial_node,
    risk_node,
    ceo_node,
    supervisor_node,
    final_decision_node,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

# Maximum recursion depth to prevent infinite loops
MAX_RECURSION_LIMIT = 25

# Node names
NODE_SUPERVISOR = "supervisor"
NODE_STRATEGIST = "strategist"
NODE_FINANCIAL = "financial"
NODE_RISK = "risk"
NODE_CEO = "ceo"
NODE_FINAL_DECISION = "final_decision"

# Routing targets
ROUTING_TARGETS = [NODE_STRATEGIST, NODE_FINANCIAL, NODE_RISK, NODE_CEO, NODE_FINAL_DECISION]

# ============================================================================
# Conditional Edge Functions
# ============================================================================

def route_decision(state: AgentState) -> Literal[
    NODE_STRATEGIST, NODE_FINANCIAL, NODE_RISK, NODE_CEO, NODE_FINAL_DECISION, "__end__"
]:
    """
    Route to the next node based on supervisor's decision.
    
    This function implements the core routing logic for the board meeting.
    It uses the 'next' field set by the supervisor to determine which
    agent should speak next.
    
    Args:
        state: Current agent state.
        
    Returns:
        The name of the next node to invoke.
    """
    next_agent = state.get("next", NODE_FINAL_DECISION).lower().strip()
    
    # Validate routing decision
    if next_agent not in ROUTING_TARGETS:
        logger.warning(f"Invalid routing decision: '{next_agent}', defaulting to final_decision")
        next_agent = NODE_FINAL_DECISION
    
    # Special handling for final decision
    if next_agent == NODE_FINAL_DECISION or next_agent == "FINAL":
        logger.info("Board meeting concluded, routing to final decision")
        return NODE_FINAL_DECISION
    
    # Check for recursion limit to prevent infinite loops
    current_round = state.get("decision_rounds", 0)
    if current_round >= MAX_RECURSION_LIMIT // 4:  # Allow ~6 full rounds
        logger.info("Max rounds reached, concluding meeting")
        return NODE_FINAL_DECISION
    
    logger.info(f"Routing to: {next_agent}")
    return next_agent


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    Determine if the board meeting should continue or end.
    
    Args:
        state: Current agent state.
        
    Returns:
        "continue" if meeting should proceed, "end" if concluded.
    """
    next_agent = state.get("next", "")
    
    if next_agent == "FINAL" or next_agent == "__end__":
        return "end"
    
    return "continue"


# ============================================================================
# Graph Construction
# ============================================================================

def create_board_graph() -> StateGraph:
    """
    Create and configure the AI Board of Directors StateGraph.
    
    The graph structure follows a supervisor pattern where:
    1. Supervisor analyzes state and decides routing
    2. Selected agent provides their perspective
    3. Loop continues until supervisor routes to final_decision
    
    Returns:
        Configured StateGraph ready for compilation.
    """
    logger.info("Creating AI Board of Directors graph")
    
    # Define the graph with our state schema
    workflow = StateGraph(AgentState)
    
    # ========================================================================
    # Add All Agent Nodes
    # ========================================================================
    
    # Supervisor/Board Chair - orchestrates the meeting
    workflow.add_node(NODE_SUPERVISOR, supervisor_node)
    
    # Individual board members
    workflow.add_node(NODE_STRATEGIST, strategist_node)
    workflow.add_node(NODE_FINANCIAL, financial_node)
    workflow.add_node(NODE_RISK, risk_node)
    workflow.add_node(NODE_CEO, ceo_node)
    
    # Final decision synthesis
    workflow.add_node(NODE_FINAL_DECISION, final_decision_node)
    
    # ========================================================================
    # Define Entry Point
    # ========================================================================
    
    workflow.set_entry_point(NODE_SUPERVISOR)
    
    # ========================================================================
    # Add Edges Between Nodes
    # ========================================================================
    
    # From supervisor, route to appropriate agent
    workflow.add_conditional_edges(
        NODE_SUPERVISOR,
        route_decision,
        {
            NODE_STRATEGIST: NODE_STRATEGIST,
            NODE_FINANCIAL: NODE_FINANCIAL,
            NODE_RISK: NODE_RISK,
            NODE_CEO: NODE_CEO,
            NODE_FINAL_DECISION: NODE_FINAL_DECISION,
        }
    )
    
    # After each agent speaks, return to supervisor for routing
    workflow.add_edge(NODE_STRATEGIST, NODE_SUPERVISOR)
    workflow.add_edge(NODE_FINANCIAL, NODE_SUPERVISOR)
    workflow.add_edge(NODE_RISK, NODE_SUPERVISOR)
    workflow.add_edge(NODE_CEO, NODE_SUPERVISOR)
    
    # Final decision ends the meeting
    workflow.add_edge(NODE_FINAL_DECISION, END)
    
    logger.info("Graph structure defined successfully")
    
    return workflow


def compile_graph():
    """
    Compile the StateGraph with MemorySaver checkpointer.
    
    The checkpointer enables:
    - Thread-based session persistence
    - Resume from any checkpoint
    - Audit trail of conversations
    
    Returns:
        Compiled LangGraph application ready for invocation.
    """
    logger.info("Compiling graph with MemorySaver checkpointer")
    
    # Create the workflow
    workflow = create_board_graph()
    
    # Compile with memory checkpointer for persistence
    checkpointer = MemorySaver()
    
    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],  # Could add nodes for human-in-the-loop
        interrupt_after=[],   # Could add nodes for human approval
    )
    
    logger.info("Graph compiled successfully")
    
    return compiled


# ============================================================================
# Pre-built Graph Instance
# ============================================================================

# Singleton compiled graph instance
_compiled_graph = None


def get_graph():
    """
    Get the compiled graph instance (singleton pattern).
    
    Returns:
        Compiled LangGraph application.
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_graph()
    return _compiled_graph


def reset_graph() -> None:
    """Reset the compiled graph instance (useful for testing)."""
    global _compiled_graph
    _compiled_graph = None


# ============================================================================
# Utility Functions
# ============================================================================

def get_checkpointer():
    """
    Get a new MemorySaver checkpointer instance.
    
    Useful when you need separate checkpointer instances
    for different graph instances.
    
    Returns:
        New MemorySaver instance.
    """
    return MemorySaver()


def visualize_graph() -> str:
    """
    Generate a text representation of the graph structure.
    
    Returns:
        String describing the graph structure.
    """
    structure = """
AI BOARD OF DIRECTORS - GRAPH STRUCTURE
========================================

Entry Point: supervisor

Flow:
    ┌─────────────────────────────────────────────────────────────┐
    │                         supervisor                          │
    │                   (Board Chair - routing)                   │
    └─────────┬───────────┬───────────┬───────────┬──────────────┘
              │           │           │           │
              ▼           ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
        │strategist│ │financial │ │   risk   │ │   ceo    │
        │(Strategy)│ │(Finance) │ │  (Risk)  │ │(CEO/Exec)│
        └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │            │
             └────────────┴────────────┴────────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │final_decision │
                     │(Board Summary)│
                     └───────┬───────┘
                             │
                             ▼
                            END

Notes:
- After any agent speaks, control returns to supervisor
- Supervisor decides whether to continue discussion or conclude
- final_decision produces the structured board decision
- MemorySaver enables thread-based session persistence
"""
    return structure