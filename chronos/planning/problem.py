
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


class PlanningProblem:
    def __init__(self, initial_state, planning_start, available_end):
        self.initial_state = initial_state
        self.planning_start = planning_start
        self.available_end = available_end

    def is_goal(self, state):
        return is_goal(state)

    def get_successors(self, state):
        from chronos.planning.successor import generate_successors
        return generate_successors(state, self.available_end, self.planning_start)