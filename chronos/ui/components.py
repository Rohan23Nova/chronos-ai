"""
Reusable presentation components for Chronos AI UI.
Linear/Notion-inspired minimalist presentation cards, badges, and headers.
"""

from typing import List, Optional, Tuple, Union
import html
import streamlit as st


def render_badge(text: str, badge_type: str = "primary") -> str:
    """
    Generate HTML for a semantic status or category badge.
    badge_type options: 'primary', 'cyan', 'success', 'warning', 'danger', 'neutral'.
    """
    clean_text = html.escape(str(text))
    valid_types = {"primary", "cyan", "success", "warning", "danger", "neutral"}
    btype = badge_type if badge_type in valid_types else "neutral"
    return f'<span class="chronos-badge chronos-badge-{btype}">{clean_text}</span>'


def render_header(
    title: str,
    subtitle: str,
    badges: Optional[List[Union[str, Tuple[str, str]]]] = None,
) -> None:
    """
    Render a clean, modern page header with optional status/tag badges.
    """
    escaped_title = html.escape(title)
    escaped_sub = html.escape(subtitle)
    
    badge_html = ""
    if badges:
        items = []
        for b in badges:
            if isinstance(b, tuple):
                items.append(render_badge(b[0], b[1]))
            else:
                items.append(render_badge(b, "primary"))
        badge_html = f'<div class="chronos-badge-bar">{"".join(items)}</div>'

    st.markdown(
        f"""
        <div class="chronos-header">
            <h1 class="chronos-title">{escaped_title}</h1>
            <p class="chronos-subtitle">{escaped_sub}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(
    icon: str,
    title: str,
    description: str,
    action_hint: Optional[str] = None,
) -> None:
    """Render a clean empty state card with guidance."""
    e_icon = html.escape(icon)
    e_title = html.escape(title)
    e_desc = html.escape(description)
    
    hint_html = ""
    if action_hint:
        hint_html = f'<div style="font-size: 0.85rem; font-weight: 600; opacity: 0.8;">💡 {html.escape(action_hint)}</div>'

    st.markdown(
        f"""
        <div class="chronos-empty-state">
            <div class="chronos-empty-icon">{e_icon}</div>
            <div class="chronos-empty-title">{e_title}</div>
            <div class="chronos-empty-desc">{e_desc}</div>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_timeline_slot(
    start_time: int,
    end_time: int,
    task_name: str,
    priority: str = "medium",
    difficulty: str = "medium",
    deadline: Optional[int] = None,
) -> None:
    """Render an individual timeline slot for a scheduled task."""
    p_badge_type = {
        "high": "danger",
        "medium": "warning",
        "low": "neutral",
    }.get(priority.lower(), "neutral")

    meta_parts = [
        f"Duration: {end_time - start_time}h",
        f"Difficulty: {difficulty.capitalize()}",
    ]
    if deadline is not None:
        meta_parts.append(f"Deadline: {deadline}:00")

    meta_text = " • ".join(meta_parts)
    badge = render_badge(f"Priority: {priority.upper()}", p_badge_type)

    st.markdown(
        f"""
        <div class="chronos-timeline-slot">
            <div class="chronos-time-badge">{start_time:02d}:00 – {end_time:02d}:00</div>
            <div class="chronos-slot-info">
                <div class="chronos-slot-name">{html.escape(task_name)}</div>
                <div class="chronos-slot-meta">{html.escape(meta_text)}</div>
            </div>
            <div>{badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(title: str, description: Optional[str] = None, content: str = "") -> None:
    """Render a content card with title and body."""
    e_title = html.escape(title)
    desc_html = f'<div class="chronos-card-desc">{html.escape(description)}</div>' if description else ""
    st.markdown(
        f"""
        <div class="chronos-card">
            <div class="chronos-card-title">{e_title}</div>
            {desc_html}
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )
