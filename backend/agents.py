"""
Agent nodes for the AI Board of Directors LangGraph.
"""
import logging
import time
import re
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from config import get_config
from state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# System Prompts (Shortened for better context management)
# ============================================================================
STRATEGIST_SYSTEM_PROMPT = """You are the Chief Strategy Officer. Focus on growth, market expansion, competitive advantage.
FORMAT:
1. Strategic Opportunity: [Clear articulation]
2. Market Rationale: [Why this makes sense]
3. Competitive Advantage: [How this creates moat]
4. Implementation Approach: [Phased execution]
5. Success Metrics: [How we measure success]
Sign with: [Strategic Advisor]"""

FINANCIAL_SYSTEM_PROMPT = """You are the Chief Financial Officer. Focus on revenue modeling, ROI, financial viability.
FORMAT:
1. Financial Summary: [Top-line assessment]
2. Investment Analysis: [Capital, ROI, payback]
3. Revenue Projections: [Expected impact]
4. Cost Structure: [One-time vs ongoing]
5. Financial Recommendation: [Optimal investment]
Sign with: [Financial Advisor]"""

RISK_SYSTEM_PROMPT = """You are the Chief Risk Officer. Focus on identifying and mitigating risks.
FORMAT:
1. Risk Assessment: [Primary risks]
2. Compliance Considerations: [Regulatory implications]
3. Risk Mitigation Strategies: [Specific actions]
4. Contingency Plans: [What if things go wrong]
5. Go/No-Go Recommendation: [Clear recommendation]
Sign with: [Risk Advisor]"""

CEO_SYSTEM_PROMPT = """You are the Chief Executive Officer. Synthesize board input into decisions.
FORMAT:
1. Executive Assessment: [Your synthesis]
2. Key Decision Points: [Critical choices]
3. CEO Recommendation: [Your recommendation]
4. Execution Requirements: [What it takes]
5. Next Steps: [Immediate actions]
Sign with: [Chief Executive Officer]"""

SUPERVISOR_SYSTEM_PROMPT = """You are the Board Chair. Your ONLY job is to decide who speaks next.
Respond with EXACTLY ONE of these words and nothing else:

strategist
financial
risk
ceo
final_decision

Do not add any explanation."""


