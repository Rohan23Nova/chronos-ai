"""
Plot generation utilities for Chronos AI evaluation experiments.
Produces clean, legible figures representing measured experiment data without decorative fluff.
"""

import os
import tempfile
from typing import List

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


def plot_scaling_expansions(results: List[ExperimentResult], output_path: str) -> bool:
    """Plot States Expanded vs Task Count for the scaling experiment."""
    if not MATPLOTLIB_AVAILABLE:
        return False

    scaling_results = [r for r in results if r.experiment_name == "scaling_experiment"]
    if not scaling_results:
        return False

    scaling_results.sort(key=lambda r: r.task_count)
    task_counts = [r.task_count for r in scaling_results]
    expansions = [r.states_expanded for r in scaling_results]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(7, 4.5))
    plt.plot(task_counts, expansions, marker="o", color="#2563EB", linewidth=2, markersize=6)
    plt.title("A* Search: States Expanded vs Task Count", fontsize=12, fontweight="bold")
    plt.xlabel("Number of Tasks (n)", fontsize=10)
    plt.ylabel("States Expanded", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    return True


def plot_scaling_runtime(results: List[ExperimentResult], output_path: str) -> bool:
    """Plot Runtime (ms) vs Task Count for the scaling experiment."""
    if not MATPLOTLIB_AVAILABLE:
        return False

    scaling_results = [r for r in results if r.experiment_name == "scaling_experiment"]
    if not scaling_results:
        return False

    scaling_results.sort(key=lambda r: r.task_count)
    task_counts = [r.task_count for r in scaling_results]
    runtimes = [r.runtime_ms for r in scaling_results]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(7, 4.5))
    plt.plot(task_counts, runtimes, marker="s", color="#D97706", linewidth=2, markersize=6)
    plt.title("A* Search: Runtime (ms) vs Task Count", fontsize=12, fontweight="bold")
    plt.xlabel("Number of Tasks (n)", fontsize=10)
    plt.ylabel("Runtime (milliseconds)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    return True


def plot_algorithm_comparison(results: List[ExperimentResult], output_path: str) -> bool:
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

    # Filter available scenarios
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

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(8.5, 5))
    colors = ["#2563EB", "#059669", "#7C3AED", "#DC2626"]

    for i, (alg, color) in enumerate(zip(algorithms, colors)):
        plt.bar(x + (i - 1.5) * width, data[alg], width, label=alg, color=color, alpha=0.9)

    plt.title("Search Algorithm Comparison: States Expanded by Scenario", fontsize=12, fontweight="bold")
    plt.xlabel("Benchmark Scenario", fontsize=10)
    plt.ylabel("States Expanded", fontsize=10)
    plt.xticks(x, active_scenarios)
    plt.legend(title="Algorithm")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    return True


def generate_all_plots(results: List[ExperimentResult], figures_dir: str = "evaluation/figures") -> List[str]:
    """Generate all standard evaluation plots from experiment results."""
    generated = []
    p1 = os.path.join(figures_dir, "states_expanded_vs_tasks.png")
    if plot_scaling_expansions(results, p1):
        generated.append(p1)

    p2 = os.path.join(figures_dir, "runtime_vs_tasks.png")
    if plot_scaling_runtime(results, p2):
        generated.append(p2)

    p3 = os.path.join(figures_dir, "algorithm_comparison.png")
    if plot_algorithm_comparison(results, p3):
        generated.append(p3)

    return generated
