"""
Deterministic benchmark scenario definitions for Chronos AI evaluation experiments.
All scenarios are synthetic, deterministic, and reproducible.
"""

from dataclasses import dataclass
from typing import Dict, List

from chronos.models.task import Task


@dataclass(frozen=True)
class BenchmarkScenario:
    """
    Specification of a reproducible scheduling problem scenario.
    """
    name: str
    description: str
    tasks: List[Task]
    planning_start: int
    available_end: int
    expected_feasible: bool = True

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def total_duration(self) -> int:
        return sum(t.duration for t in self.tasks)

    @property
    def window_size(self) -> int:
        return self.available_end - self.planning_start


def get_canonical_scenario() -> BenchmarkScenario:
    """Scenario A: Canonical 3-task problem (DSA, AI, DBMS)."""
    return BenchmarkScenario(
        name="Canonical (3 tasks)",
        description="Canonical benchmark problem with DSA (2h), AI (3h), and DBMS (1h).",
        tasks=[
            Task(id=1, name="DSA", duration=2, priority="high", deadline=24, difficulty="high"),
            Task(id=2, name="AI", duration=3, priority="medium", deadline=72, difficulty="high"),
            Task(id=3, name="DBMS", duration=1, priority="medium", deadline=48, difficulty="medium"),
        ],
        planning_start=18,
        available_end=24,
        expected_feasible=True,
    )


def get_small_scenario() -> BenchmarkScenario:
    """Scenario B: Small 4-task problem with competing deadlines and priorities."""
    return BenchmarkScenario(
        name="Small (4 tasks)",
        description="4 tasks with distinct priorities, durations, and tight early deadlines.",
        tasks=[
            Task(id=1, name="OS Assignment", duration=2, priority="high", deadline=22, difficulty="high"),
            Task(id=2, name="Math Problem Set", duration=1, priority="high", deadline=21, difficulty="medium"),
            Task(id=3, name="Web Dev Project", duration=2, priority="medium", deadline=26, difficulty="medium"),
            Task(id=4, name="Ethics Essay", duration=1, priority="low", deadline=26, difficulty="low"),
        ],
        planning_start=18,
        available_end=26,
        expected_feasible=True,
    )


def get_medium_scenario() -> BenchmarkScenario:
    """Scenario C: Medium 6-task problem."""
    return BenchmarkScenario(
        name="Medium (6 tasks)",
        description="6 tasks testing trade-offs between urgent high-priority and larger low-priority tasks.",
        tasks=[
            Task(id=1, name="Algorithms", duration=2, priority="high", deadline=24, difficulty="high"),
            Task(id=2, name="Database Lab", duration=1, priority="high", deadline=22, difficulty="medium"),
            Task(id=3, name="Networks Quiz", duration=2, priority="medium", deadline=28, difficulty="high"),
            Task(id=4, name="Software Eng", duration=2, priority="medium", deadline=30, difficulty="medium"),
            Task(id=5, name="AI Reading", duration=1, priority="low", deadline=30, difficulty="low"),
            Task(id=6, name="Code Review", duration=1, priority="low", deadline=30, difficulty="low"),
        ],
        planning_start=18,
        available_end=30,
        expected_feasible=True,
    )


def get_larger_scenario() -> BenchmarkScenario:
    """Scenario D: Larger 8-task problem."""
    return BenchmarkScenario(
        name="Larger (8 tasks)",
        description="8 tasks with varied deadlines, multiple high-difficulty and multi-priority items.",
        tasks=[
            Task(id=1, name="Compiler Project", duration=3, priority="high", deadline=28, difficulty="high"),
            Task(id=2, name="Security Lab", duration=2, priority="high", deadline=26, difficulty="high"),
            Task(id=3, name="Data Mining Prep", duration=2, priority="medium", deadline=32, difficulty="medium"),
            Task(id=4, name="Cloud Architecture", duration=2, priority="medium", deadline=34, difficulty="medium"),
            Task(id=5, name="Linear Algebra", duration=2, priority="medium", deadline=36, difficulty="medium"),
            Task(id=6, name="Seminar Slides", duration=1, priority="low", deadline=38, difficulty="low"),
            Task(id=7, name="Documentation", duration=1, priority="low", deadline=40, difficulty="low"),
            Task(id=8, name="Bug Fixes", duration=1, priority="low", deadline=40, difficulty="low"),
        ],
        planning_start=18,
        available_end=36,
        expected_feasible=True,
    )


def get_infeasible_scenario() -> BenchmarkScenario:
    """Deliberately infeasible scenario violating deadline and available time constraints."""
    return BenchmarkScenario(
        name="Infeasible (3 tasks)",
        description="Deliberately overconstrained scenario where total duration (8h) exceeds window (4h).",
        tasks=[
            Task(id=1, name="Overconstrained Task A", duration=3, priority="high", deadline=20, difficulty="high"),
            Task(id=2, name="Overconstrained Task B", duration=3, priority="medium", deadline=21, difficulty="high"),
            Task(id=3, name="Overconstrained Task C", duration=2, priority="low", deadline=21, difficulty="medium"),
        ],
        planning_start=18,
        available_end=22,
        expected_feasible=False,
    )


def get_scaling_scenarios() -> List[BenchmarkScenario]:
    """
    Generate deterministic benchmark scenarios of sizes 3, 4, 5, 6, 7, and 8 tasks.
    """
    task_pool = [
        Task(id=1, name="Algorithm Practice", duration=2, priority="high", deadline=26, difficulty="high"),
        Task(id=2, name="System Design", duration=1, priority="high", deadline=24, difficulty="medium"),
        Task(id=3, name="Database Tuning", duration=3, priority="medium", deadline=32, difficulty="high"),
        Task(id=4, name="Network Simulation", duration=2, priority="medium", deadline=34, difficulty="medium"),
        Task(id=5, name="ML Pipeline", duration=2, priority="medium", deadline=36, difficulty="medium"),
        Task(id=6, name="Unit Testing", duration=1, priority="low", deadline=40, difficulty="low"),
        Task(id=7, name="Code Cleanup", duration=2, priority="low", deadline=42, difficulty="low"),
        Task(id=8, name="Tech Writing", duration=2, priority="low", deadline=46, difficulty="low"),
    ]

    scenarios = []
    for count in range(3, 9):
        subset = [
            Task(
                id=t.id,
                name=t.name,
                duration=t.duration,
                priority=t.priority,
                deadline=t.deadline,
                difficulty=t.difficulty,
            )
            for t in task_pool[:count]
        ]
        total_dur = sum(t.duration for t in subset)
        scenarios.append(
            BenchmarkScenario(
                name=f"Scaling ({count} tasks)",
                description=f"Scaling test with {count} tasks (total duration {total_dur}h).",
                tasks=subset,
                planning_start=18,
                available_end=18 + total_dur + 6,
                expected_feasible=True,
            )
        )
    return scenarios


def get_all_benchmark_scenarios() -> Dict[str, BenchmarkScenario]:
    """Return dictionary of all primary named benchmark scenarios."""
    return {
        "canonical": get_canonical_scenario(),
        "small": get_small_scenario(),
        "medium": get_medium_scenario(),
        "larger": get_larger_scenario(),
        "infeasible": get_infeasible_scenario(),
    }
