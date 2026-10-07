from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from chronos.models.task import Task
from chronos.models.schedule import ScheduleEntry
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem, priority_weight, task_cost
from chronos.constraints.checker import explain_feasibility
from chronos.knowledge import Fact, RuleEngine, get_default_engine, task_to_facts


@dataclass
class CandidateEvaluation:
    """
    Feasibility and constraint evaluation for a candidate task at a given start time.
    """
    task_id: int
    task_name: str
    start_time: int
    end_time: int
    duration: int
    deadline: int
    available_end: int
    fits_window: bool
    meets_deadline: bool
    feasible: bool
    reasons: List[str]


@dataclass
class TraceStep:
    """
    Lightweight record of a single candidate evaluation step during search.
    """
    state_current_time: int
    candidate_task_id: int
    candidate_task_name: str
    accepted: bool
    reasons: List[str]
    cost: Optional[float] = None
    heuristic_val: Optional[float] = None


class SearchTrace:
    """
    Lightweight search trace recorder for state expansions and candidate decisions.
    """
    def __init__(self):
        self.expansions: int = 0
        self.steps: List[TraceStep] = []
        self.rejected_candidates: List[TraceStep] = []

    def record_expansion(self, state: Any) -> None:
        self.expansions += 1

    def record_candidate(
        self,
        task: Any,
        start_time: int,
        accepted: bool,
        reasons: List[str],
        cost: Optional[float] = None,
        heuristic_val: Optional[float] = None,
    ) -> None:
        step = TraceStep(
            state_current_time=start_time,
            candidate_task_id=task.id,
            candidate_task_name=task.name,
            accepted=accepted,
            reasons=list(reasons),
            cost=cost,
            heuristic_val=heuristic_val,
        )
        self.steps.append(step)
        if not accepted:
            self.rejected_candidates.append(step)


@dataclass
class TaskExplanation:
    """
    Structured explanation for a single scheduled task.
    """
    task_id: int
    task_name: str
    start_time: int
    end_time: int
    duration: int
    priority: str
    deadline: int
    difficulty: str
    waiting_time: int
    cost_contribution: float
    accumulated_cost: float
    derived_facts: List[Fact]
    constraint_status: str
    reasons: List[str]


@dataclass
class OrderingExplanation:
    """
    Structured pairwise ordering explanation between two scheduled tasks.
    """
    preceding_task_id: int
    preceding_task_name: str
    following_task_id: int
    following_task_name: str
    reasons: List[str]


@dataclass
class ScheduleExplanation:
    """
    Complete explanation model for a scheduled plan.
    """
    problem_summary: str
    task_explanations: List[TaskExplanation]
    ordering_explanations: List[OrderingExplanation]
    rejected_candidates: List[CandidateEvaluation]
    total_cost: float
    planning_start: int
    available_end: int
    states_expanded: Optional[int] = None

    def to_text(self) -> str:
        """
        Render a structured, human-readable explanation report.
        """
        lines = []
        lines.append("-" * 50)
        lines.append("CHRONOS PLAN EXPLANATION")
        lines.append("-" * 50)
        lines.append("")
        lines.append("Overall:")
        lines.append(f"{self.problem_summary}")
        lines.append("")

        for te in self.task_explanations:
            lines.append(f"{te.task_name}: {te.start_time}-{te.end_time}")
            lines.append(f"- Duration: {te.duration}")
            lines.append(f"- Priority: {te.priority}")
            lines.append(f"- Deadline: {te.deadline}")
            lines.append(f"- Difficulty: {te.difficulty}")
            lines.append(f"- Waiting time: {te.waiting_time} (cost: {te.cost_contribution})")
            lines.append(f"- Constraint status: {te.constraint_status}")

            fact_strs = [f"{f.predicate}={f.value}" for f in te.derived_facts]
            if fact_strs:
                lines.append(f"- Derived facts: {', '.join(fact_strs)}")
            else:
                lines.append("- Derived facts: none")

            lines.append("- Scheduling reasons:")
            for r in te.reasons:
                lines.append(f"  * {r}")
            lines.append("")

        if self.ordering_explanations:
            lines.append("Task Ordering Decisions:")
            for oe in self.ordering_explanations:
                lines.append(f"- {oe.preceding_task_name} before {oe.following_task_name}:")
                for r in oe.reasons:
                    lines.append(f"  * {r}")
            lines.append("")

        if self.rejected_candidates:
            lines.append("Candidate Pruning / Constraint Rejections:")
            for rc in self.rejected_candidates:
                lines.append(f"- {rc.task_name} at time {rc.start_time} (finish {rc.end_time}):")
                for r in rc.reasons:
                    lines.append(f"  * {r}")
            lines.append("")

        lines.append(f"Final cost: {self.total_cost}")
        if self.states_expanded is not None:
            lines.append(f"States expanded: {self.states_expanded}")
        lines.append("-" * 50)
        return "\n".join(lines)


