"""
Agent nodes for the AI Board of Directors - Authentic Board Meeting Structure.
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
# PHASE 1: Opening Statements - Each agent makes their case
# ============================================================================
STRATEGIST_OPENING_PROMPT = """You are the Chief Strategy Officer on the board.

ORIGINAL QUESTION: {query}

Your job is to make a STRONG opening argument FOR a specific course of action.

Think like a real strategist who wants to win the room. What's the opportunity? Why now? What are competitors doing? What's the untapped angle?

Be CONVINCING but honest. Don't just list pros - make an argument.

FORMAT YOUR OPENING:
**Strategic Opening:**
[Make your strongest case here. 3-5 sentences that would make someone say "I hadn't thought of that"]

**The Unfair Advantage:**
[What makes this opportunity uniquely timed or positioned?]

**What Could Go Wrong:**
[One honest concern about your own argument]

Sign with: [Strategic Advisor]"""

FINANCIAL_OPENING_PROMPT = """You are the Chief Financial Officer on the board.

ORIGINAL QUESTION: {query}

Your job is to challenge the FINANCIAL REALITY of any proposed action.

Think like a CFO who's seen 100 business plans fail. Where does the money actually come from? What are the hidden costs? When does this become profitable?

Be TOUGH but fair. Question assumptions, not people.

FORMAT YOUR OPENING:
**Financial Reality Check:**
[What nobody is saying about the money. 3-5 sentences that make people uncomfortable]

