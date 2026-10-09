"""
CSS theme styles and scoped stylesheets for Chronos AI.
Linear-inspired minimalism with Notion clarity and restrained cosmic accents.
"""

from chronos.ui.theme import ThemeColors, get_theme


def get_theme_css(theme_mode: str = "Dark") -> str:
    """
    Generate scoped CSS style block for the specified theme mode.
    Overwrites Streamlit UI elements with crisp Linear/Notion styling.
    """
    theme: ThemeColors = get_theme(theme_mode)
    is_dark = theme.name == "Dark"

    # Subtle shadow and glow tokens
    card_shadow = (
        "0 1px 3px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.25)"
        if is_dark
        else "0 1px 3px rgba(0, 0, 0, 0.06), 0 4px 12px rgba(0, 0, 0, 0.03)"
    )
    glow_accent = (
        "rgba(120, 105, 246, 0.15)"
        if is_dark
        else "rgba(101, 88, 232, 0.08)"
    )

    return f"""
<style>
/* ==========================================================================
   Chronos Design System Variables ({theme.name} Mode)
   ========================================================================== */
:root {{
    --chronos-bg: {theme.bg};
    --chronos-sidebar-bg: {theme.sidebar_bg};
    --chronos-surface: {theme.surface};
    --chronos-surface-secondary: {theme.surface_secondary};
    --chronos-text-primary: {theme.text_primary};
    --chronos-text-secondary: {theme.text_secondary};
    --chronos-border: {theme.border};
    --chronos-primary: {theme.primary_action};
    --chronos-primary-hover: {theme.primary_hover};
    --chronos-accent-surface: {theme.accent_surface};
    --chronos-accent-lavender: {theme.accent_lavender};
    --chronos-signal-cyan: {theme.signal_cyan};
    --chronos-success: {theme.success_green};
    --chronos-warning: {theme.warning_amber};
    --chronos-error: {theme.error_red};
    --chronos-card-shadow: {card_shadow};
    --chronos-glow-accent: {glow_accent};
}}

/* ==========================================================================
   Core Layout & Typography
   ========================================================================== */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: var(--chronos-bg) !important;
    color: var(--chronos-text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", sans-serif;
    letter-spacing: -0.01em;
}}

[data-testid="stHeader"] {{
    background-color: transparent !important;
}}

/* Top decoration bar */
[data-testid="stDecoration"] {{
    background-image: linear-gradient(90deg, var(--chronos-primary), var(--chronos-signal-cyan)) !important;
    height: 3px !important;
}}

/* ==========================================================================
   Sidebar Styling
   ========================================================================== */
[data-testid="stSidebar"] {{
    background-color: var(--chronos-sidebar-bg) !important;
    border-right: 1px solid var(--chronos-border) !important;
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
    color: var(--chronos-text-primary) !important;
}}

[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
    color: var(--chronos-text-secondary) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}}

/* Navigation Radio Styling */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {{
    gap: 4px !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] label {{
    background: transparent !important;
    padding: 7px 12px !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    color: var(--chronos-text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
    background-color: var(--chronos-surface-secondary) !important;
    color: var(--chronos-text-primary) !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {{
    background-color: var(--chronos-accent-surface) !important;
    color: var(--chronos-primary) !important;
    font-weight: 600 !important;
}}

/* Segmented Control Pill Switcher */
[data-testid="stSegmentedControl"] {{
    background-color: var(--chronos-surface-secondary) !important;
    border: 1px solid var(--chronos-border) !important;
    border-radius: 8px !important;
    padding: 2px !important;
}}

[data-testid="stSegmentedControl"] button {{
    border-radius: 6px !important;
    border: none !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--chronos-text-secondary) !important;
    transition: all 0.15s ease !important;
}}

[data-testid="stSegmentedControl"] button[data-checked="true"] {{
    background-color: var(--chronos-surface) !important;
    color: var(--chronos-text-primary) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}}

/* ==========================================================================
   Metrics & Stat Cards
   ========================================================================== */
[data-testid="stMetric"] {{
    background-color: var(--chronos-surface) !important;
    border: 1px solid var(--chronos-border) !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: var(--chronos-card-shadow) !important;
    transition: border-color 0.15s ease, transform 0.15s ease !important;
}}

[data-testid="stMetric"]:hover {{
    border-color: var(--chronos-primary) !important;
}}

[data-testid="stMetricLabel"] p {{
    color: var(--chronos-text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}}

[data-testid="stMetricValue"] div {{
    color: var(--chronos-text-primary) !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}}

/* ==========================================================================
   Buttons & Interactive Controls
   ========================================================================== */
button[kind="primary"],
.stButton > button[kind="primary"],
[data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, var(--chronos-primary), var(--chronos-primary-hover)) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.55rem 1.25rem !important;
    box-shadow: 0 2px 6px var(--chronos-glow-accent) !important;
    transition: all 0.15s ease !important;
}}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover,
[data-testid="baseButton-primary"]:hover {{
    filter: brightness(1.1) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px var(--chronos-glow-accent) !important;
}}

button[kind="secondary"],
.stButton > button,
[data-testid="baseButton-secondary"] {{
    background-color: var(--chronos-surface) !important;
    color: var(--chronos-text-primary) !important;
    border: 1px solid var(--chronos-border) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    padding: 0.5rem 1.15rem !important;
    transition: all 0.15s ease !important;
}}

button[kind="secondary"]:hover,
.stButton > button:hover,
[data-testid="baseButton-secondary"]:hover {{
    border-color: var(--chronos-primary) !important;
    background-color: var(--chronos-surface-secondary) !important;
    color: var(--chronos-primary) !important;
}}

/* Inputs, TextAreas, Selectboxes */
[data-baseweb="input"],
[data-baseweb="select"] > div,
[data-baseweb="base-input"] {{
    background-color: var(--chronos-surface-secondary) !important;
    border: 1px solid var(--chronos-border) !important;
    border-radius: 8px !important;
    color: var(--chronos-text-primary) !important;
    transition: border-color 0.15s ease !important;
}}

[data-baseweb="input"]:focus-within,
[data-baseweb="select"] > div:focus-within {{
    border-color: var(--chronos-primary) !important;
    box-shadow: 0 0 0 1px var(--chronos-primary) !important;
}}

input, textarea {{
    color: var(--chronos-text-primary) !important;
}}

/* Tabs Styling */
[data-baseweb="tab-list"] {{
    gap: 8px !important;
    border-bottom: 1px solid var(--chronos-border) !important;
    padding-bottom: 4px !important;
}}

[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--chronos-text-secondary) !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    padding: 6px 14px !important;
    transition: all 0.15s ease !important;
}}

[data-baseweb="tab"]:hover {{
    color: var(--chronos-text-primary) !important;
    background-color: var(--chronos-surface-secondary) !important;
}}

[aria-selected="true"][data-baseweb="tab"] {{
    color: var(--chronos-primary) !important;
    font-weight: 600 !important;
    background-color: var(--chronos-accent-surface) !important;
}}

[data-baseweb="tab-highlight"] {{
    background-color: var(--chronos-primary) !important;
}}

/* Expanders */
[data-testid="stExpander"] {{
    background-color: var(--chronos-surface) !important;
    border: 1px solid var(--chronos-border) !important;
    border-radius: 10px !important;
    box-shadow: var(--chronos-card-shadow) !important;
    overflow: hidden !important;
}}

[data-testid="stExpander"] summary {{
    color: var(--chronos-text-primary) !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
}}

[data-testid="stExpander"] summary:hover {{
    color: var(--chronos-primary) !important;
}}

/* DataFrames / Tables */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--chronos-border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}}

/* Alerts and Callouts */
[data-testid="stAlert"] {{
    border-radius: 10px !important;
    border: 1px solid var(--chronos-border) !important;
    background-color: var(--chronos-surface) !important;
}}

/* Dividers */
hr {{
    border: none !important;
    border-top: 1px solid var(--chronos-border) !important;
    margin: 1.5rem 0 !important;
}}

/* ==========================================================================
   Custom Chronos UI Component Classes
   ========================================================================== */
.chronos-header {{
    margin-bottom: 1.75rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--chronos-border);
}}

.chronos-title {{
    font-size: 2.1rem;
    font-weight: 750;
    letter-spacing: -0.03em;
    color: var(--chronos-text-primary);
    margin: 0 0 0.35rem 0;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}}

.chronos-subtitle {{
    font-size: 0.98rem;
    color: var(--chronos-text-secondary);
    line-height: 1.5;
    margin: 0;
    max-width: 850px;
}}

.chronos-badge-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.85rem;
}}

.chronos-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    border: 1px solid transparent;
}}

.chronos-badge-primary {{
    background-color: var(--chronos-accent-surface);
    color: var(--chronos-primary);
    border-color: var(--chronos-accent-lavender);
}}

.chronos-badge-cyan {{
    background-color: rgba(85, 198, 217, 0.12);
    color: var(--chronos-signal-cyan);
    border-color: rgba(85, 198, 217, 0.3);
}}

.chronos-badge-success {{
    background-color: rgba(56, 181, 138, 0.12);
    color: var(--chronos-success);
    border-color: rgba(56, 181, 138, 0.3);
}}

.chronos-badge-warning {{
    background-color: rgba(233, 165, 75, 0.12);
    color: var(--chronos-warning);
    border-color: rgba(233, 165, 75, 0.3);
}}

.chronos-badge-danger {{
    background-color: rgba(227, 109, 122, 0.12);
    color: var(--chronos-error);
    border-color: rgba(227, 109, 122, 0.3);
}}

.chronos-badge-neutral {{
    background-color: var(--chronos-surface-secondary);
    color: var(--chronos-text-secondary);
    border-color: var(--chronos-border);
}}

/* Custom Surface Card */
.chronos-card {{
    background-color: var(--chronos-surface);
    border: 1px solid var(--chronos-border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: var(--chronos-card-shadow);
    margin-bottom: 1.25rem;
}}

.chronos-card-title {{
    font-size: 1.1rem;
    font-weight: 650;
    color: var(--chronos-text-primary);
    margin: 0 0 0.5rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.chronos-card-desc {{
    font-size: 0.88rem;
    color: var(--chronos-text-secondary);
    margin: 0 0 1rem 0;
}}

/* Timeline Schedule Slot */
.chronos-timeline-slot {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: var(--chronos-surface);
    border: 1px solid var(--chronos-border);
    border-left: 4px solid var(--chronos-primary);
    border-radius: 8px;
    padding: 0.85rem 1.15rem;
    margin-bottom: 0.6rem;
    transition: all 0.15s ease;
}}

.chronos-timeline-slot:hover {{
    border-color: var(--chronos-primary);
    transform: translateX(2px);
}}

.chronos-time-badge {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--chronos-primary);
    background: var(--chronos-accent-surface);
    padding: 0.25rem 0.65rem;
    border-radius: 6px;
    letter-spacing: 0.02em;
}}

.chronos-slot-info {{
    flex: 1;
    margin: 0 1.25rem;
}}

.chronos-slot-name {{
    font-weight: 650;
    font-size: 0.98rem;
    color: var(--chronos-text-primary);
    margin: 0;
}}

.chronos-slot-meta {{
    font-size: 0.8rem;
    color: var(--chronos-text-secondary);
    margin-top: 0.15rem;
}}

/* Empty State Widget */
.chronos-empty-state {{
    background-color: var(--chronos-surface);
    border: 1px dashed var(--chronos-border);
    border-radius: 12px;
    padding: 2.75rem 2rem;
    text-align: center;
    margin: 1.5rem 0;
}}

.chronos-empty-icon {{
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    opacity: 0.85;
}}

.chronos-empty-title {{
    font-size: 1.2rem;
    font-weight: 650;
    color: var(--chronos-text-primary);
    margin-bottom: 0.4rem;
}}

.chronos-empty-desc {{
    font-size: 0.92rem;
    color: var(--chronos-text-secondary);
    max-width: 500px;
    margin: 0 auto 1.25rem auto;
    line-height: 1.5;
}}

/* Architectural Pill for Sidebar */
.chronos-brand-pill {{
    display: inline-block;
    padding: 0.2rem 0.5rem;
    font-size: 0.74rem;
    font-weight: 600;
    border-radius: 6px;
    background-color: var(--chronos-surface-secondary);
    color: var(--chronos-text-secondary);
    border: 1px solid var(--chronos-border);
    margin: 0 0.25rem 0.25rem 0;
}}
</style>
"""
