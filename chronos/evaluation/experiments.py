"""
Controlled evaluation experiments for Chronos AI planning agent.
All metrics are measured from actual executions; no numbers are fabricated or hardcoded.
"""

import os
import time
from typing import Any, Dict, List, Optional

from chronos.models.state import State
from chronos.models.task import Task
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar
from chronos.search.ucs import ucs
from chronos.search.bfs import bfs
from chronos.search.dfs import dfs
from chronos.knowledge import get_default_engine
from chronos.adaptation.feedback import (
    FeedbackRecord,
    AdaptationModel,
    POSTPONED,
    TOO_DIFFICULT,
    NOT_COMPLETED,
    COMPLETED_ON_TIME,
)
from chronos.explainability.explainer import SearchTrace
from chronos.constraints.checker import explain_feasibility
from chronos.evaluation.metrics import (
    ExperimentResult,
    results_to_csv,
    results_to_json,
)
from chronos.evaluation.scenarios import (
    BenchmarkScenario,
    get_canonical_scenario,
    get_small_scenario,
    get_medium_scenario,
    get_larger_scenario,
    get_infeasible_scenario,
    get_scaling_scenarios,
    get_all_benchmark_scenarios,
)
from chronos.evaluation.plots import generate_all_plots


DEFAULT_RESULTS_DIR = "evaluation/results"
DEFAULT_FIGURES_DIR = "evaluation/figures"


def _solve(
    problem: PlanningProblem,
    algorithm: str,
    knowledge_engine: Optional[Any] = None,
    adaptation_model: Optional[AdaptationModel] = None,
    trace: Optional[SearchTrace] = None,
) -> tuple[Optional[State], int, float]:
    """
    Execute specified search algorithm and record elapsed time in milliseconds.
    """
    start_time = time.perf_counter()

    if algorithm == "A*":
        result_state, expanded = astar(
            problem,
            knowledge_engine=knowledge_engine,
            adaptation_model=adaptation_model,
            trace=trace,
        )
    elif algorithm == "UCS":
        result_state, expanded = ucs(problem)
    elif algorithm == "BFS":
        result_state, expanded = bfs(problem)
    elif algorithm == "DFS":
        result_state, expanded = dfs(problem)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return result_state, expanded, elapsed_ms


# ===========================================================================
# Experiment 1: Algorithm Comparison
# ===========================================================================

def run_algorithm_comparison(
    scenarios: Optional[List[BenchmarkScenario]] = None,
) -> List[ExperimentResult]:
    """
    Evaluate BFS, DFS, UCS, and A* across deterministic benchmark scenarios.
    """
    if scenarios is None:
        scenarios = [
            get_canonical_scenario(),
            get_small_scenario(),
            get_medium_scenario(),
            get_larger_scenario(),
            get_infeasible_scenario(),
        ]

    algorithms = ["A*", "UCS", "BFS", "DFS"]
    results: List[ExperimentResult] = []

    for scenario in scenarios:
        for alg in algorithms:
            initial_state = State(
                current_time=scenario.planning_start,
                remaining_tasks=list(scenario.tasks),
                schedule=[],
                cost=0,
            )
            problem = PlanningProblem(
                initial_state=initial_state,
                planning_start=scenario.planning_start,
                available_end=scenario.available_end,
            )

            result_state, expanded, runtime_ms = _solve(problem, alg)
            found = result_state is not None
            cost = result_state.cost if found else None
            order = [e.task_id for e in result_state.schedule] if found else None

            results.append(
                ExperimentResult(
                    experiment_name="algorithm_comparison",
                    scenario=scenario.name,
                    algorithm=alg,
                    task_count=scenario.task_count,
                    solution_found=found,
                    final_cost=cost,
                    states_expanded=expanded,
                    runtime_ms=round(runtime_ms, 3),
                    schedule_order=order,
                    notes=f"Window: [{scenario.planning_start}, {scenario.available_end}]",
                )
            )

    return results


# ===========================================================================
# Experiment 2: Knowledge-Aware Heuristic
# ===========================================================================