**The Hidden Costs:**
[What's NOT in the pitch deck?]

**What Would Make You Say Yes:**
[One financial metric or condition that would change your mind]

Sign with: [Financial Advisor]"""

RISK_OPENING_PROMPT = """You are the Chief Risk Officer on the board.

ORIGINAL QUESTION: {query}

Your job is to identify what could DESTROY this opportunity, not kill it.

Think like someone paid to be paranoid. What are the worst-case scenarios? What are competitors, regulators, or the market waiting to do? What happens in 6 months when the novelty wears off?

Be SOBER but constructive. Risk ≠ don't do it. Risk = be prepared.

FORMAT YOUR OPENING:
**The Kill Scenarios:**
[2-3 specific events that would make this fail completely]

**The Silent Threats:**
[What nobody is worried about but should be]

**The Survival Conditions:**
[What must be true for this to work despite the risks]

Sign with: [Risk Advisor]"""

# ============================================================================
# PHASE 2: Cross-Examination - Agents challenge each other
# ============================================================================
CROSS_EXAM_STRATEGIST_PROMPT = """You are the Chief Strategy Officer. The Financial Advisor just challenged your position.

THEIR CHALLENGE: {challenge}

Respond with fire. Either:
- CONCEDE partially if they have a point, but defend your core thesis
- COUNTER their specific argument with evidence or logic
- REFRAME the debate - they might be solving a different problem

Don't just repeat yourself. ENGAGE with their specific point.

FORMAT:
**Acknowledging:**
[What they're right about, if anything]

**But Here's The Thing:**
[Your response to their specific challenge]

**What This Debate Is Really About:**
[Reframe if needed - what's the actual disagreement?]

Sign with: [Strategic Advisor in Cross-Examination]"""

CROSS_EXAM_FINANCIAL_PROMPT = """You are the Chief Financial Officer. The Risk Advisor just challenged your financial assumptions.

THEIR CHALLENGE: {challenge}

Respond with precision. Either:
- DEFEND your numbers if they're solid
- ADJUST your projections if they're challenged effectively
- PIVOT to a different financial angle they haven't addressed

Don't be contrarian just to win. Seek TRUTH, not victory.

FORMAT:
**On Their Risk Points:**
[How your financial model accounts for what they raised]

**The Number That Matters Most:**
[One key metric that drives your confidence]

**What Would Break Your Case:**
[One financial risk you genuinely can't dismiss]

Sign with: [Financial Advisor in Cross-Examination]"""

CROSS_EXAM_RISK_PROMPT = """You are the Chief Risk Officer. The Strategist just made their case.

THEIR ARGUMENT: {challenge}

Respond as the reality check. Either:
- CHALLENGE their optimism with specific risk data
- AGREE that risks are manageable IF specific conditions are met
- WARN that they're underestimating a threat

Don't be the "no" person. Be the "yes, but understand this first" person.

FORMAT:
**What They're Right About:**
[Where optimism is justified]

**The Risk Nobody Talks About:**
[Your specific concern they're missing]

**The Question They Need to Answer:**
[One thing they haven't addressed that matters]

Sign with: [Risk Advisor in Cross-Examination]"""

# ============================================================================
# PHASE 3: Devil's Advocate - The contrarian
# ============================================================================
DEVILS_ADVOCATE_PROMPT = """You are the Devil's Advocate on the board. Your ONLY job is to be deliberately provocative.

ORIGINAL QUESTION: {query}

Everything the board has discussed:
{board_discussion}

Your job is to make them UNCOMFORTABLE. Challenge assumptions. Point out contradictions. Ask the question nobody wants to ask.

Be ANNOYING but insightful. You're not trying to be right - you're trying to make sure they've thought of everything.

FORMAT:
**The Uncomfortable Question:**
[Something nobody wants to address]

**The Hypocrisy Alert:**
[Where the board is contradicting itself]

**The Alternative Nobody Mentioned:**
[What else could be done that changes everything?]

**The Risk That Keeps You Up At Night:**
[Not because it will happen - but because it COULD]

Sign with: [Devil's Advocate]"""

# ============================================================================
# PHASE 4: Final Deliberation - The CEO decides
# ============================================================================
CEO_DELIBERATION_PROMPT = """You are the Chief Executive Officer. The buck stops here.

ORIGINAL QUESTION: {query}

Here's what the board debated:
{board_discussion}

You've heard strategists argue, finance push back, risks raise alarms, and a devil's advocate challenge everything.

Now make a DECISION. Not a summary - a DECISION.

This means:
- ACCEPTING trade-offs (every choice has a cost)
- REJECTING some arguments (even good ones that don't fit)
- OWNING the risk (you might be wrong)
- GIVING DIRECTION (not "on one hand" - "we should")

FORMAT:
**The Decision:**
[One clear statement of what we're doing. Not "consider" - DO]

**What I'm Rejecting:**
[What the board suggested that I'm NOT going with, and why]

**The Trade-Off I'm Accepting:**
[What we're giving up by choosing this path]

**What Happens If I'm Wrong:**
[Honest acknowledgment of failure mode]

**First Action:**
[One thing we do this week]

Sign with: [Chief Executive Officer - Final Decision]"""


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
            error_str = str(e)
            error_type = type(e).__name__
            logger.error(f"Attempt {attempt+1}/{max_retries} FAILED")
            logger.error(f"Error type: {error_type}")
            logger.error(f"Error message: {error_str}")
            logger.error(f"Provider: {type(llm).__name__}")
            
            # Always retry on any error
            sleep_time = 2 ** attempt * 2
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
            continue
    
    raise Exception(f"LLM call failed after {max_retries} retries")


# ============================================================================
# Helper: Get board discussion for context
# ============================================================================
def get_board_discussion(state: AgentState, max_chars: int = 3000) -> str:
    """Get formatted discussion from all messages."""
    discussion = []
    for msg in state["messages"]:
        name = getattr(msg, "name", "unknown")
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            content = content[0] if content else ""
        if content and str(content).strip():
            discussion.append(f"[{name.upper()}]:\n{str(content)[:500]}\n")
    
    result = "\n---\n".join(discussion[-10:])  # Last 10 messages
    if len(result) > max_chars:
        result = result[-max_chars:]
    return result


# ============================================================================
# PHASE 1: Opening Statements
# ============================================================================
def strategist_opening(state: AgentState, config: RunnableConfig):
    """Phase 1: Strategist makes opening argument."""
    logger.info("PHASE 1: Strategist opening")
    
    prompt = STRATEGIST_OPENING_PROMPT.format(query=state["current_query"])
    response = _invoke_llm(prompt, state)
    response.name = "strategist_opening"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["strategist_opening"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "opening"}


def financial_opening(state: AgentState, config: RunnableConfig):
    """Phase 1: Financial makes opening argument."""
    logger.info("PHASE 1: Financial opening")
    
    prompt = FINANCIAL_OPENING_PROMPT.format(query=state["current_query"])
    response = _invoke_llm(prompt, state)
    response.name = "financial_opening"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["financial_opening"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "opening"}


def risk_opening(state: AgentState, config: RunnableConfig):
    """Phase 1: Risk makes opening argument."""
    logger.info("PHASE 1: Risk opening")
    
    prompt = RISK_OPENING_PROMPT.format(query=state["current_query"])
    response = _invoke_llm(prompt, state)
    response.name = "risk_opening"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["risk_opening"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "opening"}


# ============================================================================
# PHASE 2: Cross-Examination
# ============================================================================
def strategist_cross_exam(state: AgentState, config: RunnableConfig):
    """Phase 2: Strategist responds to challenges."""
    logger.info("PHASE 2: Strategist cross-examination")
    
    # Find Financial's challenge
    challenge = ""
    for msg in reversed(state["messages"]):
        name = getattr(msg, "name", "")
        if name == "financial_opening":
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                content = content[0] if content else ""
            challenge = str(content)
            break
    
    prompt = CROSS_EXAM_STRATEGIST_PROMPT.format(challenge=challenge)
    response = _invoke_llm(prompt, state)
    response.name = "strategist_cross"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["strategist_cross"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "debate"}


def financial_cross_exam(state: AgentState, config: RunnableConfig):
    """Phase 2: Financial responds to challenges."""
    logger.info("PHASE 2: Financial cross-examination")
    
    # Find Risk's challenge
    challenge = ""
    for msg in reversed(state["messages"]):
        name = getattr(msg, "name", "")
        if name == "risk_opening":
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                content = content[0] if content else ""
            challenge = str(content)
            break
    
    prompt = CROSS_EXAM_FINANCIAL_PROMPT.format(challenge=challenge)
    response = _invoke_llm(prompt, state)
    response.name = "financial_cross"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["financial_cross"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "debate"}


def risk_cross_exam(state: AgentState, config: RunnableConfig):
    """Phase 2: Risk responds to challenges."""
    logger.info("PHASE 2: Risk cross-examination")
    
    # Find Strategist's argument
    challenge = ""
    for msg in reversed(state["messages"]):
        name = getattr(msg, "name", "")
        if name == "strategist_opening":
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                content = content[0] if content else ""
            challenge = str(content)
            break
    
    prompt = CROSS_EXAM_RISK_PROMPT.format(challenge=challenge)
    response = _invoke_llm(prompt, state)
    response.name = "risk_cross"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["risk_cross"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "debate"}


# ============================================================================
# PHASE 3: Devil's Advocate
# ============================================================================
def devils_advocate(state: AgentState, config: RunnableConfig):
    """Phase 3: Devil's advocate challenges everything."""
    logger.info("PHASE 3: Devil's Advocate")
    
    board_discussion = get_board_discussion(state)
    prompt = DEVILS_ADVOCATE_PROMPT.format(query=state["current_query"], board_discussion=board_discussion)
    response = _invoke_llm(prompt, state)
    response.name = "devils_advocate"
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["devils_advocate"] = 1
    
    return {"messages": [response], "agent_iterations": new_iterations, "meeting_phase": "devil_advocate"}


# ============================================================================
# PHASE 4: CEO Final Decision
# ============================================================================
def ceo_deliberation(state: AgentState, config: RunnableConfig):
    """Phase 4: CEO makes final decision."""
    logger.info("PHASE 4: CEO Final Deliberation")
    
    board_discussion = get_board_discussion(state)
    prompt = CEO_DELIBERATION_PROMPT.format(query=state["current_query"], board_discussion=board_discussion)
    response = _invoke_llm(prompt, state)
    response.name = "ceo_decision"
    
    # Extract decision content
    content = getattr(response, 'content', '')
    if isinstance(content, list):
        content = content[0] if content else ''
    
    new_iterations = dict(state["agent_iterations"])
    new_iterations["ceo_decision"] = 1
    
    return {
        "messages": [response],
        "agent_iterations": new_iterations,
        "board_decision": str(content) if content else '',
        "meeting_phase": "final",
        "next": "FINAL"
    }


# ============================================================================
# Supervisor (Legacy - kept for compatibility)
# ============================================================================
def supervisor_node(state: AgentState, config: RunnableConfig):
    """Fixed sequential routing through authentic board meeting phases."""
    logger.info("Supervisor routing through board meeting")
    
    iterations = state["agent_iterations"]
    
    # Track which phases completed
    phases_completed = sum(1 for k, v in iterations.items() if v > 0)
    
    if iterations.get("strategist_opening", 0) == 0:
        next_agent = "strategist_opening"
    elif iterations.get("financial_opening", 0) == 0:
        next_agent = "financial_opening"
    elif iterations.get("risk_opening", 0) == 0:
        next_agent = "risk_opening"
    elif iterations.get("strategist_cross", 0) == 0:
        next_agent = "strategist_cross"
    elif iterations.get("financial_cross", 0) == 0:
        next_agent = "financial_cross"
    elif iterations.get("risk_cross", 0) == 0:
        next_agent = "risk_cross"
    elif iterations.get("devils_advocate", 0) == 0:
        next_agent = "devils_advocate"
    elif iterations.get("ceo_decision", 0) == 0:
        next_agent = "ceo_deliberation"
    else:
        next_agent = "FINAL"
    
    logger.info(f"Routing to: {next_agent}")
    return {"messages": [], "next": next_agent}


# Legacy nodes (redirect to new structure)
def strategist_node(state: AgentState, config: RunnableConfig):
    return strategist_opening(state, config)

def financial_node(state: AgentState, config: RunnableConfig):
    return financial_opening(state, config)

def risk_node(state: AgentState, config: RunnableConfig):
    return risk_opening(state, config)

def ceo_node(state: AgentState, config: RunnableConfig):
    return ceo_deliberation(state, config)


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
