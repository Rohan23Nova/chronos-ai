
def priority_weight(priority):
    weights = {
        "high": 3,
        "medium": 2,
        "low": 1
    }

    return weights[priority]


def task_cost(task, start_time, planning_start):
    waiting_time = start_time - planning_start
    return priority_weight(task.priority) * waiting_time


def is_goal(state):
    return len(state.remaining_tasks) == 0