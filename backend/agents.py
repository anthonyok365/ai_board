"""
Agent nodes for the AI Board of Directors LangGraph.

Each agent represents a member of the board with specialized expertise:
- Strategist: Growth, innovation, market strategy, competitive advantage.
- Financial: Revenue, costs, ROI, profitability, financial modeling.
- Risk: Risks, compliance, downsides, mitigation, scenario planning.
- CEO: Leadership, synthesis of inputs, final decision-making.

All agents follow LangGraph conventions: receive state, append system prompt,
call LLM, and return updated state with new messages.
"""

import logging
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from config import get_config
from state import AgentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# System Prompts for Each Board Member
# ============================================================================

STRATEGIST_SYSTEM_PROMPT = """You are the Chief Strategy Officer on an AI-powered Board of Directors.

ROLE & EXPERTISE:
- You specialize in growth strategy, market expansion, innovation opportunities
- You analyze competitive advantages and market positioning
- You identify new business opportunities and strategic pivots
- You focus on long-term value creation and sustainable growth

RESPONSE GUIDELINES:
- Be visionary yet grounded in market realities
- Provide specific, actionable strategic recommendations
- Consider market trends, competitor actions, and emerging opportunities
- Balance aggressive growth with prudent risk assessment
- Focus on profitable, scalable business decisions

FORMAT YOUR RESPONSE AS:
1. Strategic Opportunity: [Clear articulation of the strategic option]
2. Market Rationale: [Why this makes sense in current market conditions]
3. Competitive Advantage: [How this creates or enhances competitive moat]
4. Implementation Approach: [Phased approach to execution]
5. Success Metrics: [How we measure success]

Always sign your response with: [Strategic Advisor]
"""

FINANCIAL_SYSTEM_PROMPT = """You are the Chief Financial Officer on an AI-powered Board of Directors.

ROLE & EXPERTISE:
- You specialize in revenue modeling, cost analysis, and financial projections
- You evaluate ROI, payback periods, and financial viability
- You analyze cash flow implications and capital allocation
- You ensure financial prudence and fiscal responsibility

RESPONSE GUIDELINES:
- Provide specific financial projections with assumptions stated
- Calculate ROI, NPV, IRR where applicable
- Identify cost structures and margin implications
- Consider both best-case and worst-case financial scenarios
- Recommend optimal investment levels and timing

FORMAT YOUR RESPONSE AS:
1. Financial Summary: [Top-line financial impact assessment]
2. Investment Analysis: [Capital required, ROI, payback period]
3. Revenue Projections: [Expected revenue impact with timeline]
4. Cost Structure: [One-time vs. ongoing costs, margin impact]
5. Financial Recommendation: [Optimal investment level and rationale]

Always sign your response with: [Financial Advisor]
"""

RISK_SYSTEM_PROMPT = """You are the Chief Risk Officer on an AI-powered Board of Directors.

ROLE & EXPERTISE:
- You specialize in identifying, assessing, and mitigating business risks
- You analyze compliance requirements and regulatory implications
- You evaluate operational, market, and strategic risks
- You develop contingency plans and scenario analyses

RESPONSE GUIDELINES:
- Be thorough in risk identification - leave no stone unturned
- Categorize risks by likelihood and potential impact
- Provide specific mitigation strategies for each identified risk
- Consider regulatory, operational, market, and reputational risks
- Balance risk mitigation with business opportunity

FORMAT YOUR RESPONSE AS:
1. Risk Assessment: [Primary risks identified with severity ratings]
2. Compliance Considerations: [Regulatory or compliance implications]
3. Risk Mitigation Strategies: [Specific actions to reduce risk exposure]
4. Contingency Plans: [What to do if things go wrong]
5. Go/No-Go Recommendation: [Clear recommendation with conditions]

Always sign your response with: [Risk Advisor]
"""

CEO_SYSTEM_PROMPT = """You are the Chief Executive Officer on an AI-powered Board of Directors.

ROLE & EXPERTISE:
- You synthesize all board input into cohesive decisions
- You balance competing priorities and stakeholder interests
- You provide decisive leadership and clear direction
- You focus on execution excellence and organizational capability

RESPONSE GUIDELINES:
- Synthesize the input from all board members thoughtfully
- Make clear, decisive recommendations when possible
- Identify any remaining questions or information gaps
- Consider organizational capacity for execution
- Ensure recommendations align with overall company strategy
- May call for additional discussion from specific advisors if needed

FORMAT YOUR RESPONSE AS:
1. Executive Assessment: [Your synthesis of the board discussion]
2. Key Decision Points: [Critical choices that need to be made]
3. CEO Recommendation: [Your clear recommendation or decision]
4. Execution Requirements: [What it takes to succeed]
5. Next Steps: [Immediate actions and timeline]

Always sign your response with: [Chief Executive Officer]
"""

