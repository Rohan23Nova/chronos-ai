from chronos.knowledge import Fact


def priority_weight(priority):
    weights = {
        "high": 3,
        "medium": 2,
        "low": 1
    }

    return weights[priority]


def heuristic(state, available_end, knowledge_engine=None):
    """
    Domain-specific scheduling heuristic combining workload pressure,
    deadline urgency, and optional symbolic domain knowledge.

    Note: This is a domain-specific search guidance heuristic and is not
    claimed to be admissible.
    """
    if not state.remaining_tasks:
        return 0

    total_remaining_duration = sum(
        task.duration
        for task in state.remaining_tasks
    )

    available_time = available_end - state.current_time

    workload_pressure = max(
        0,
        total_remaining_duration - available_time
    )

    urgency_pressure = 0

    for task in state.remaining_tasks:

        time_to_deadline = task.deadline - state.current_time

        if time_to_deadline > 0:
            urgency_pressure += (
                priority_weight(task.priority)
                / time_to_deadline
            )
        else:
            urgency_pressure += priority_weight(task.priority)

    knowledge_pressure = 0
    if knowledge_engine is not None:
        facts = knowledge_engine.infer_all(
            state.remaining_tasks,
            current_time=state.current_time
        )
        for task in state.remaining_tasks:
            # Immediate attention derived from high urgency + deadline pressure
            if Fact("attention", task.id, "immediate") in facts:
                knowledge_pressure += 2.0
            elif Fact("deadline_pressure", task.id, "high") in facts:
                knowledge_pressure += 1.0

            # Risk pressure derived from task difficulty
            if Fact("risk", task.id, "high") in facts:
                knowledge_pressure += 0.5
            elif Fact("risk", task.id, "medium") in facts:
                knowledge_pressure += 0.2

    return workload_pressure + urgency_pressure + knowledge_pressure


def get_heuristic_breakdown(state, available_end, knowledge_engine=None):
    """
    Detailed component breakdown of the heuristic for explainability and inspection.
    """
    if not state.remaining_tasks:
        return {
            "workload_pressure": 0,
            "urgency_pressure": 0,
            "knowledge_pressure": 0,
            "total": 0,
            "task_facts": {},
        }

    total_remaining_duration = sum(t.duration for t in state.remaining_tasks)
    available_time = available_end - state.current_time
    workload_pressure = max(0, total_remaining_duration - available_time)

    urgency_pressure = 0
    for task in state.remaining_tasks:
        time_to_deadline = task.deadline - state.current_time
        if time_to_deadline > 0:
            urgency_pressure += priority_weight(task.priority) / time_to_deadline
        else:
            urgency_pressure += priority_weight(task.priority)

    knowledge_pressure = 0
    task_facts = {}
    if knowledge_engine is not None:
        facts = knowledge_engine.infer_all(
            state.remaining_tasks,
            current_time=state.current_time
        )
        for task in state.remaining_tasks:
            task_facts[task.id] = [f for f in facts if f.entity_id == task.id]
            if Fact("attention", task.id, "immediate") in facts:
                knowledge_pressure += 2.0
            elif Fact("deadline_pressure", task.id, "high") in facts:
                knowledge_pressure += 1.0

            if Fact("risk", task.id, "high") in facts:
                knowledge_pressure += 0.5
            elif Fact("risk", task.id, "medium") in facts:
                knowledge_pressure += 0.2

    return {
        "workload_pressure": workload_pressure,
        "urgency_pressure": urgency_pressure,
        "knowledge_pressure": knowledge_pressure,
        "total": workload_pressure + urgency_pressure + knowledge_pressure,
        "task_facts": task_facts,
    }