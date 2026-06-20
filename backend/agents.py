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

# System Prompts
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

SUPERVISOR_SYSTEM_PROMPT = """You are the Board Chair. Route the discussion.

Return ONLY ONE: strategist, financial, risk, ceo, or final_decision

Consider: Have all board members contributed? Is the board ready to decide?"""

# LLM Invocation with Retry
def _invoke_llm(system_prompt: str, state: AgentState, max_retries: int = 3) -> AIMessage:
    """Invoke LLM with retry logic for rate limiting."""
    config_instance = get_config()
    llm = config_instance.get_llm()

    messages = [SystemMessage(content=system_prompt)]

    current_query = state.get("current_query", "")
    if current_query:
        messages.append(HumanMessage(content=current_query))

    recent_messages = list(state["messages"])[-6:]
    for msg in recent_messages:
        if hasattr(msg, 'content'):
            clean_msg = AIMessage(content=msg.content, name=getattr(msg, 'name', None))
            messages.append(clean_msg)

    logger.info(f"Invoking LLM with {len(messages)} messages")

    delay = 5
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            error_str = str(e)
            last_error = error_str
            
            if any(x in error_str for x in ["429", "RESOURCE_EXHAUSTED", "rate", "502", "timeout"]):
                match = re.search(r"retry.*?(\d+\.?\d*)s", error_str.lower())
                if match:
                    delay = float(match.group(1))
                
                logger.warning(f"Rate limited. Retry in {delay}s... ({attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"LLM failed: {type(e).__name__}: {error_str}")
                raise
    
    raise Exception(f"Failed after {max_retries} retries. Last error: {last_error}")

# Agent Nodes
def strategist_node(state: AgentState, config: RunnableConfig) -> AgentState:
    logger.info("Strategist node invoked")
    response = _invoke_llm(STRATEGIST_SYSTEM_PROMPT, state)
    response.name = "strategist"
    new_iterations = dict(state["agent_iterations"])
    new_iterations["strategist"] = new_iterations.get("strategist", 0) + 1
    return {"messages": [response], "agent_iterations": new_iterations}

def financial_node(state: AgentState, config: RunnableConfig) -> AgentState:
    logger.info("Financial node invoked")
    response = _invoke_llm(FINANCIAL_SYSTEM_PROMPT, state)
    response.name = "financial"
    new_iterations = dict(state["agent_iterations"])
    new_iterations["financial"] = new_iterations.get("financial", 0) + 1
    return {"messages": [response], "agent_iterations": new_iterations}

def risk_node(state: AgentState, config: RunnableConfig) -> AgentState:
    logger.info("Risk node invoked")
    response = _invoke_llm(RISK_SYSTEM_PROMPT, state)
    response.name = "risk"
    new_iterations = dict(state["agent_iterations"])
    new_iterations["risk"] = new_iterations.get("risk", 0) + 1
    return {"messages": [response], "agent_iterations": new_iterations}

def ceo_node(state: AgentState, config: RunnableConfig) -> AgentState:
    logger.info("CEO node invoked")
    response = _invoke_llm(CEO_SYSTEM_PROMPT, state)
    response.name = "ceo"
    new_iterations = dict(state["agent_iterations"])
    new_iterations["ceo"] = new_iterations.get("ceo", 0) + 1
    return {"messages": [response], "agent_iterations": new_iterations}

def supervisor_node(state: AgentState, config: RunnableConfig) -> AgentState:
    logger.info("Supervisor node invoked")

    agent_counts = state["agent_iterations"]
    recent_messages = list(state["messages"])[-4:]
    
    summary = f"Rounds: {state['decision_rounds']}
Contributions:
"
    for agent, count in agent_counts.items():
        summary += f"  - {agent}: {count}
"
    summary += "
Recent:
"
    for msg in recent_messages:
        name = getattr(msg, 'name', 'unknown')
        summary += f"  [{name}]: {msg.content[:200]}...
"

    enhanced_prompt = f"""{SUPERVISOR_SYSTEM_PROMPT}

{summary}

Respond with ONLY ONE: strategist, financial, risk, ceo, or final_decision"""

    minimal_state = AgentState(
        messages=[], next="", board_decision=None,
        thread_id=state["thread_id"], current_query=state["current_query"],
        meeting_context=state["meeting_context"], agent_iterations=state["agent_iterations"],
        decision_rounds=state["decision_rounds"],
    )

    response = _invoke_llm(enhanced_prompt, minimal_state)
    response.name = "supervisor"

    response_text = response.content.strip().lower()
    valid_routes = ["strategist", "financial", "risk", "ceo", "final_decision"]
    next_agent = "final_decision"

    for route in valid_routes:
        if route in response_text:
            next_agent = route
            break

    logger.info(f"Supervisor routing to: {next_agent}")
    return {"messages": [response], "next": next_agent}

def final_decision_node(state: AgentState, config: RunnableConfig) -> AgentState:
    logger.info("Final decision node invoked")

    recent_messages = list(state["messages"])[-6:]
    all_input = "

".join([
        f"--- {getattr(msg, 'name', 'unknown').upper()} ---
{msg.content[:1500]}"
        for msg in recent_messages
        if hasattr(msg, 'name') and msg.name != "supervisor"
    ])

    final_prompt = f"""You are the Board Secretary. Compile board input into a structured decision.

ORIGINAL QUERY: {state['current_query']}

BOARD INPUT:
{all_input}

FORMAT:
# EXECUTIVE SUMMARY
[2-3 sentence overview]

# KEY RECOMMENDATIONS
1. [Primary recommendation]
2. [Secondary recommendation]

# ACTION ITEMS
- [Specific action]

# PROJECTED FINANCIAL IMPACT
- Initial Investment: $XXX
- Expected ROI: XX%

# RISKS & MITIGATIONS
| Risk | Mitigation |
|------|------------|
| Risk 1 | Mitigation |

# NEXT STEPS
1. [Immediate next step]

[Board Secretary]"""

    response = _invoke_llm(final_prompt, state)
    response.name = "final_decision"

    return {"messages": [response], "board_decision": response.content, "next": "FINAL"}
