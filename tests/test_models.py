from chronos.models.task import Task
from chronos.models.schedule import ScheduleEntry
from chronos.models.state import State


task = Task(
    id=1,
    name="DSA Practice",
    duration=2,
    priority="high",
    deadline=24,
    difficulty="high"
)

entry = ScheduleEntry(
    task_id=1,
    start_time=18,
    end_time=20
)

state = State(
    current_time=20,
    remaining_tasks=[],
    schedule=[entry],
    cost=0
)

print(task)
print(entry)
print(state)