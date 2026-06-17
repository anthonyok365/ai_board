"""
AI Board of Directors - Streamlit Frontend

A beautiful, modern frontend for the AI-powered Board of Directors application.
Connects seamlessly to the backend for real-time board meeting simulations.
"""

import streamlit as st
import time
import json
from datetime import datetime
from typing import Optional
import uuid

# Page configuration
st.set_page_config(
    page_title="AI Board of Directors",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import components
from components.sidebar import render_sidebar
from components.chat_display import (
    render_chat_display,
    render_agent_message,
    render_status_indicator,
    AGENT_CONFIG,
)
from components.decision_panel import render_decision_panel, parse_decision_sections
from utils.backend_client import BackendClient, get_backend_client, MeetingResult


# =============================================================================
# Custom CSS
# =============================================================================

def load_custom_css():
    """Load custom CSS for styling."""
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary: #6366F1;
        --secondary: #8B5CF6;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --dark-bg: #0F172A;
        --dark-card: #1E293B;
        --dark-border: #334155;
    }
    
    /* Dark mode styles */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    }
    
    /* Custom header */
    .main-header {
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        padding: 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 24px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    /* Card styling */
    .stCard {
        background: #1E293B;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #334155;
    }
    
    /* Metric styling */
    .stMetric {
        background: #1E293B;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #334155;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #1E293B;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border-right: 1px solid #334155;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1E293B;
    }
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64748B;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading-pulse {
        animation: pulse 1.5s infinite;
    }
    
    /* Success/Error messages */
    .success-message {
        background: #10B98120;
        border: 1px solid #10B981;
        border-radius: 8px;
        padding: 12px;
        color: #10B981;
    }
    
    .error-message {
        background: #EF444420;
        border: 1px solid #EF4444;
        border-radius: 8px;
        padding: 12px;
        color: #EF4444;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# Session State Management
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    
    defaults = {
        "meeting_active": False,
        "meeting_result": None,
        "messages": [],
        "current_agent": None,
        "meeting_error": None,
        "sidebar_config": None,
        "theme": "dark",
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    
    # Initialize session state
    init_session_state()
    
    # Load custom CSS
    load_custom_css()
    
    # Render sidebar and get configuration
    sidebar_config = render_sidebar()
    st.session_state.sidebar_config = sidebar_config
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Header
        st.markdown("""
        <div class="main-header">
            <h1 style="color: white; margin: 0; font-size: 36px;">
                🏢 AI Board of Directors
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 18px;">
                Multi-Agent Business Decision Making
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Quick stats
        if st.session_state.meeting_result:
            st.metric("Last Meeting", st.session_state.meeting_result.thread_id[:12])
            st.metric("Rounds", st.session_state.meeting_result.rounds)
            st.metric("Messages", len(st.session_state.meeting_result.messages))
    
    st.markdown("---")
    
    # Query input section
    st.markdown("### 📋 Business Question")
    
    query = st.text_area(
        "Describe the business decision or scenario for the board to discuss:",
        placeholder="Example: Should we invest $800k in expanding our AI product line next quarter?",
        height=120,
        help="Provide a clear, specific business question for the board to analyze",
    )
    
    # Start meeting button
    col_start, col_clear, col_help = st.columns([2, 1, 1])
    
    with col_start:
        start_button = st.button(
            "🚀 Start Board Meeting",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.meeting_active or not query.strip(),
        )
    
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.meeting_result = None
            st.session_state.messages = []
            st.session_state.meeting_error = None
            st.rerun()
    
    with col_help:
        st.info("💡 Tip: Be specific about the decision you need help with")
    
    # Handle meeting start
    if start_button and query.strip():
        run_meeting(query.strip(), sidebar_config)
    
    # Display results
    display_results()
    
    # Action buttons (after meeting)
    if st.session_state.meeting_result and st.session_state.meeting_result.success:
        st.markdown("---")
        render_action_buttons()


def run_meeting(query: str, config) -> None:
    """
    Run the board meeting.
    
    Args:
        query: The business question.
        config: Sidebar configuration.
    """
    # Set meeting active state
    st.session_state.meeting_active = True
    st.session_state.meeting_error = None
    st.session_state.messages = []
    
    # Create status placeholder
    status_container = st.empty()
    progress_container = st.container()
    
    try:
        # Show initial status
        status_container.info("🔄 Initializing board meeting...")
        
        # Get backend client
        client = get_backend_client()
        
        # Show configuration
        status_container.info(
            f"🤖 Starting meeting with {config.provider.title()} - "
            f"{config.model} (Round {1}/{config.max_rounds})"
        )
        
        # Create progress bar
        progress_bar = progress_container.progress(0)
        status_text = progress_container.empty()
        
        # Run meeting with progress updates
        with st.spinner("Board members are deliberating..."):
            result = client.run_meeting(
                query=query,
                thread_id=config.thread_id,
                provider=config.provider,
                model=config.model,
                temperature=config.temperature,
                max_rounds=config.max_rounds,
                use_premium=config.use_premium,
                recursion_limit=config.recursion_limit,
            )
        
        # Store result
        st.session_state.meeting_result = result
        st.session_state.messages = result.messages
        
        # Clear progress
        progress_bar.progress(100)
        status_text.success("✅ Board meeting completed!")
        
        # Show success message
        if result.success:
            st.success(f"🎉 Meeting completed successfully! Thread ID: {result.thread_id}")
        else:
            st.error(f"Meeting encountered an error: {result.error}")
        
    except Exception as e:
        st.session_state.meeting_error = str(e)
        st.error(f"❌ Error running meeting: {e}")
        
    finally:
        st.session_state.meeting_active = False
        time.sleep(1)
        st.rerun()


def display_results():
    """Display meeting results."""
    
    result = st.session_state.meeting_result
    
    if not result and not st.session_state.messages:
        # Show placeholder
        st.markdown("""
        <div style="
            background: #1E293B;
            border: 2px dashed #334155;
            border-radius: 16px;
            padding: 48px;
            text-align: center;
            margin: 24px 0;
        ">
            <div style="font-size: 64px; margin-bottom: 16px;">🏛️</div>
            <h3 style="color: #94A3B8; margin: 0;">No Meeting Yet</h3>
            <p style="color: #64748B; margin: 8px 0 0 0;">
                Enter a business question above and click "Start Board Meeting" 
                to see the AI board discuss and make recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if st.session_state.meeting_active:
        # Show loading state
        st.markdown("""
        <div style="text-align: center; padding: 24px;">
            <div class="loading-pulse" style="font-size: 48px;">⏳</div>
            <p style="color: #94A3B8; margin-top: 16px;">
                Board members are deliberating...
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Display chat transcript
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 💬 Board Discussion")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Summary", "💬 Full Transcript", "📜 Raw"])
        
        with tab1:
            # Summary view with agent counts
            agent_counts = {}
            for msg in st.session_state.messages:
                name = getattr(msg, 'name', 'unknown') or 'unknown'
                agent_counts[name] = agent_counts.get(name, 0) + 1
            
            cols = st.columns(len(agent_counts))
            for i, (agent, count) in enumerate(agent_counts.items()):
                info = AGENT_CONFIG.get(agent, {"icon": "🤖", "name": agent.title()})
                with cols[i]:
                    st.metric(
                        label=f"{info['icon']} {info['name'].split()[-1]}",
                        value=f"{count} messages",
                    )
        
        with tab2:
            # Full transcript
            render_chat_display(st.session_state.messages)
        
        with tab3:
            # Raw messages
            st.json({
                "message_count": len(st.session_state.messages),
                "messages": [
                    {
                        "agent": getattr(msg, 'name', 'unknown'),
                        "content": msg.content if hasattr(msg, 'content') else str(msg),
                    }
                    for msg in st.session_state.messages
                ],
            })
    
    # Display decision
    if result and result.decision:
        st.markdown("---")
        st.markdown("### 🎯 Final Decision")
        render_decision_panel(result.decision)
    
    # Display error if any
    if st.session_state.meeting_error:
        st.error(f"Meeting Error: {st.session_state.meeting_error}")


def render_action_buttons():
    """Render action buttons for meeting results."""
    
    result = st.session_state.meeting_result
    
    st.markdown("### 📋 Actions")
    
    col_save, col_export, col_new = st.columns(3)
    
    with col_save:
        if st.button("💾 Save Meeting", use_container_width=True):
            try:
                client = get_backend_client()
                filepath = client.save_meeting(result)
                st.success(f"✅ Meeting saved to: {filepath}")
            except Exception as e:
                st.error(f"Failed to save: {e}")
    
    with col_export:
        if st.button("📤 Export JSON", use_container_width=True):
            try:
                json_data = json.dumps(result.to_dict(), indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"{result.thread_id}.json",
                    mime="application/json",
                )
            except Exception as e:
                st.error(f"Failed to export: {e}")
    
    with col_new:
        if st.button("✨ New Meeting", use_container_width=True):
            st.session_state.meeting_result = None
            st.session_state.messages = []
            st.rerun()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()