def run_knowledge_heuristic_experiment(
    scenarios: Optional[List[BenchmarkScenario]] = None,
) -> List[ExperimentResult]:
    """
    Compare A* with knowledge-aware heuristic enabled vs disabled.
    Demonstrates the actual effect of symbolic forward-chaining rules on search guidance.
    """
    if scenarios is None:
        scenarios = [
            get_canonical_scenario(),
            get_small_scenario(),
            get_medium_scenario(),
        ]

    results: List[ExperimentResult] = []
    default_engine = get_default_engine()

    for scenario in scenarios:
        for kn_enabled in [True, False]:
            initial_state = State(
                current_time=scenario.planning_start,
                remaining_tasks=list(scenario.tasks),
                schedule=[],
                cost=0,
            )
            problem = PlanningProblem(
                initial_state=initial_state,
                planning_start=scenario.planning_start,
                available_end=scenario.available_end,
            )

            engine_arg = default_engine if kn_enabled else False
            result_state, expanded, runtime_ms = _solve(
                problem,
                algorithm="A*",
                knowledge_engine=engine_arg,
            )

            found = result_state is not None
            cost = result_state.cost if found else None
            order = [e.task_id for e in result_state.schedule] if found else None
            variant_name = "A* (Knowledge Enabled)" if kn_enabled else "A* (Knowledge Disabled)"

            results.append(
                ExperimentResult(
                    experiment_name="knowledge_heuristic",
                    scenario=scenario.name,
                    algorithm=variant_name,
                    task_count=scenario.task_count,
                    solution_found=found,
                    final_cost=cost,
                    states_expanded=expanded,
                    runtime_ms=round(runtime_ms, 3),
                    schedule_order=order,
                    notes=(
                        "Rules fired: urgency, risk, deadline_pressure, attention"
                        if kn_enabled
                        else "No symbolic rules; pure workload/urgency heuristic"
                    ),
                )
            )

    return results


# ===========================================================================
# Experiment 3: Adaptation Feedback
# ===========================================================================

def run_adaptation_experiment() -> List[ExperimentResult]:
    """
    Demonstrate the empirical effect of user feedback records on A* search.
    Compares baseline A* with A* under learned task adaptation adjustments.
    """
    scenario = get_canonical_scenario()
    results: List[ExperimentResult] = []

    # 1. Baseline: No prior feedback
    initial_state_1 = State(
        current_time=scenario.planning_start,
        remaining_tasks=list(scenario.tasks),
        schedule=[],
        cost=0,
    )
    problem_1 = PlanningProblem(
        initial_state=initial_state_1,
        planning_start=scenario.planning_start,
        available_end=scenario.available_end,
    )

    baseline_state, baseline_exp, baseline_time = _solve(problem_1, "A*")
    found_1 = baseline_state is not None
    cost_1 = baseline_state.cost if found_1 else None
    order_1 = [e.task_id for e in baseline_state.schedule] if found_1 else None

    results.append(
        ExperimentResult(
            experiment_name="adaptation_experiment",
            scenario=scenario.name,
            algorithm="A* (Baseline / No Feedback)",
            task_count=scenario.task_count,
            solution_found=found_1,
            final_cost=cost_1,
            states_expanded=baseline_exp,
            runtime_ms=round(baseline_time, 3),
            schedule_order=order_1,
            notes="Neutral adaptation profiles (all adjustments 0.0)",
        )
    )

    # 2. Adapted: Apply feedback to Task 1 (DSA) and Task 2 (AI)
    # Task 1 was repeatedly postponed; Task 2 was marked too difficult
    adapted_model = AdaptationModel()
    adapted_model.record_feedback(task_id=1, feedback_type=POSTPONED)
    adapted_model.record_feedback(task_id=1, feedback_type=POSTPONED)
    adapted_model.record_feedback(task_id=1, feedback_type=NOT_COMPLETED)
    adapted_model.record_feedback(task_id=2, feedback_type=TOO_DIFFICULT)

    prof_1 = adapted_model.get_task_profile(1)
    prof_2 = adapted_model.get_task_profile(2)

    initial_state_2 = State(
        current_time=scenario.planning_start,
        remaining_tasks=list(scenario.tasks),
        schedule=[],
        cost=0,
    )
    problem_2 = PlanningProblem(
        initial_state=initial_state_2,
        planning_start=scenario.planning_start,
        available_end=scenario.available_end,
    )

    adapted_state, adapted_exp, adapted_time = _solve(
        problem_2,
        "A*",
        adaptation_model=adapted_model,
    )
    found_2 = adapted_state is not None
    cost_2 = adapted_state.cost if found_2 else None
    order_2 = [e.task_id for e in adapted_state.schedule] if found_2 else None

    results.append(
        ExperimentResult(
            experiment_name="adaptation_experiment",
            scenario=scenario.name,
            algorithm="A* (Feedback Adapted)",
            task_count=scenario.task_count,
            solution_found=found_2,
            final_cost=cost_2,
            states_expanded=adapted_exp,
            runtime_ms=round(adapted_time, 3),
            schedule_order=order_2,
            notes=(
                f"Task 1 adj: {prof_1.net_adjustment:+.2f} (postponed/uncompleted); "
                f"Task 2 adj: {prof_2.net_adjustment:+.2f} (too difficult)"
            ),
        )
    )

    return results


