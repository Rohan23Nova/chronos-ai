"""
Plot generation utilities for Chronos AI evaluation experiments.
Produces clean, theme-aware figures representing measured experiment data.
"""

import os
import tempfile
from typing import List, Optional

# Ensure non-interactive backend and safe writable config directory
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "chronos_matplotlib"))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from chronos.evaluation.metrics import ExperimentResult
from chronos.ui.theme import ThemeColors, get_theme, ALGORITHM_COLORS


def _apply_theme_to_plot(fig, ax, theme: ThemeColors) -> None:
    """Apply unified theme styling to figure and axes."""
    is_dark = theme.name == "Dark"
    bg_color = theme.surface
    plot_bg = theme.surface if is_dark else "#FFFFFF"

    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(plot_bg)
    ax.title.set_color(theme.text_primary)
    ax.xaxis.label.set_color(theme.text_secondary)
    ax.yaxis.label.set_color(theme.text_secondary)
    ax.tick_params(colors=theme.text_secondary, labelsize=9)

    for spine in ax.spines.values():
        spine.set_color(theme.border)
        spine.set_linewidth(1.0)

    ax.grid(
        True,
        linestyle="--",
        alpha=0.45 if is_dark else 0.7,
        color=theme.border,
    )


def plot_scaling_expansions(
    results: List[ExperimentResult],
    output_path: str,
    theme_mode: str = "Dark",
) -> bool:
    """Plot States Expanded vs Task Count for the scaling experiment."""
    if not MATPLOTLIB_AVAILABLE:
        return False

    scaling_results = [r for r in results if r.experiment_name == "scaling_experiment"]
    if not scaling_results:
        return False

    scaling_results.sort(key=lambda r: r.task_count)
    task_counts = [r.task_count for r in scaling_results]
    expansions = [r.states_expanded for r in scaling_results]

    theme = get_theme(theme_mode)
    line_color = ALGORITHM_COLORS.get("A*", "#7869F6")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    _apply_theme_to_plot(fig, ax, theme)

    ax.plot(
        task_counts,
        expansions,
        marker="o",
        color=line_color,
        linewidth=2.2,
        markersize=6,
        label="A* (Knowledge-aware)",
    )

    ax.set_title("A* Search: States Expanded vs Task Count", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Tasks (n)", fontsize=10, labelpad=8)
    ax.set_ylabel("States Expanded", fontsize=10, labelpad=8)

    legend = ax.legend(framealpha=0.9, loc="upper left")
    if legend:
        legend.get_frame().set_facecolor(theme.surface_secondary)
        legend.get_frame().set_edgecolor(theme.border)
        for text in legend.get_texts():
            text.set_color(theme.text_primary)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return True


def plot_scaling_runtime(
    results: List[ExperimentResult],
    output_path: str,
    theme_mode: str = "Dark",
) -> bool:
    """Plot Runtime (ms) vs Task Count for the scaling experiment."""
    if not MATPLOTLIB_AVAILABLE:
        return False

    scaling_results = [r for r in results if r.experiment_name == "scaling_experiment"]
    if not scaling_results:
        return False

    scaling_results.sort(key=lambda r: r.task_count)
    task_counts = [r.task_count for r in scaling_results]
    runtimes = [r.runtime_ms for r in scaling_results]

    theme = get_theme(theme_mode)
    line_color = theme.signal_cyan

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    _apply_theme_to_plot(fig, ax, theme)

    ax.plot(
        task_counts,
        runtimes,
        marker="s",
        color=line_color,
        linewidth=2.2,
        markersize=6,
        label="Runtime (ms)",
    )

    ax.set_title("A* Search: Runtime (ms) vs Task Count", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Number of Tasks (n)", fontsize=10, labelpad=8)
    ax.set_ylabel("Runtime (milliseconds)", fontsize=10, labelpad=8)

    legend = ax.legend(framealpha=0.9, loc="upper left")
    if legend:
        legend.get_frame().set_facecolor(theme.surface_secondary)
        legend.get_frame().set_edgecolor(theme.border)
        for text in legend.get_texts():
            text.set_color(theme.text_primary)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return True


def plot_algorithm_comparison(
    results: List[ExperimentResult],
    output_path: str,
    theme_mode: str = "Dark",
) -> bool:
    """
    Plot grouped bar chart comparing States Expanded across algorithms
    for feasible scenarios (Canonical, Small, Medium).
    """
    if not MATPLOTLIB_AVAILABLE:
        return False

    comparison_results = [
        r for r in results
        if r.experiment_name == "algorithm_comparison" and r.solution_found
    ]
    if not comparison_results:
        return False

    scenarios = ["Canonical (3 tasks)", "Small (4 tasks)", "Medium (6 tasks)"]
    algorithms = ["A*", "UCS", "BFS", "DFS"]

    active_scenarios = [s for s in scenarios if any(r.scenario == s for r in comparison_results)]
    if not active_scenarios:
        return False

    data = {alg: [] for alg in algorithms}
    for s in active_scenarios:
        for alg in algorithms:
            match = next((r for r in comparison_results if r.scenario == s and r.algorithm == alg), None)
            data[alg].append(match.states_expanded if match else 0)

    import numpy as np
    x = np.arange(len(active_scenarios))
    width = 0.18

    theme = get_theme(theme_mode)
    colors = [ALGORITHM_COLORS.get(alg, theme.primary_action) for alg in algorithms]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    _apply_theme_to_plot(fig, ax, theme)

    for i, (alg, color) in enumerate(zip(algorithms, colors)):
        ax.bar(
            x + (i - 1.5) * width,
            data[alg],
            width,
            label=alg,
            color=color,
            alpha=0.9,
            edgecolor=theme.border,
            linewidth=0.8,
        )

    ax.set_title("Search Algorithm Comparison: States Expanded by Scenario", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Benchmark Scenario", fontsize=10, labelpad=8)
    ax.set_ylabel("States Expanded", fontsize=10, labelpad=8)
    ax.set_xticks(x)
    ax.set_xticklabels(active_scenarios)

    legend = ax.legend(title="Algorithm", framealpha=0.9)
    if legend:
        legend.get_frame().set_facecolor(theme.surface_secondary)
        legend.get_frame().set_edgecolor(theme.border)
        legend.get_title().set_color(theme.text_secondary)
        for text in legend.get_texts():
            text.set_color(theme.text_primary)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return True


def generate_all_plots(
    results: List[ExperimentResult],
    figures_dir: str = "evaluation/figures",
    theme_mode: str = "Dark",
) -> List[str]:
    """Generate all standard evaluation plots from experiment results."""
    generated = []
    p1 = os.path.join(figures_dir, f"states_expanded_vs_tasks_{theme_mode.lower()}.png")
    # Also save standard path for backward-compatibility
    std_p1 = os.path.join(figures_dir, "states_expanded_vs_tasks.png")
    if plot_scaling_expansions(results, p1, theme_mode=theme_mode):
        plot_scaling_expansions(results, std_p1, theme_mode=theme_mode)
        generated.append(p1)

    p2 = os.path.join(figures_dir, f"runtime_vs_tasks_{theme_mode.lower()}.png")
    std_p2 = os.path.join(figures_dir, "runtime_vs_tasks.png")
    if plot_scaling_runtime(results, p2, theme_mode=theme_mode):
        plot_scaling_runtime(results, std_p2, theme_mode=theme_mode)
        generated.append(p2)

    p3 = os.path.join(figures_dir, f"algorithm_comparison_{theme_mode.lower()}.png")
    std_p3 = os.path.join(figures_dir, "algorithm_comparison.png")
    if plot_algorithm_comparison(results, p3, theme_mode=theme_mode):
        plot_algorithm_comparison(results, std_p3, theme_mode=theme_mode)
        generated.append(p3)

    return generated
