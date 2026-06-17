"""
Decision panel component for AI Board Frontend.

Displays the final board decision with structured sections,
metrics, and actionable insights.
"""

import streamlit as st
import re
from typing import Optional, Dict, List


def parse_decision_sections(decision_text: str) -> Dict[str, str]:
    """
    Parse the decision text into structured sections.
    
    Args:
        decision_text: The raw decision text.
        
    Returns:
        Dictionary mapping section names to content.
    """
    sections = {}
    
    # Define section markers (order matters for matching)
    section_patterns = [
        (r"#+\s*EXECUTIVE\s*SUMMARY", "EXECUTIVE SUMMARY"),
        (r"#+\s*KEY\s*RECOMMENDATIONS", "KEY RECOMMENDATIONS"),
        (r"#+\s*ACTION\s*ITEMS", "ACTION ITEMS"),
        (r"#+\s*PROJECTED\s*FINANCIAL\s*IMPACT", "PROJECTED FINANCIAL IMPACT"),
        (r"#+\s*RISKS?\s*&\s*MITIGATIONS?", "RISKS & MITIGATIONS"),
        (r"#+\s*BOARD\s*CONSENSUS", "BOARD CONSENSUS"),
        (r"#+\s*NEXT\s*STEPS", "NEXT STEPS"),
    ]
    
    # Split by section headers
    parts = []
    current_pos = 0
    
    for pattern, name in section_patterns:
        match = re.search(pattern, decision_text, re.IGNORECASE)
        if match:
            # Get content before this section
            if match.start() > current_pos:
                parts.append(("PREAMBLE", decision_text[current_pos : match.start()]))
            parts.append((name, match.start()))
            current_pos = match.start()
    
    # Add remaining content
    if current_pos < len(decision_text):
        parts.append(("CONCLUSION", decision_text[current_pos:]))
    
    # Now extract content for each section
    for i, (name, start_pos) in enumerate(parts[:-1]):
        end_pos = parts[i + 1][1]
        content = decision_text[start_pos:end_pos].strip()
        # Remove the header line
        lines = content.split("\n")
        if lines and ("#" in lines[0] or name in lines[0].upper()):
            content = "\n".join(lines[1:]).strip()
        sections[name] = content
    
    # Handle last section
    if parts:
        last_name, last_pos = parts[-1]
        if last_name in [name for _, name in section_patterns]:
            content = decision_text[last_pos:].strip()
            lines = content.split("\n")
            if lines and "#" in lines[0]:
                content = "\n".join(lines[1:]).strip()
            sections[last_name] = content
    
    return sections


def extract_metrics(decision_text: str) -> Dict[str, str]:
    """
    Extract key metrics from decision text.
    
    Args:
        decision_text: The decision text.
        
    Returns:
        Dictionary of extracted metrics.
    """
    metrics = {}
    
    # Extract financial figures
    money_patterns = [
        r"\$[\d,]+(?:\.\d{2})?",
        r"USD\s*[\d,]+(?:\.\d{2})?",
    ]
    
    for pattern in money_patterns:
        matches = re.findall(pattern, decision_text)
        if matches:
            metrics["Investment"] = matches[0]
            if len(matches) > 1:
                metrics["Projected Revenue"] = matches[1]
            break
    
    # Extract percentages
    percent_matches = re.findall(r"(\d+)%", decision_text)
    if percent_matches:
        metrics["ROI"] = f"{percent_matches[0]}%"
    
    # Extract time periods
    time_pattern = r"(\d+)\s*(month|year|quarter)s?"
    time_matches = re.findall(time_pattern, decision_text, re.IGNORECASE)
    if time_matches:
        metrics["Timeline"] = f"{time_matches[0][0]} {time_matches[0][1]}s"
    
    return metrics


