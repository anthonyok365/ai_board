"""
Sidebar component for AI Board Frontend.

Provides configuration options for LLM providers, models,
meeting parameters, and session management.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class SidebarConfig:
    """Configuration values from the sidebar."""
    provider: str
    model: str
    temperature: float
    max_rounds: int
    thread_id: str
    use_premium: bool
    recursion_limit: int
    api_key: Optional[str]


def render_sidebar() -> SidebarConfig:
    """
    Render the sidebar configuration panel.
    
    Returns:
        SidebarConfig with all user selections.
    """
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # ========================================================================
        # LLM Provider Selection
        # ========================================================================
        st.markdown("### 🤖 LLM Provider")
        
        provider_options = {
            "xai": "xAI (Grok)",
            "groq": "Groq (Llama)",
        }
        
        selected_provider = st.selectbox(
            "Select Provider",
            options=list(provider_options.keys()),
            format_func=lambda x: provider_options[x],
            index=0,
            help="Choose the LLM provider for the board meeting",
        )
        
        # ========================================================================
        # Model Selection
        # ========================================================================
        st.markdown("### 📊 Model")
        
        # Define models per provider
        models_by_provider = {
            "xai": {
                "grok-2": "Grok 2 (Fast & Capable)",
                "grok-2-mini": "Grok 2 Mini (Even Faster)",
            },
            "groq": {
                "llama-3.3-70b-versatile": "Llama 3.3 70B (Fast, Free tier)",
                "llama-3.1-70b-versatile": "Llama 3.1 70B (Extended Context)",
                "mixtral-8x7b-32768": "Mixtral 8x7B (Balanced)",
            },
        }
        
        provider_models = models_by_provider.get(selected_provider, {})
        model_options = list(provider_models.keys())
        model_display = list(provider_models.values())
        
        selected_model = st.selectbox(
            "Select Model",
            options=model_options,
            format_func=lambda x: provider_models.get(x, x),
            index=0,
            help="Choose the specific model to use",
        )
        
        # Premium model toggle
        use_premium = st.checkbox(
            "Use Premium Model",
            value=False,
            help="Use the most powerful (but more expensive) model variant",
        )
        
        # ========================================================================
        # Temperature Setting
        # ========================================================================
        st.markdown("### 🌡️ Temperature")
        
        temperature = st.slider(
            "Response Creativity",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Lower = more focused, Higher = more creative responses",
        )
        
        temp_labels = {
            (0.0, 0.3): "🎯 Focused",
            (0.3, 0.6): "⚖️ Balanced",
            (0.6, 0.8): "💡 Creative",
            (0.8, 1.0): "🎨 Very Creative",
        }
        
        for (low, high), label in temp_labels.items():
            if low <= temperature < high:
                st.caption(f"**Mode:** {label}")
                break
        
        # ========================================================================
        # Meeting Parameters
        # ========================================================================
        st.markdown("### 📋 Meeting Settings")
        
        max_rounds = st.slider(
            "Discussion Depth",
            min_value=1,
            max_value=10,
            value=4,
            step=1,
            help="Number of discussion rounds before final decision",
        )
        
        st.caption(f"**Rounds:** {max_rounds} (each round: Strategist → Financial → Risk → CEO)")
        
        recursion_limit = st.slider(
            "Max Steps",
            min_value=10,
            max_value=50,
            value=25,
            step=5,
            help="Maximum number of agent steps in the graph",
        )
        
        # ========================================================================
        # Session Management
        # ========================================================================
        st.markdown("### 🆔 Session")
        
        # Thread ID input
        thread_id = st.text_input(
            "Thread ID",
            value="",
            placeholder="Auto-generated if empty",
            help="Unique identifier for this meeting session",
        )
        
        # Auto-generate if empty
        if not thread_id:
            thread_id = f"meeting_{uuid.uuid4().hex[:8]}"
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New ID", use_container_width=True):
                thread_id = f"meeting_{uuid.uuid4().hex[:8]}"
                st.rerun()
        
        with col2:
            if st.button("📋 Copy", use_container_width=True):
                st.code(thread_id)
                st.toast(f"Thread ID: {thread_id}")
        
        # ========================================================================
        # API Key Input
        # ========================================================================
        st.markdown("### 🔑 API Key")
        
        api_key_help = {
            "xai": "Get your key from https://console.x.ai/",
            "groq": "Get your key from https://console.groq.com/keys",
        }
        
        # Check if API key is in environment
        import os
        env_key_map = {
            "xai": "XAI_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        
        env_key = os.getenv(env_key_map.get(selected_provider, ""), "")
        
        if env_key:
            st.success("✅ API key found in environment")
        else:
            st.warning("⚠️ API key not found in environment")
            api_key_input = st.text_input(
                f"Enter {selected_provider.title()} API Key",
                type="password",
                help=api_key_help.get(selected_provider, ""),
            )
            
            if api_key_input:
                # Store in session state for this session
                st.session_state[f"{selected_provider}_api_key"] = api_key_input
                os.environ[env_key_map[selected_provider]] = api_key_input
                st.success("✅ API key configured for this session")
        
        # ========================================================================
        # Meeting History
        # ========================================================================
        st.markdown("### 📜 Meeting History")
        
        from client.backend_client import get_backend_client
        
        try:
            client = get_backend_client()
            meetings = client.list_saved_meetings()
            
            if meetings:
                st.caption(f"**{len(meetings)} saved meetings**")
                
                for meeting in meetings[:5]:  # Show last 5
                    with st.expander(f"📄 {meeting['thread_id'][:20]}..."):
                        st.write(f"**Date:** {meeting.get('timestamp', 'Unknown')}")
                        st.write(f"**Success:** {'✅' if meeting.get('success') else '❌'}")
            else:
                st.info("No saved meetings yet")
        except Exception as e:
            st.error(f"Could not load history: {e}")
        
        # ========================================================================
        # About Section
        # ========================================================================
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption(
            "AI Board of Directors v1.0\n"
            "Built with Streamlit & LangGraph"
        )
        
        # Theme toggle
        theme = st.radio(
            "Theme",
            ["🌙 Dark", "☀️ Light"],
            horizontal=True,
            index=0,
        )
        
        if theme == "☀️ Light":
            st.session_state.theme = "light"
        else:
            st.session_state.theme = "dark"
    
    # Return configuration
    return SidebarConfig(
        provider=selected_provider,
        model=selected_model,
        temperature=temperature,
        max_rounds=max_rounds,
        thread_id=thread_id,
        use_premium=use_premium,
        recursion_limit=recursion_limit,
        api_key=env_key or st.session_state.get(f"{selected_provider}_api_key"),
    )


def get_sidebar_config() -> Optional[SidebarConfig]:
    """
    Get the current sidebar configuration from session state.
    
    Returns:
        SidebarConfig if sidebar was rendered, None otherwise.
    """
    return st.session_state.get("sidebar_config")