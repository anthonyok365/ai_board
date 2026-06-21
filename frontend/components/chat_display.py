"""
Chat display component for AI Board Frontend.

Renders beautiful, real-time debate display with colored agent cards,
avatars, and streaming simulation.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, List, Callable
import time


# Agent configuration
AGENT_CONFIG = {
    "supervisor": {
        "name": "Board Chair",
        "icon": "👔",
        "color": "#6366F1",  # Indigo
        "description": "Orchestrates the board discussion",
    },
    "strategist": {
        "name": "Chief Strategy Officer",
        "icon": "🎯",
        "color": "#3B82F6",  # Blue
        "description": "Growth & market strategy",
    },
    "financial": {
        "name": "Chief Financial Officer",
        "icon": "💰",
        "color": "#10B981",  # Emerald
        "description": "Financial analysis & ROI",
    },
    "risk": {
        "name": "Chief Risk Officer",
        "icon": "⚠️",
        "color": "#F59E0B",  # Amber
        "description": "Risk assessment & mitigation",
    },
    "ceo": {
        "name": "Chief Executive Officer",
        "icon": "👨‍💼",
        "color": "#8B5CF6",  # Violet
        "description": "Executive decision & synthesis",
    },
    "final_decision": {
        "name": "Board Secretary",
        "icon": "📋",
        "color": "#EC4899",  # Pink
        "description": "Final decision summary",
    },
}


def get_agent_info(agent_name: str) -> dict:
    """
    Get configuration for an agent by name.
    
    Args:
        agent_name: The agent identifier.
        
    Returns:
        Agent configuration dictionary.
    """
    return AGENT_CONFIG.get(
        agent_name.lower().strip(),
        {
            "name": agent_name.title(),
            "icon": "🤖",
            "color": "#6B7280",  # Gray
            "description": "Board member",
        }
    )


def render_agent_avatar(agent_name: str, size: str = "medium") -> str:
    """
    Generate HTML for an agent avatar.
    
    Args:
        agent_name: The agent identifier.
        size: Avatar size (small, medium, large).
        
    Returns:
        HTML string for the avatar.
    """
    info = get_agent_info(agent_name)
    
    size_map = {
        "small": "32px",
        "medium": "48px",
        "large": "64px",
    }
    
    font_size = {
        "small": "16px",
        "medium": "24px",
        "large": "32px",
    }
    
    px = size_map.get(size, "48px")
    fs = font_size.get(size, "24px")
    
    return f"""
    <div style="
        width: {px};
        height: {px};
        border-radius: 50%;
        background: {info['color']};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {fs};
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    ">
        {info['icon']}
    </div>
    """


def render_agent_card(
    agent_name: str,
    content: str,
    timestamp: Optional[datetime] = None,
    expanded: bool = False,
) -> str:
    """
    Generate HTML for an agent message card.
    
    Args:
        agent_name: The agent identifier.
        content: The message content.
        timestamp: Optional timestamp.
        expanded: Whether to show expanded by default.
        
    Returns:
        HTML string for the agent card.
    """
    info = get_agent_info(agent_name)
    
    time_str = ""
    if timestamp:
        time_str = timestamp.strftime("%H:%M:%S")
    
    # Truncate long content for preview
    preview = content[:300] + "..." if len(content) > 300 else content
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {info['color']}15, {info['color']}05);
        border-left: 4px solid {info['color']};
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="
                width: 48px;
                height: 48px;
                border-radius: 50%;
                background: {info['color']};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            ">
                {info['icon']}
            </div>
            <div>
                <div style="font-weight: 600; font-size: 16px; color: #1F2937;">
                    {info['name']}
                </div>
                <div style="font-size: 12px; color: #6B7280;">
                    {info['description']} {f'• {time_str}' if time_str else ''}
                </div>
            </div>
        </div>
        <div style="
            font-size: 14px;
            line-height: 1.6;
            color: #374151;
            white-space: pre-wrap;
        ">
            {content}
        </div>
    </div>
    """