# ===========================================================================
# Experiment 4: Constraint Handling
# ===========================================================================

def run_constraint_experiment() -> List[ExperimentResult]:
    """
    Evaluate constraint enforcement on feasible vs infeasible scenarios.
    Verifies that hard deadlines and planning horizons properly prune invalid actions.
    """
    scenarios = [
        get_canonical_scenario(),
        get_infeasible_scenario(),
    ]
    results: List[ExperimentResult] = []

    for scenario in scenarios:
        initial_state = State(
            current_time=scenario.planning_start,
            remaining_tasks=list(scenario.tasks),
            schedule=[],
            cost=0,
        )
        problem = PlanningProblem(
            initial_state=initial_state,
            planning_start=scenario.planning_start,
            available_end=scenario.available_end,
        )

        trace = SearchTrace()
        result_state, expanded, runtime_ms = _solve(
            problem,
            "A*",
            trace=trace,
        )
        found = result_state is not None
        cost = result_state.cost if found else None
        order = [e.task_id for e in result_state.schedule] if found else None

        # Gather diagnostic notes
        pruned_count = len(trace.rejected_candidates)
        notes = (
            f"Feasible schedule found within [{scenario.planning_start}, {scenario.available_end}]"
            if found
            else f"Correctly pruned all paths ({pruned_count} candidate rejections)"
        )

        results.append(
            ExperimentResult(
                experiment_name="constraint_handling",
                scenario=scenario.name,
                algorithm="A*",
                task_count=scenario.task_count,
                solution_found=found,
                final_cost=cost,
                states_expanded=expanded,
                runtime_ms=round(runtime_ms, 3),
                schedule_order=order,
                notes=notes,
            )
        )

    return results


# ===========================================================================
# Experiment 5: Scaling with Increasing Task Counts
# ===========================================================================

def run_scaling_experiment(
    scaling_scenarios: Optional[List[BenchmarkScenario]] = None,
) -> List[ExperimentResult]:
    """
    Evaluate A* search performance scaling across increasing task counts (3 to 8 tasks).
    """
    if scaling_scenarios is None:
        scaling_scenarios = get_scaling_scenarios()

    results: List[ExperimentResult] = []

    for scenario in scaling_scenarios:
        initial_state = State(
            current_time=scenario.planning_start,
            remaining_tasks=list(scenario.tasks),
            schedule=[],
            cost=0,
        )
        problem = PlanningProblem(
            initial_state=initial_state,
            planning_start=scenario.planning_start,
            available_end=scenario.available_end,
        )

        result_state, expanded, runtime_ms = _solve(problem, "A*")
        found = result_state is not None
        cost = result_state.cost if found else None
        order = [e.task_id for e in result_state.schedule] if found else None

        results.append(
            ExperimentResult(
                experiment_name="scaling_experiment",
                scenario=scenario.name,
                algorithm="A*",
                task_count=scenario.task_count,
                solution_found=found,
                final_cost=cost,
                states_expanded=expanded,
                runtime_ms=round(runtime_ms, 3),
                schedule_order=order,
                notes=f"Window: [{scenario.planning_start}, {scenario.available_end}]",
            )
        )

    return results


