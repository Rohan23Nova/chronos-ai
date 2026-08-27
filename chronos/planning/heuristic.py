def priority_weight(priority):
    weights = {
        "high": 3,
        "medium": 2,
        "low": 1
    }

    return weights[priority]


def heuristic(state, available_end):

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

    return workload_pressure + urgency_pressure