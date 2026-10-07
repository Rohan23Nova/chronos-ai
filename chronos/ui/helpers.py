"""
Presentation and execution helpers for the Chronos AI user interface.
Provides data conversions, input validation, planning execution, and report formatters
without mixing UI display logic with core AI/planning models.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar
from chronos.search.ucs import ucs
from chronos.search.bfs import bfs
from chronos.search.dfs import dfs
from chronos.knowledge import get_default_engine
from chronos.explainability.explainer import SearchTrace, explain_schedule, ScheduleExplanation
from chronos.adaptation.feedback import (
    COMPLETED_ON_TIME,
    COMPLETED_EARLY,
    POSTPONED,
    NOT_COMPLETED,
    TOO_DIFFICULT,
    TOO_EASY,
    SCHEDULE_ACCEPTABLE,
    SCHEDULE_UNACCEPTABLE,
    FeedbackRecord,
    AdaptationModel,
)


PRIORITY_MAP: Dict[str, str] = {
    "Low": "low",
    "Medium": "medium",
    "High": "high",
}

PRIORITY_REVERSE_MAP: Dict[str, str] = {v: k for k, v in PRIORITY_MAP.items()}

DIFFICULTY_MAP: Dict[str, str] = {
    "Low": "low",
    "Medium": "medium",
    "High": "high",
}

DIFFICULTY_REVERSE_MAP: Dict[str, str] = {v: k for k, v in DIFFICULTY_MAP.items()}

FEEDBACK_TYPE_MAP: Dict[str, str] = {
    "Completed on time": COMPLETED_ON_TIME,
    "Completed early": COMPLETED_EARLY,
    "Postponed": POSTPONED,
    "Not completed": NOT_COMPLETED,
    "Too difficult": TOO_DIFFICULT,
    "Too easy": TOO_EASY,
    "Schedule acceptable": SCHEDULE_ACCEPTABLE,
    "Schedule unacceptable": SCHEDULE_UNACCEPTABLE,
}

FEEDBACK_TYPE_REVERSE_MAP: Dict[str, str] = {v: k for k, v in FEEDBACK_TYPE_MAP.items()}


def validate_task_input(
    task_id: int,
    name: str,
    duration: int,
    priority: str,
    difficulty: str,
    deadline: int,
    existing_ids: Optional[Set[int]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate inputs for a new task.
    Returns (True, None) if valid, or (False, error_message).
    """
    if task_id <= 0:
        return False, "Task ID must be a positive integer greater than 0."

    if existing_ids is not None and task_id in existing_ids:
        return False, f"Task ID {task_id} already exists in the database."

    clean_name = name.strip()
    if not clean_name:
        return False, "Task name cannot be empty."

    if duration <= 0:
        return False, "Task duration must be a positive integer (>= 1)."

    if deadline <= 0:
        return False, "Task deadline must be a positive integer (>= 1)."

    if deadline < duration:
        return False, f"Deadline ({deadline}) cannot be less than duration ({duration})."

    if priority not in {"low", "medium", "high"}:
        return False, f"Invalid priority: {priority}."

    if difficulty not in {"low", "medium", "high"}:
        return False, f"Invalid difficulty: {difficulty}."

    return True, None


def execute_planning(
    tasks: List[Task],
    planning_start: int,
    available_end: int,
    algorithm: str = "A*",
    adaptation_model: Optional[AdaptationModel] = None,
    knowledge_engine: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Execute a planning search over the specified tasks and window.
    Delegates to the existing search algorithms, knowledge engine, and explainability subsystems.
    """
    if not tasks:
        raise ValueError("Cannot plan with an empty list of tasks.")

    if available_end <= planning_start:
        raise ValueError(
            f"Available end ({available_end}) must be greater than planning start ({planning_start})."
        )

    initial_state = State(
        current_time=planning_start,
        remaining_tasks=list(tasks),
        schedule=[],
        cost=0,
    )

    problem = PlanningProblem(
        initial_state=initial_state,
        planning_start=planning_start,
        available_end=available_end,
    )

    trace = SearchTrace()
    engine = knowledge_engine if knowledge_engine is not None else get_default_engine()

    result_state = None
    expanded = 0

    if algorithm == "A*":
        result_state, expanded = astar(
            problem,
            knowledge_engine=engine,
            trace=trace,
            adaptation_model=adaptation_model,
        )
    elif algorithm == "UCS":
        result_state, expanded = ucs(problem)
    elif algorithm == "BFS":
        result_state, expanded = bfs(problem)
    elif algorithm == "DFS":
        result_state, expanded = dfs(problem)
    else:
        raise ValueError(f"Unsupported planning algorithm: {algorithm}")

    explanation: ScheduleExplanation = explain_schedule(
        problem=problem,
        result_state=result_state,
        knowledge_engine=engine,
        search_trace=trace,
        tasks=tasks,
        states_expanded=expanded,
        adaptation_model=adaptation_model,
    )

    return {
        "problem": problem,
        "result_state": result_state,
        "expanded": expanded,
        "algorithm": algorithm,
        "trace": trace,
        "explanation": explanation,
        "success": result_state is not None,
    }


def format_schedule_rows(result_state: Any, tasks: List[Task]) -> List[Dict[str, Any]]:
    """Convert scheduled entries into structured rows suitable for table rendering."""
    if result_state is None or not getattr(result_state, "schedule", None):
        return []

    task_map = {t.id: t for t in tasks}
    rows = []
    for idx, entry in enumerate(result_state.schedule, start=1):
        task = task_map.get(entry.task_id)
        rows.append({
            "Order": idx,
            "Task ID": entry.task_id,
            "Name": task.name if task else f"Task #{entry.task_id}",
            "Start": entry.start_time,
            "End": entry.end_time,
            "Duration": (entry.end_time - entry.start_time),
            "Priority": task.priority.capitalize() if task else "-",
            "Difficulty": task.difficulty.capitalize() if task else "-",
            "Deadline": task.deadline if task else "-",
        })
    return rows


def format_task_rows(tasks: List[Task]) -> List[Dict[str, Any]]:
    """Convert Task objects into structured rows for table rendering."""
    return [
        {
            "ID": t.id,
            "Name": t.name,
            "Duration": t.duration,
            "Priority": t.priority.capitalize(),
            "Difficulty": t.difficulty.capitalize(),
            "Deadline": t.deadline,
        }
        for t in tasks
    ]


def format_feedback_rows(
    records: List[FeedbackRecord],
    tasks: Optional[List[Task]] = None,
) -> List[Dict[str, Any]]:
    """Convert FeedbackRecord objects into structured rows for table rendering."""
    task_map = {t.id: t.name for t in tasks} if tasks else {}
    rows = []
    for r in records:
        readable_type = FEEDBACK_TYPE_REVERSE_MAP.get(r.feedback_type, r.feedback_type)
        rows.append({
            "Task ID": r.task_id,
            "Task Name": task_map.get(r.task_id, f"Task #{r.task_id}"),
            "Feedback Type": readable_type,
            "Rating": r.rating if r.rating is not None else "-",
            "Comment": r.comment if r.comment else "-",
        })
    return rows
