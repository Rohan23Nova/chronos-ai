from chronos.models.state import State
from chronos.models.schedule import ScheduleEntry
from chronos.planning.problem import task_cost

def generate_successors(state, available_end):
    successors = []

    for task in state.remaining_tasks:

        end_time = state.current_time + task.duration

        if end_time <= available_end:

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
                18
            )
            
            new_state = State(
                current_time=end_time,
                remaining_tasks=new_remaining,
                schedule=new_schedule,
                cost=state.cost + task_cost_value
            )

            successors.append(new_state)

    return successors