def evaluate_candidate(task: Task, start_time: int, available_end: int) -> CandidateEvaluation:
    """
    Evaluate feasibility of a candidate task at a start time using the constraint system.
    """
    diag = explain_feasibility(task, start_time, available_end)
    return CandidateEvaluation(
        task_id=diag["task_id"],
        task_name=diag["task_name"],
        start_time=diag["start_time"],
        end_time=diag["end_time"],
        duration=diag["duration"],
        deadline=diag["deadline"],
        available_end=diag["available_end"],
        fits_window=diag["fits_window"],
        meets_deadline=diag["meets_deadline"],
        feasible=diag["feasible"],
        reasons=diag["reasons"],
    )


def explain_task_ordering(
    task_a: Task,
    entry_a: ScheduleEntry,
    task_b: Task,
    entry_b: ScheduleEntry,
    planning_start: int,
    available_end: int,
    engine: Optional[RuleEngine] = None,
) -> OrderingExplanation:
    """
    Explain why task_a was scheduled before task_b using actual task properties,
    knowledge-derived facts, delay costs, and constraints.
    """
    reasons: List[str] = []

    # 1. Priority comparison
    weight_a = priority_weight(task_a.priority)
    weight_b = priority_weight(task_b.priority)
    if weight_a > weight_b:
        reasons.append(
            f"{task_a.name} has higher priority ({task_a.priority}) than {task_b.name} ({task_b.priority})."
        )

    # 2. Deadline comparison
    if task_a.deadline < task_b.deadline:
        reasons.append(
            f"{task_a.name} has an earlier deadline ({task_a.deadline}) than {task_b.name} ({task_b.deadline})."
        )

    # 3. Knowledge-derived facts comparison
    if engine is not None:
        facts_a = engine.infer(task_a, current_time=planning_start)
        facts_b = engine.infer(task_b, current_time=planning_start)

        urg_a = engine.get_fact_value(facts_a, "urgency", task_a.id)
        urg_b = engine.get_fact_value(facts_b, "urgency", task_b.id)
        urgency_levels = {"high": 3, "medium": 2, "low": 1}
        val_a = urgency_levels.get(urg_a, 0)
        val_b = urgency_levels.get(urg_b, 0)
        if val_a > val_b:
            if urg_b:
                reasons.append(
                    f"{task_a.name} has higher urgency ({urg_a}) than {task_b.name} ({urg_b})."
                )
            else:
                reasons.append(
                    f"{task_a.name} has higher urgency ({urg_a}) than {task_b.name}."
                )

        dp_a = engine.get_fact_value(facts_a, "deadline_pressure", task_a.id)
        dp_b = engine.get_fact_value(facts_b, "deadline_pressure", task_b.id)
        if dp_a == "high" and dp_b != "high":
            reasons.append(
                f"{task_a.name} has high deadline pressure, whereas {task_b.name} does not."
            )

        att_a = engine.get_fact_value(facts_a, "attention", task_a.id)
        att_b = engine.get_fact_value(facts_b, "attention", task_b.id)
        if att_a == "immediate" and att_b != "immediate":
            reasons.append(
                f"{task_a.name} requires immediate attention due to combined high urgency and deadline pressure."
            )

        risk_a = engine.get_fact_value(facts_a, "risk", task_a.id)
        risk_b = engine.get_fact_value(facts_b, "risk", task_b.id)
        risk_levels = {"high": 3, "medium": 2, "low": 1}
        if risk_a and risk_b and risk_levels.get(risk_a, 0) > risk_levels.get(risk_b, 0):
            reasons.append(
                f"{task_a.name} has higher risk ({risk_a}) than {task_b.name} ({risk_b})."
            )

    # 4. Mutual delay penalty and duration comparison
    cost_if_a_then_b = weight_b * task_a.duration
    cost_if_b_then_a = weight_a * task_b.duration
    if cost_if_a_then_b < cost_if_b_then_a:
        reasons.append(
            f"Scheduling {task_a.name} before {task_b.name} minimizes mutual delay penalty "
            f"({cost_if_a_then_b} vs {cost_if_b_then_a})."
        )

    if task_a.duration < task_b.duration:
        reasons.append(
            f"{task_a.name} has shorter duration ({task_a.duration} vs {task_b.duration}), "
            f"freeing the schedule earlier for subsequent tasks."
        )

    # 5. Feasibility of alternative placement
    end_b_first = entry_a.start_time + task_b.duration
    end_a_after = end_b_first + task_a.duration
    if end_a_after > task_a.deadline:
        reasons.append(
            f"Scheduling {task_b.name} first would push {task_a.name} past its deadline ({task_a.deadline})."
        )
    if end_a_after > available_end:
        reasons.append(
            f"Scheduling {task_b.name} first would push {task_a.name} past the planning horizon ({available_end})."
        )

    if not reasons:
        reasons.append(
            f"Both tasks are feasible; scheduling {task_a.name} at {entry_a.start_time} "
            f"yielded lower cumulative path cost."
        )

    return OrderingExplanation(
        preceding_task_id=task_a.id,
        preceding_task_name=task_a.name,
        following_task_id=task_b.id,
        following_task_name=task_b.name,
        reasons=reasons,
    )