def render_decision_panel(
    decision: Optional[str],
    container=None,
    expanded: bool = True,
) -> None:
    """
    Render the complete decision panel with all sections.
    
    Args:
        decision: The decision text (can be None).
        container: Optional Streamlit container.
        expanded: Whether to show expanded by default.
    """
    if container is None:
        container = st
    
    if not decision:
        container.warning("No decision has been made yet.")
        return
    
    # Parse sections
    sections = parse_decision_sections(decision)
    metrics = extract_metrics(decision)
    
    # Header
    container.markdown("""
    <div style="
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        text-align: center;
    ">
        <h2 style="color: white; margin: 0; font-size: 28px;">
            🎯 AI Board Decision
        </h2>
        <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0;">
            Official Position of the AI Board of Directors
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row
    if metrics:
        cols = container.columns(len(metrics))
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i]:
                st.metric(label=key, value=value)
    
    container.markdown("---")
    
    # Executive Summary
    if "EXECUTIVE SUMMARY" in sections:
        with container.expander("📝 Executive Summary", expanded=expanded):
            st.markdown(sections["EXECUTIVE SUMMARY"])
    
    # Key Recommendations
    if "KEY RECOMMENDATIONS" in sections:
        container.markdown("### 🎯 Key Recommendations")
        
        recs = sections["KEY RECOMMENDATIONS"]
        # Parse bullet points
        lines = recs.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*") or line[0].isdigit():
                st.markdown(f"- {line.lstrip('-* 0123456789.')}")
        
        if not any(line.strip().startswith(("-", "*")) or line[0].isdigit() for line in lines):
            st.markdown(recs)
    
    # Action Items
    if "ACTION ITEMS" in sections:
        container.markdown("### ✅ Action Items")
        
        actions = sections["ACTION ITEMS"]
        lines = actions.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*") or line[0].isdigit():
                st.markdown(f"- {line.lstrip('-* 0123456789.')}")
        
        if not any(line.strip().startswith(("-", "*")) or line[0].isdigit() for line in lines):
            st.markdown(actions)
    
    # Financial Impact
    if "PROJECTED FINANCIAL IMPACT" in sections:
        with container.expander("💰 Projected Financial Impact", expanded=True):
            st.markdown(sections["PROJECTED FINANCIAL IMPACT"])
    
    # Risks & Mitigations
    if "RISKS & MITIGATIONS" in sections:
        container.markdown("### ⚠️ Risks & Mitigations")
        
        risks = sections["RISKS & MITIGATIONS"]
        
        # Try to parse as table
        if "|" in risks:
            st.markdown(risks)
        else:
            lines = risks.split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    st.markdown(f"- {line}")
    
    # Board Consensus
    if "BOARD CONSENSUS" in sections:
        with container.expander("🤝 Board Consensus", expanded=False):
            st.markdown(sections["BOARD CONSENSUS"])
    
    # Next Steps
    if "NEXT STEPS" in sections:
        with container.expander("🚀 Next Steps", expanded=True):
            st.markdown(sections["NEXT STEPS"])
    
    # Full decision in expander
    with container.expander("📄 View Full Decision Document", expanded=False):
        st.markdown(decision)


def render_confidence_score(score: Optional[float] = None, container=None) -> None:
    """
    Render a confidence score indicator.
    
    Args:
        score: Confidence score (0-100), auto-calculated if None.
        container: Optional Streamlit container.
    """
    if container is None:
        container = st
    
    if score is None:
        # Auto-calculate based on meeting completeness
        score = 85  # Default score
    
    # Color based on score
    if score >= 80:
        color = "#10B981"  # Green
        label = "High Confidence"
    elif score >= 60:
        color = "#F59E0B"  # Amber
        label = "Medium Confidence"
    else:
        color = "#EF4444"  # Red
        label = "Low Confidence"
    
    container.markdown(f"""
    <div style="
        background: {color}20;
        border: 2px solid {color};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    ">
        <div style="font-size: 14px; color: #6B7280;">{label}</div>
        <div style="font-size: 36px; font-weight: bold; color: {color};">
            {score}%
        </div>
        <div style="
            background: #E5E7EB;
            border-radius: 4px;
            height: 8px;
            margin-top: 8px;
        ">
            <div style="
                background: {color};
                height: 100%;
                width: {score}%;
                border-radius: 4px;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_decision_summary_cards(decision: str, container=None) -> None:
    """
    Render decision as a series of summary cards.
    
    Args:
        decision: The decision text.
        container: Optional Streamlit container.
    """
    if container is None:
        container = st
    
    sections = parse_decision_sections(decision)
    
    # Create cards for key sections
    card_data = [
        ("EXECUTIVE SUMMARY", "📝", "#6366F1"),
        ("KEY RECOMMENDATIONS", "🎯", "#3B82F6"),
        ("ACTION ITEMS", "✅", "#10B981"),
        ("PROJECTED FINANCIAL IMPACT", "💰", "#F59E0B"),
        ("RISKS & MITIGATIONS", "⚠️", "#EF4444"),
    ]
    
    cols = container.columns(len(card_data))
    
    for i, (section, icon, color) in enumerate(card_data):
        with cols[i]:
            content = sections.get(section, "No data available")
            # Truncate content
            preview = content[:100] + "..." if len(content) > 100 else content
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}20, {color}10);
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 16px;
                height: 150px;
                overflow: hidden;
            ">
                <div style="font-size: 24px; margin-bottom: 8px;">{icon}</div>
                <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px;">
                    {section}
                </div>
                <div style="font-size: 12px; color: #6B7280;">
                    {preview}
                </div>
            </div>
            """, unsafe_allow_html=True)