# ============================================================================
# Core LLM Invocation (Fixed)
# ============================================================================
def _invoke_llm(system_prompt: str, state: AgentState, max_retries: int = 3):
    config_instance = get_config()
    llm = config_instance.get_llm()
    
    messages = [SystemMessage(content=system_prompt)]
    
    if state.get("current_query"):
        messages.append(HumanMessage(content=state["current_query"]))
    
    # Add only recent messages to prevent context explosion
    recent_messages = list(state["messages"])[-8:]
    for msg in recent_messages:
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            content = content[0] if content else ""
        if content and str(content).strip():
            # Use plain AIMessage without .name for better Gemini/Groq compatibility
            messages.append(AIMessage(content=str(content)))
    
    logger.info(f"Invoking LLM with {len(messages)} messages | Provider: {type(llm).__name__}")
    
    for attempt in range(max_retries):
        try:
            result = llm.invoke(messages)
            
            # Ensure we always return a single AIMessage
            if isinstance(result, list):
                result = result[0] if result else AIMessage(content="")
            
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {type(e).__name__}")
            
            if any(err in error_str for err in ["502", "503", "timeout", "overloaded", "resource_exhausted", "429"]):
                sleep_time = 2 ** attempt * 3
                logger.info(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                continue
            else:
                logger.error(f"Non-retryable error: {str(e)}")
                raise
    
    raise Exception(f"LLM call failed after {max_retries} retries")


# ============================================================================
# Agent Nodes
# ============================================================================
def strategist_node(state: AgentState, config: RunnableConfig):
    logger.info("Strategist node invoked")
    response = _invoke_llm(STRATEGIST_SYSTEM_PROMPT, state)
    response.name = "strategist"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["strategist"] = new_iterations.get("strategist", 0) + 1
    
    return {"messages": [response], "agent_iterations": new_iterations}


def financial_node(state: AgentState, config: RunnableConfig):
    logger.info("Financial node invoked")
    response = _invoke_llm(FINANCIAL_SYSTEM_PROMPT, state)
    response.name = "financial"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["financial"] = new_iterations.get("financial", 0) + 1
    
    return {"messages": [response], "agent_iterations": new_iterations}


def risk_node(state: AgentState, config: RunnableConfig):
    logger.info("Risk node invoked")
    response = _invoke_llm(RISK_SYSTEM_PROMPT, state)
    response.name = "risk"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["risk"] = new_iterations.get("risk", 0) + 1
    
    return {"messages": [response], "agent_iterations": new_iterations}


def ceo_node(state: AgentState, config: RunnableConfig):
    logger.info("CEO node invoked")
    response = _invoke_llm(CEO_SYSTEM_PROMPT, state)
    response.name = "ceo"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["ceo"] = new_iterations.get("ceo", 0) + 1
    
    return {"messages": [response], "agent_iterations": new_iterations}


def supervisor_node(state: AgentState, config: RunnableConfig):
    logger.info("Supervisor node invoked")
    
    agent_counts = state["agent_iterations"]
    recent_messages = list(state["messages"])[-4:]
    
    summary = f"Rounds: {state['decision_rounds']}\nContributions:\n"
    for agent, count in agent_counts.items():
        summary += f" - {agent}: {count}\n"
    
    summary += "\nRecent:\n"
    for msg in recent_messages:
        name = getattr(msg, "name", "unknown")
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            content = content[0] if content else ""
        summary += f" [{name}]: {str(content)[:250]}...\n"
    
    enhanced_prompt = SUPERVISOR_SYSTEM_PROMPT + "\n\nCurrent State:\n" + summary
    
    minimal_state = AgentState(
        messages=[],
        next="",
        board_decision=None,
        thread_id=state["thread_id"],
        current_query=state["current_query"],
        meeting_context=state["meeting_context"],
        agent_iterations=state["agent_iterations"],
        decision_rounds=state["decision_rounds"],
    )
    
    response = _invoke_llm(enhanced_prompt, minimal_state)
    response.name = "supervisor"
    
    # === FIXED: Safe content extraction ===
    content = getattr(response, 'content', '')
    if isinstance(content, list):
        content = content[0] if content else ''
    
    response_text = str(content).strip().lower()
    
    valid_routes = ["strategist", "financial", "risk", "ceo", "final_decision"]
    next_agent = "final_decision"  # safe default
    
    for route in valid_routes:
        if route in response_text:
            next_agent = route
            break
    
    logger.info(f"Supervisor routing to: {next_agent}")
    return {"messages": [response], "next": next_agent}


def final_decision_node(state: AgentState, config: RunnableConfig):
    logger.info("Final decision node invoked")
    
    recent_messages = list(state["messages"])[-8:]
    all_input = "\n\n".join([
        f"--- {getattr(msg, 'name', 'unknown').upper()} ---\n{str(getattr(msg, 'content', '') or '')[:1200]}"
        for msg in recent_messages
        if getattr(msg, 'name', None) not in [None, "supervisor"]
    ])
    
    final_prompt = f"""You are the Board Secretary. Compile all input into a clear decision document.

ORIGINAL QUERY: {state['current_query']}

BOARD INPUT:
{all_input}

FORMAT EXACTLY LIKE THIS:
# EXECUTIVE SUMMARY
[2-3 sentence overview]

# KEY RECOMMENDATIONS
1. ...
2. ...

# ACTION ITEMS
- ...

# PROJECTED FINANCIAL IMPACT
- Initial Investment: $XXX
- Expected ROI: XX%

# RISKS & MITIGATIONS
| Risk | Mitigation |
|------|------------|

# NEXT STEPS
1. ...

[Board Secretary]"""
    
    response = _invoke_llm(final_prompt, state)
    response.name = "final_decision"
    
    # Handle list content from LLM
    board_decision = getattr(response, 'content', '')
    if isinstance(board_decision, list):
        board_decision = board_decision[0] if board_decision else ''
    
    return {
        "messages": [response],
        "board_decision": str(board_decision) if board_decision else '',
        "next": "FINAL"
    }