def explain_schedule(
    problem: PlanningProblem,
    result_state: State,
    knowledge_engine: Optional[RuleEngine] = None,
    search_trace: Optional[SearchTrace] = None,
    tasks: Optional[List[Task]] = None,
    states_expanded: Optional[int] = None,
) -> ScheduleExplanation:
    """
    Generate a complete, verifiable explanation for a final schedule.
    """
    if knowledge_engine is None:
        knowledge_engine = get_default_engine()

    # Resolve task catalogue
    if tasks is not None:
        task_map = {t.id: t for t in tasks}
    elif hasattr(problem, "initial_state") and hasattr(problem.initial_state, "remaining_tasks"):
        task_map = {t.id: t for t in problem.initial_state.remaining_tasks}
    else:
        task_map = {}

    planning_start = getattr(problem, "planning_start", 18)
    available_end = getattr(problem, "available_end", 24)

    if result_state is None:
        rejected_candidates: List[CandidateEvaluation] = []
        if search_trace is not None and search_trace.rejected_candidates:
            for step in search_trace.rejected_candidates:
                task = task_map.get(step.candidate_task_id)
                if task:
                    diag = explain_feasibility(task, step.state_current_time, available_end)
                    rejected_candidates.append(
                        CandidateEvaluation(
                            task_id=task.id,
                            task_name=task.name,
                            start_time=step.state_current_time,
                            end_time=step.state_current_time + task.duration,
                            duration=task.duration,
                            deadline=task.deadline,
                            available_end=available_end,
                            fits_window=diag["fits_window"],
                            meets_deadline=diag["meets_deadline"],
                            feasible=diag["feasible"],
                            reasons=step.reasons,
                        )
                    )

        summary = (
            f"No feasible schedule found. All candidate planning paths were pruned "
            f"or violated hard constraints within horizon [{planning_start}, {available_end}]."
        )
        if states_expanded is None and search_trace is not None:
            states_expanded = search_trace.expansions

        return ScheduleExplanation(
            problem_summary=summary,
            task_explanations=[],
            ordering_explanations=[],
            rejected_candidates=rejected_candidates,
            total_cost=float("inf"),
            planning_start=planning_start,
            available_end=available_end,
            states_expanded=states_expanded,
        )

    # Task-level explanations
    task_explanations: List[TaskExplanation] = []
    accumulated_cost = 0.0

    for entry in result_state.schedule:
        task = task_map.get(entry.task_id)
        if task is None:
            continue

        waiting_time = entry.start_time - planning_start
        cost_contrib = task_cost(task, entry.start_time, planning_start)
        accumulated_cost += cost_contrib

        diag = explain_feasibility(task, entry.start_time, available_end)
        constraint_status = "FEASIBLE" if diag["feasible"] else "INFEASIBLE"

        # Obtain derived facts at planning start
        derived_facts = sorted(
            list(knowledge_engine.get_derived_facts(task_to_facts(task, current_time=planning_start))),
            key=lambda f: str(f),
        )

        reasons: List[str] = []
        if waiting_time == 0:
            reasons.append(
                f"Scheduled first at planning start (waiting time 0), incurring 0 waiting cost."
            )
        else:
            reasons.append(
                f"Scheduled at time {entry.start_time} (waiting time {waiting_time}); "
                f"incurs waiting cost of {cost_contrib} (waiting time {waiting_time} × priority weight {priority_weight(task.priority)})."
            )

        # Knowledge-based reasons
        if Fact("attention", task.id, "immediate") in derived_facts:
            reasons.append(
                "Identified for immediate attention due to combined high urgency and high deadline pressure."
            )
        elif Fact("deadline_pressure", task.id, "high") in derived_facts:
            reasons.append(
                f"High deadline pressure with deadline {task.deadline} close to planning horizon."
            )

        if Fact("risk", task.id, "high") in derived_facts:
            reasons.append(f"High difficulty task ({task.difficulty}) classified as high risk.")
        elif Fact("risk", task.id, "medium") in derived_facts:
            reasons.append(f"Medium difficulty task ({task.difficulty}) classified as medium risk.")

        if Fact("urgency", task.id, "high") in derived_facts and Fact("attention", task.id, "immediate") not in derived_facts:
            reasons.append(f"High urgency task based on high priority.")

        task_explanations.append(
            TaskExplanation(
                task_id=task.id,
                task_name=task.name,
                start_time=entry.start_time,
                end_time=entry.end_time,
                duration=task.duration,
                priority=task.priority,
                deadline=task.deadline,
                difficulty=task.difficulty,
                waiting_time=waiting_time,
                cost_contribution=cost_contrib,
                accumulated_cost=accumulated_cost,
                derived_facts=derived_facts,
                constraint_status=constraint_status,
                reasons=reasons,
            )
        )

    # Ordering explanations across scheduled pairs
    ordering_explanations: List[OrderingExplanation] = []
    schedule_len = len(result_state.schedule)
    for i in range(schedule_len):
        for j in range(i + 1, schedule_len):
            entry_a = result_state.schedule[i]
            entry_b = result_state.schedule[j]
            task_a = task_map.get(entry_a.task_id)
            task_b = task_map.get(entry_b.task_id)
            if task_a and task_b:
                ordering_explanations.append(
                    explain_task_ordering(
                        task_a=task_a,
                        entry_a=entry_a,
                        task_b=task_b,
                        entry_b=entry_b,
                        planning_start=planning_start,
                        available_end=available_end,
                        engine=knowledge_engine,
                    )
                )

    # Rejected candidates collection
    rejected_candidates: List[CandidateEvaluation] = []
    if search_trace is not None and search_trace.rejected_candidates:
        for step in search_trace.rejected_candidates:
            task = task_map.get(step.candidate_task_id)
            if task:
                diag = explain_feasibility(task, step.state_current_time, available_end)
                rejected_candidates.append(
                    CandidateEvaluation(
                        task_id=task.id,
                        task_name=task.name,
                        start_time=step.state_current_time,
                        end_time=step.state_current_time + task.duration,
                        duration=task.duration,
                        deadline=task.deadline,
                        available_end=available_end,
                        fits_window=diag["fits_window"],
                        meets_deadline=diag["meets_deadline"],
                        feasible=diag["feasible"],
                        reasons=step.reasons,
                    )
                )

    # Overall summary
    total_tasks = len(task_map)
    scheduled_tasks = len(result_state.schedule)
    if scheduled_tasks == total_tasks:
        summary = (
            f"All {total_tasks} tasks were successfully scheduled within the planning "
            f"window [{planning_start}, {available_end}] and all hard constraints were satisfied."
        )
    else:
        summary = (
            f"{scheduled_tasks} of {total_tasks} tasks were scheduled within the planning "
            f"window [{planning_start}, {available_end}]. "
            f"{total_tasks - scheduled_tasks} tasks could not be scheduled due to constraints."
        )

    if states_expanded is None and search_trace is not None:
        states_expanded = search_trace.expansions

    return ScheduleExplanation(
        problem_summary=summary,
        task_explanations=task_explanations,
        ordering_explanations=ordering_explanations,
        rejected_candidates=rejected_candidates,
        total_cost=result_state.cost,
        planning_start=planning_start,
        available_end=available_end,
        states_expanded=states_expanded,
    )
