"""
Design system tokens and color themes for Chronos AI.
Linear-inspired minimalism with Notion-like clarity.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ThemeColors:
    name: str
    bg: str
    sidebar_bg: str
    surface: str
    surface_secondary: str
    text_primary: str
    text_secondary: str
    border: str
    primary_action: str
    primary_hover: str
    accent_surface: str
    accent_lavender: str
    signal_cyan: str
    success_green: str
    warning_amber: str
    error_red: str


LIGHT_THEME = ThemeColors(
    name="Light",
    bg="#F5F6FA",
    sidebar_bg="#FFFFFF",
    surface="#FFFFFF",
    surface_secondary="#F0F1F8",
    text_primary="#191C2B",
    text_secondary="#777D91",
    border="#E2E5EF",
    primary_action="#6558E8",
    primary_hover="#5749DC",
    accent_surface="#F0EEFF",
    accent_lavender="#B3A9FF",
    signal_cyan="#55C6D9",
    success_green="#38B58A",
    warning_amber="#E9A54B",
    error_red="#E36D7A",
)

DARK_THEME = ThemeColors(
    name="Dark",
    bg="#10121B",
    sidebar_bg="#12141F",
    surface="#191C29",
    surface_secondary="#202436",
    text_primary="#F2F1FC",
    text_secondary="#9899AD",
    border="#2B3042",
    primary_action="#7869F6",
    primary_hover="#6959E8",
    accent_surface="#24213A",
    accent_lavender="#B3A9FF",
    signal_cyan="#55C6D9",
    success_green="#38B58A",
    warning_amber="#E9A54B",
    error_red="#E36D7A",
)

THEMES: Dict[str, ThemeColors] = {
    "Light": LIGHT_THEME,
    "Dark": DARK_THEME,
}

ALGORITHM_COLORS: Dict[str, str] = {
    "A*": "#7869F6",
    "UCS": "#55C6D9",
    "BFS": "#4A72F5",
    "DFS": "#E9A54B",
}


def get_theme(theme_name: str) -> ThemeColors:
    """Retrieve theme tokens by name, defaulting to Dark."""
    return THEMES.get(theme_name, DARK_THEME)