def render_status_indicator(agent_name: str, status: str = "speaking") -> str:
    """
    Generate HTML for a status indicator.
    
    Args:
        agent_name: The agent identifier.
        status: Status text (speaking, analyzing, etc.).
        
    Returns:
        HTML string for the indicator.
    """
    info = get_agent_info(agent_name)
    
    status_colors = {
        "speaking": "#10B981",
        "analyzing": "#3B82F6",
        "thinking": "#F59E0B",
        "waiting": "#6B7280",
    }
    
    color = status_colors.get(status.lower(), "#6B7280")
    
    return f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: {color}20;
        border: 1px solid {color};
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
    ">
        <span style="
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {color};
            animation: pulse 1.5s infinite;
        "></span>
        <span style="color: {color};">
            {info['icon']} {info['name']} {status}...
        </span>
    </div>
    """


def render_chat_display(
    messages: list,
    container=None,
    show_expanders: bool = True,
) -> None:
    """
    Render the full chat display with all messages.
    
    Args:
        messages: List of message objects.
        container: Optional Streamlit container.
        show_expanders: Whether to show expanders for full transcript.
    """
    if container is None:
        container = st
    
    if not messages:
        container.info("No messages yet. Start a board meeting to see the discussion.")
        return
    
    # Group messages by agent for better display
    agent_messages = {}
    for msg in messages:
        name = getattr(msg, 'name', 'unknown') or 'unknown'
        if name not in agent_messages:
            agent_messages[name] = []
        agent_messages[name].append(msg)
    
    # Display summary first
    container.markdown("### 📊 Discussion Summary")
    
    cols = container.columns(len(agent_messages))
    for i, (agent, msgs) in enumerate(agent_messages.items()):
        info = get_agent_info(agent)
        with cols[i]:
            st.metric(
                label=f"{info['icon']} {info['name'].split()[-1]}",
                value=f"{len(msgs)}",
                help=info['description'],
            )
    
    st.markdown("---")
    
    # Display full transcript
    container.markdown("### 💬 Full Transcript")
    
    for i, msg in enumerate(messages):
        name = getattr(msg, 'name', 'unknown') or 'unknown'
        content = getattr(msg, 'content', '') if hasattr(msg, 'content') else str(msg)
        # Handle list content (can happen with some LLM providers)
        if isinstance(content, list):
            content = content[0] if content else ''
        content = str(content) if content else ''
        
        # Render with expander for long messages
        if len(content) > 500 and show_expanders:
            with container.expander(
                f"{get_agent_info(name)['icon']} **{get_agent_info(name)['name']}**",
                expanded=False,
            ):
                st.markdown(content)
        else:
            st.markdown(render_agent_card(name, content), unsafe_allow_html=True)
    
    # Show expandable full transcript
    if show_expanders:
        with container.expander("📜 View Full Raw Transcript"):
            for msg in messages:
                name = getattr(msg, 'name', 'unknown') or 'unknown'
                content = getattr(msg, 'content', '') if hasattr(msg, 'content') else str(msg)
                # Handle list content
                if isinstance(content, list):
                    content = content[0] if content else ''
                st.text(f"[{name.upper()}] {str(content)}")


def render_agent_message(
    agent_name: str,
    content: str,
    container=None,
) -> None:
    """
    Render a single agent message.
    
    Args:
        agent_name: The agent identifier.
        content: The message content.
        container: Optional Streamlit container.
    """
    if container is None:
        container = st
    
    container.markdown(render_agent_card(agent_name, content), unsafe_allow_html=True)


def render_streaming_message(
    agent_name: str,
    container=None,
) -> Callable[[str], None]:
    """
    Create a streaming message display that can be updated incrementally.
    
    Args:
        agent_name: The agent identifier.
        container: Optional Streamlit container.
        
    Returns:
        Callback function to update the message content.
    """
    if container is None:
        container = st
    
    info = get_agent_info(agent_name)
    placeholder = container.empty()
    
    # Show status indicator
    placeholder.markdown(
        render_status_indicator(agent_name, "thinking"),
        unsafe_allow_html=True,
    )
    
    def update(content: str):
        placeholder.markdown(render_agent_card(agent_name, content), unsafe_allow_html=True)
    
    return update


def render_meeting_progress(
    current_agent: str,
    round_num: int,
    total_rounds: int,
    container=None,
) -> None:
    """
    Render meeting progress indicator.
    
    Args:
        current_agent: Current agent name.
        round_num: Current round number.
        total_rounds: Total rounds.
        container: Optional Streamlit container.
    """
    if container is None:
        container = st
    
    info = get_agent_info(current_agent)
    
    progress = min(round_num / total_rounds, 1.0)
    
    container.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {info['color']}20, transparent);
        padding: 20px;
        border-radius: 12px;
        margin: 16px 0;
    ">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="font-size: 24px;">{info['icon']}</span>
            <div>
                <div style="font-weight: 600;">{info['name']}</div>
                <div style="font-size: 12px; color: #6B7280;">{info['description']}</div>
            </div>
        </div>
        <div style="
            background: #E5E7EB;
            border-radius: 8px;
            height: 8px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, {info['color']}, {info['color']}CC);
                height: 100%;
                width: {progress * 100}%;
                border-radius: 8px;
                transition: width 0.5s ease;
            "></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #6B7280;">
            <span>Round {round_num} of {total_rounds}</span>
            <span>{int(progress * 100)}% complete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def simulate_streaming(
    text: str,
    container=None,
    words_per_second: int = 30,
) -> None:
    """
    Simulate streaming text display with typing effect.
    
    Args:
        text: The text to display.
        container: Optional Streamlit container.
        words_per_second: Typing speed.
    """
    if container is None:
        container = st
    
    placeholder = container.empty()
    words = text.split()
    
    for i, word in enumerate(words):
        partial = " ".join(words[: i + 1])
        placeholder.markdown(f"```\n{partial}\n```")
        time.sleep(1 / words_per_second)