SUPERVISOR_SYSTEM_PROMPT = """You are the Board Chair on an AI-powered Board of Directors.

ROLE & EXPERTISE:
- You orchestrate productive board discussions
- You ensure all perspectives are heard and considered
- You route discussions to the appropriate board member
- You recognize when the board is ready to make a decision

ROUTING LOGIC:
- If this is the START of discussion, route to "strategist" first
- After strategist speaks, route to "financial" for analysis
- After financial speaks, route to "risk" for risk assessment
- After risk speaks, route to "ceo" for synthesis
- After CEO speaks, evaluate if more rounds needed or route to "final_decision"
- Always ensure balanced discussion before finalizing

RESPONSE FORMAT:
Return ONLY the name of the next agent to speak:
- "strategist" - For strategic growth and market analysis
- "financial" - For financial modeling and ROI analysis  
- "risk" - For risk assessment and mitigation planning
- "ceo" - For executive synthesis and decision-making
- "final_decision" - When the board is ready to conclude

Consider these factors when deciding:
1. Have all board members had a chance to contribute?
2. Has sufficient analysis been done on all dimensions?
3. Are there remaining questions that need exploration?
4. Is the board aligned enough to make a final decision?

Always respond with just the agent name: strategist, financial, risk, ceo, or final_decision"""

# ============================================================================
# Agent Node Functions
# ============================================================================

def _invoke_llm(system_prompt: str, state: AgentState) -> AIMessage:
    """
    Invoke the LLM with the given system prompt and conversation history.
    
    Args:
        system_prompt: The system prompt for the current agent.
        state: Current agent state containing conversation history.
        
    Returns:
        LLM response as an AIMessage.
    """

    # Build the conversation with system prompt and history
    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [SystemMessage(content=system_prompt)]
    
    # Add the current query as a HumanMessage (required for Gemini)
    current_query = state.get("current_query", "")
    if current_query:
        messages.append(HumanMessage(content=current_query))
    # Add conversation history
    messages.extend(list(state["messages"]))

    logger.info(f"Invoking LLM with {len(messages)} messages")
    
    response = llm.invoke(messages)
    return response


def strategist_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Strategist agent node - analyzes growth and strategic opportunities.
    
    Args:
        state: Current agent state.
        config: LangGraph runnable configuration.
        
    Returns:
        Updated state with strategist's analysis added.
    """
    logger.info("Strategist node invoked")
    
    # Create a context-aware prompt that includes the original query
    enhanced_prompt = f"{STRATEGIST_SYSTEM_PROMPT}\n\nThe board is considering the following matter:\n{state['current_query']}"
    
    response = _invoke_llm(enhanced_prompt, state)
    response.name = "strategist"
    
    # Update iterations counter
    new_iterations = dict(state["agent_iterations"])
    new_iterations["strategist"] = new_iterations.get("strategist", 0) + 1
    
    return {
        "messages": [response],
        "agent_iterations": new_iterations,
    }


def financial_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Financial agent node - provides financial analysis and modeling.
    
    Args:
        state: Current agent state.
        config: LangGraph runnable configuration.
        
    Returns:
        Updated state with financial analysis added.
    """
    logger.info("Financial node invoked")
    
    # Include context from previous discussions
    context = ""
    for msg in state["messages"]:
        if msg.name == "strategist":
            context += f"\n\n--- Strategist's Analysis ---\n{msg.content}"
    
    enhanced_prompt = f"{FINANCIAL_SYSTEM_PROMPT}\n\nThe board is considering the following matter:\n{state['current_query']}{context}"
    
    response = _invoke_llm(enhanced_prompt, state)
    response.name = "financial"
    
    # Update iterations counter
    new_iterations = dict(state["agent_iterations"])
    new_iterations["financial"] = new_iterations.get("financial", 0) + 1
    
    return {
        "messages": [response],
        "agent_iterations": new_iterations,
    }


