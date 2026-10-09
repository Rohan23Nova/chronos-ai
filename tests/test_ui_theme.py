"""
Unit tests for Chronos AI UI theming, tokens, styles, and presentation components.
"""

import unittest
from chronos.ui.theme import get_theme, LIGHT_THEME, DARK_THEME, ALGORITHM_COLORS
from chronos.ui.styles import get_theme_css
from chronos.ui.components import render_badge


class TestUITheme(unittest.TestCase):

    def test_theme_retrieval(self):
        dark = get_theme("Dark")
        self.assertEqual(dark.name, "Dark")
        self.assertEqual(dark.bg, "#10121B")
        self.assertEqual(dark.surface, "#191C29")

        light = get_theme("Light")
        self.assertEqual(light.name, "Light")
        self.assertEqual(light.bg, "#F5F6FA")
        self.assertEqual(light.surface, "#FFFFFF")

        default_theme = get_theme("unknown")
        self.assertEqual(default_theme.name, "Dark")

    def test_algorithm_colors_complete(self):
        for alg in ["A*", "UCS", "BFS", "DFS"]:
            self.assertIn(alg, ALGORITHM_COLORS)
            self.assertTrue(ALGORITHM_COLORS[alg].startswith("#"))

    def test_theme_css_generation(self):
        dark_css = get_theme_css("Dark")
        self.assertIn("--chronos-bg: #10121B", dark_css)
        self.assertIn("--chronos-surface: #191C29", dark_css)
        self.assertIn("chronos-header", dark_css)

        light_css = get_theme_css("Light")
        self.assertIn("--chronos-bg: #F5F6FA", light_css)
        self.assertIn("--chronos-surface: #FFFFFF", light_css)

    def test_badge_component_rendering(self):
        badge = render_badge("Feasible", "success")
        self.assertIn('class="chronos-badge chronos-badge-success"', badge)
        self.assertIn("Feasible", badge)

        badge_escaped = render_badge("Risk < High & Urgent", "warning")
        self.assertIn("&lt;", badge_escaped)
        self.assertIn("&amp;", badge_escaped)

        fallback_badge = render_badge("Unknown Type", "nonexistent")
        self.assertIn('class="chronos-badge chronos-badge-neutral"', fallback_badge)


if __name__ == "__main__":
    unittest.main()
