from chronos.models.state import State
from chronos.models.schedule import ScheduleEntry
from chronos.planning.problem import task_cost
from chronos.constraints.checker import is_feasible

def generate_successors(state, available_end, planning_start=None):
    if planning_start is None:
        planning_start = state.current_time

    successors = []

    for task in state.remaining_tasks:

        if is_feasible(task, state.current_time, available_end):

            end_time = state.current_time + task.duration

            entry = ScheduleEntry(
                task_id=task.id,
                start_time=state.current_time,
                end_time=end_time
            )

            new_remaining = [
                t for t in state.remaining_tasks
                if t.id != task.id
            ]

            new_schedule = state.schedule + [entry]
            task_cost_value = task_cost(
                task,
                state.current_time,
                planning_start
            )
            
            new_state = State(
                current_time=end_time,
                remaining_tasks=new_remaining,
                schedule=new_schedule,
                cost=state.cost + task_cost_value
            )

            successors.append(new_state)

    return successors