def risk_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Risk agent node - identifies and assesses risks.
    
    Args:
        state: Current agent state.
        config: LangGraph runnable configuration.
        
    Returns:
        Updated state with risk assessment added.
    """
    logger.info("Risk node invoked")
    
    # Include context from previous discussions
    context = ""
    for msg in state["messages"]:
        if hasattr(msg, 'name'):
            context += f"\n\n--- {msg.name.title()}'s Input ---\n{msg.content}"
    
    enhanced_prompt = f"{RISK_SYSTEM_PROMPT}\n\nThe board is considering the following matter:\n{state['current_query']}{context}"
    
    response = _invoke_llm(enhanced_prompt, state)
    response.name = "risk"
    
    # Update iterations counter
    new_iterations = dict(state["agent_iterations"])
    new_iterations["risk"] = new_iterations.get("risk", 0) + 1
    
    return {
        "messages": [response],
        "agent_iterations": new_iterations,
    }


def ceo_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    CEO agent node - synthesizes board input and provides executive decision.
    
    Args:
        state: Current agent state.
        config: LangGraph runnable configuration.
        
    Returns:
        Updated state with CEO's synthesis added.
    """
    logger.info("CEO node invoked")
    
    # Include all previous board input
    context = ""
    for msg in state["messages"]:
        if hasattr(msg, 'name') and msg.name != "supervisor":
            context += f"\n\n--- {msg.name.title()}'s Analysis ---\n{msg.content}"
    
    enhanced_prompt = f"{CEO_SYSTEM_PROMPT}\n\nThe board is considering the following matter:\n{state['current_query']}{context}"
    
    response = _invoke_llm(enhanced_prompt, state)
    response.name = "ceo"
    
    # Update iterations counter
    new_iterations = dict(state["agent_iterations"])
    new_iterations["ceo"] = new_iterations.get("ceo", 0) + 1
    
    return {
        "messages": [response],
        "agent_iterations": new_iterations,
    }


def supervisor_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Supervisor/Board Chair node - routes discussion to appropriate agent.
    
    This is the orchestration node that decides the flow of the board meeting.
    
    Args:
        state: Current agent state.
        config: LangGraph runnable configuration.
        
    Returns:
        Updated state with routing decision.
    """
    logger.info("Supervisor node invoked")
    
    # Include conversation history for routing decision
    context = "\n\n--- Conversation History ---\n"
    for i, msg in enumerate(state["messages"]):
        speaker = getattr(msg, 'name', 'user') or 'user'
        context += f"\n[{i+1}] {speaker}: {msg.content[:500]}..."
    
    # Add iteration context
    iterations = state["agent_iterations"]
    context += f"\n\n--- Agent Iterations ---\n"
    for agent, count in iterations.items():
        context += f"- {agent}: {count} contributions\n"
    
    context += f"\n\n--- Discussion Rounds Completed: {state['decision_rounds']} ---"
    
    enhanced_prompt = f"{SUPERVISOR_SYSTEM_PROMPT}\n{context}"
    
    # Create a minimal state for supervisor to avoid recursion
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
    
    # Parse the routing decision from the response
    routing_decision = response.content.strip().lower()
    
    # Validate and map routing decision
    valid_routes = ["strategist", "financial", "risk", "ceo", "final_decision"]
    next_agent = "final_decision"  # Default fallback
    
    for route in valid_routes:
        if route in routing_decision:
            next_agent = route
            break
    
    logger.info(f"Supervisor routing to: {next_agent}")
    
    return {
        "messages": [response],
        "next": next_agent,
    }


def final_decision_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Final decision node - produces structured board decision summary.
    
    Synthesizes all board input into a comprehensive decision document.
    
    Args:
        state: Current agent state.
        config: LangGraph runnable configuration.
        
    Returns:
        Updated state with final board decision.
    """
    logger.info("Final decision node invoked")
    
    # Compile all board input
    all_input = "\n\n".join([
        f"--- {getattr(msg, 'name', 'unknown').upper()}'s PERSPECTIVE ---\n{msg.content}"
        for msg in state["messages"]
        if hasattr(msg, 'name') and msg.name != "supervisor"
    ])
    
    final_prompt = f"""You are the Board Secretary preparing the final decision document.

Compile all board input into a structured decision summary.

ORIGINAL QUERY:
{state['current_query']}

ALL BOARD INPUT:
{all_input}

FORMAT YOUR FINAL DECISION AS:

# EXECUTIVE SUMMARY
[2-3 sentence overview of the decision]

# KEY RECOMMENDATIONS
1. [Primary recommendation with rationale]
2. [Secondary recommendation]
3. [Supporting recommendation]

# ACTION ITEMS
- [Specific action to take]
- [Timeline for implementation]
- [Owner/accountable party]

# PROJECTED FINANCIAL IMPACT
- Initial Investment: $XXX
- Expected ROI: XX%
- Payback Period: X months
- Year 1 Revenue Impact: $XXX

# RISKS & MITIGATIONS
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Risk 1 | High/Med/Low | High/Med/Low | Mitigation strategy |
| Risk 2 | ... | ... | ... |

# BOARD CONSENSUS
[Assessment of board alignment and any dissenting views]

# NEXT STEPS
1. [Immediate next step]
2. [Follow-up required]
3. [Review checkpoint]

This document represents the official position of the AI Board of Directors.

[Board Secretary]"""

    response = _invoke_llm(final_prompt, state)
    response.name = "final_decision"
    
    return {
        "messages": [response],
        "board_decision": response.content,
        "next": "FINAL",  # Signal that the meeting is concluded
    }