# ===========================================================================
# Suite Runner & Report Output
# ===========================================================================

def run_all_experiments(
    save_results: bool = True,
    generate_figures: bool = True,
    results_dir: str = DEFAULT_RESULTS_DIR,
    figures_dir: str = DEFAULT_FIGURES_DIR,
) -> List[ExperimentResult]:
    """
    Execute all 5 evaluation experiments and optionally serialize results and plots.
    """
    all_results: List[ExperimentResult] = []

    # 1. Algorithm comparison
    all_results.extend(run_algorithm_comparison())

    # 2. Knowledge-aware heuristic
    all_results.extend(run_knowledge_heuristic_experiment())

    # 3. Adaptation feedback
    all_results.extend(run_adaptation_experiment())

    # 4. Constraint handling
    all_results.extend(run_constraint_experiment())

    # 5. Scaling
    all_results.extend(run_scaling_experiment())

    if save_results:
        json_path = os.path.join(results_dir, "benchmark_results.json")
        csv_path = os.path.join(results_dir, "benchmark_results.csv")
        results_to_json(all_results, json_path)
        results_to_csv(all_results, csv_path)

    if generate_figures:
        generate_all_plots(all_results, figures_dir=figures_dir)

    return all_results


def print_summary_tables(results: List[ExperimentResult]) -> None:
    """Print readable ASCII summary tables for each evaluation experiment."""
    experiments = [
        ("algorithm_comparison", "EXPERIMENT 1: ALGORITHM COMPARISON"),
        ("knowledge_heuristic", "EXPERIMENT 2: KNOWLEDGE-AWARE HEURISTIC IMPACT"),
        ("adaptation_experiment", "EXPERIMENT 3: FEEDBACK-BASED ADAPTATION"),
        ("constraint_handling", "EXPERIMENT 4: HARD CONSTRAINT ENFORCEMENT"),
        ("scaling_experiment", "EXPERIMENT 5: SCALING WITH INCREASING TASK COUNTS"),
    ]

    for exp_id, exp_title in experiments:
        sub = [r for r in results if r.experiment_name == exp_id]
        if not sub:
            continue

        print("\n" + "=" * 95)
        print(f" {exp_title}")
        print("=" * 95)
        print(
            f"{'Scenario':<24} | {'Algorithm':<26} | {'Tasks':<5} | {'Solved':<6} | "
            f"{'Cost':<6} | {'Expanded':<8} | {'Time (ms)':<9} | {'Order'}"
        )
        print("-" * 95)

        for r in sub:
            cost_str = f"{r.final_cost:.1f}" if r.final_cost is not None else "-"
            solved_str = "Yes" if r.solution_found else "No"
            order_str = str(r.schedule_order) if r.schedule_order else "-"
            print(
                f"{r.scenario:<24} | {r.algorithm:<26} | {r.task_count:<5} | {solved_str:<6} | "
                f"{cost_str:<6} | {r.states_expanded:<8} | {r.runtime_ms:<9.2f} | {order_str}"
            )

        print("-" * 95)


def main():
    """CLI entry point: run all benchmark experiments and output report."""
    print("================================================================================")
    print(" CHRONOS AI: CONTROLLED PLANNING EVALUATION SUITE")
    print("================================================================================")
    print("Executing benchmark experiments across search algorithms, domain rules,")
    print("adaptation feedback, constraint pruning, and problem scaling...\n")

    results = run_all_experiments(save_results=True, generate_figures=True)
    print_summary_tables(results)

    print("\nBenchmark results saved to:")
    print(f" - {DEFAULT_RESULTS_DIR}/benchmark_results.json")
    print(f" - {DEFAULT_RESULTS_DIR}/benchmark_results.csv")
    print("Figures generated in:")
    print(f" - {DEFAULT_FIGURES_DIR}/")
    print("Evaluation completed successfully.")


if __name__ == "__main__":
    main()
