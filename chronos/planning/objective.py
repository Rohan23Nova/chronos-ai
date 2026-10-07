def deadline_penalty(task, end_time):
    if end_time <= task.deadline:
        return 0

    return end_time - task.deadline


def priority_weight(priority):
    weights = {
        "high": 3,
        "medium": 2,
        "low": 1
    }

    return weights[priority]


def priority_delay_penalty(
    task,
    start_time,
    planning_start
):
    waiting_time = start_time - planning_start

    return (
        priority_weight(task.priority)
        * waiting_time
    )