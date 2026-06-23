"""
LangGraph StateGraph for AI Board of Directors - Authentic Board Meeting.

Implements a real board meeting structure:
- Phase 1: Opening Statements (each agent makes their case)
- Phase 2: Cross-Examination (agents challenge each other)
- Phase 3: Devil's Advocate (challenges everything)
- Phase 4: CEO Final Decision (hard trade-offs)
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from state import AgentState
from agents import (
    supervisor_node,
    strategist_opening,
    financial_opening,
    risk_opening,
    strategist_cross_exam,
    financial_cross_exam,
    risk_cross_exam,
    devils_advocate,
    ceo_deliberation,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

MAX_RECURSION_LIMIT = 20

# Node names
NODE_SUPERVISOR = "supervisor"

# Phase 1: Opening Statements
NODE_STRATEGIST_OPENING = "strategist_opening"
NODE_FINANCIAL_OPENING = "financial_opening"
NODE_RISK_OPENING = "risk_opening"

# Phase 2: Cross-Examination
NODE_STRATEGIST_CROSS = "strategist_cross"
NODE_FINANCIAL_CROSS = "financial_cross"
NODE_RISK_CROSS = "risk_cross"

# Phase 3: Devil's Advocate
NODE_DEVILS_ADVOCATE = "devils_advocate"

# Phase 4: CEO Decision
NODE_CEO_DECISION = "ceo_decision"

# All nodes
ALL_NODES = [
    NODE_SUPERVISOR,
    NODE_STRATEGIST_OPENING, NODE_FINANCIAL_OPENING, NODE_RISK_OPENING,
    NODE_STRATEGIST_CROSS, NODE_FINANCIAL_CROSS, NODE_RISK_CROSS,
    NODE_DEVILS_ADVOCATE,
    NODE_CEO_DECISION,
]

# ============================================================================
# Routing Logic
# ============================================================================

def route_next(state: AgentState) -> str:
    """Route to the next phase based on what has completed."""
    iterations = state.get("agent_iterations", {})
    
    # Check which phases completed
    if iterations.get(NODE_STRATEGIST_OPENING, 0) == 0:
        return NODE_STRATEGIST_OPENING
    elif iterations.get(NODE_FINANCIAL_OPENING, 0) == 0:
        return NODE_FINANCIAL_OPENING
    elif iterations.get(NODE_RISK_OPENING, 0) == 0:
        return NODE_RISK_OPENING
    elif iterations.get(NODE_STRATEGIST_CROSS, 0) == 0:
        return NODE_STRATEGIST_CROSS
    elif iterations.get(NODE_FINANCIAL_CROSS, 0) == 0:
        return NODE_FINANCIAL_CROSS
    elif iterations.get(NODE_RISK_CROSS, 0) == 0:
        return NODE_RISK_CROSS
    elif iterations.get(NODE_DEVILS_ADVOCATE, 0) == 0:
        return NODE_DEVILS_ADVOCATE
    elif iterations.get(NODE_CEO_DECISION, 0) == 0:
        return NODE_CEO_DECISION
    else:
        return "FINAL"


# ============================================================================
# Graph Construction
# ============================================================================

def create_board_graph() -> StateGraph:
    """Create the authentic board meeting graph."""
    logger.info("Creating Auth Board Meeting graph")
    
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node(NODE_SUPERVISOR, supervisor_node)
    
    # Phase 1: Opening Statements
    workflow.add_node(NODE_STRATEGIST_OPENING, strategist_opening)
    workflow.add_node(NODE_FINANCIAL_OPENING, financial_opening)
    workflow.add_node(NODE_RISK_OPENING, risk_opening)
    
    # Phase 2: Cross-Examination
    workflow.add_node(NODE_STRATEGIST_CROSS, strategist_cross_exam)
    workflow.add_node(NODE_FINANCIAL_CROSS, financial_cross_exam)
    workflow.add_node(NODE_RISK_CROSS, risk_cross_exam)
    
    # Phase 3: Devil's Advocate
    workflow.add_node(NODE_DEVILS_ADVOCATE, devils_advocate)
    
    # Phase 4: CEO Decision
    workflow.add_node(NODE_CEO_DECISION, ceo_deliberation)
    
    # Entry point
    workflow.set_entry_point(NODE_SUPERVISOR)
    
    # Routing from supervisor to all nodes
    workflow.add_conditional_edges(
        NODE_SUPERVISOR,
        route_next,
        {
            NODE_STRATEGIST_OPENING: NODE_STRATEGIST_OPENING,
            NODE_FINANCIAL_OPENING: NODE_FINANCIAL_OPENING,
            NODE_RISK_OPENING: NODE_RISK_OPENING,
            NODE_STRATEGIST_CROSS: NODE_STRATEGIST_CROSS,
            NODE_FINANCIAL_CROSS: NODE_FINANCIAL_CROSS,
            NODE_RISK_CROSS: NODE_RISK_CROSS,
            NODE_DEVILS_ADVOCATE: NODE_DEVILS_ADVOCATE,
            NODE_CEO_DECISION: NODE_CEO_DECISION,
        }
    )
    
    # All nodes return to supervisor
    workflow.add_edge(NODE_STRATEGIST_OPENING, NODE_SUPERVISOR)
    workflow.add_edge(NODE_FINANCIAL_OPENING, NODE_SUPERVISOR)
    workflow.add_edge(NODE_RISK_OPENING, NODE_SUPERVISOR)
    workflow.add_edge(NODE_STRATEGIST_CROSS, NODE_SUPERVISOR)
    workflow.add_edge(NODE_FINANCIAL_CROSS, NODE_SUPERVISOR)
    workflow.add_edge(NODE_RISK_CROSS, NODE_SUPERVISOR)
    workflow.add_edge(NODE_DEVILS_ADVOCATE, NODE_SUPERVISOR)
    workflow.add_edge(NODE_CEO_DECISION, END)
    
    logger.info("Auth Board Meeting graph defined")
    
    return workflow


def compile_graph():
    """Compile the graph with MemorySaver."""
    logger.info("Compiling Auth Board Meeting graph")
    
    workflow = create_board_graph()
    checkpointer = MemorySaver()
    
    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[],
    )
    
    logger.info("Auth Board Meeting compiled successfully")
    
    return compiled


# ============================================================================
# Singleton instance
# ============================================================================

_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_graph()
    return _compiled_graph


def create_graph_config(thread_id: str = None, recursion_limit: int = MAX_RECURSION_LIMIT) -> dict:
    """Create a graph configuration dict."""
    return {
        "configurable": {
            "thread_id": thread_id or "default",
            "recursion_limit": recursion_limit,
        }
    }
