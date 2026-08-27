from chronos.models.task import Task
from chronos.models.state import State
from chronos.search.astar import astar


dsa = Task(
    1, "DSA", 2, "high", 24, "high"
)

ai = Task(
    2, "AI", 3, "medium", 72, "high"
)

dbms = Task(
    3, "DBMS", 1, "medium", 48, "medium"
)

initial_state = State(
    current_time=18,
    remaining_tasks=[dsa, ai, dbms],
    schedule=[],
    cost=0
)

result, expanded = astar(initial_state, 24)

print("Final schedule:")
print(result.schedule)

print("Final cost:", result.cost)
print("States expanded:", expanded)