from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.heuristic import heuristic


dsa = Task(1, "DSA", 2, "high", 24, "high")
ai = Task(2, "AI", 3, "medium", 72, "high")
dbms = Task(3, "DBMS", 1, "medium", 48, "medium")


state = State(
    current_time=18,
    remaining_tasks=[dsa, ai, dbms],
    schedule=[],
    cost=0
)

print(heuristic(state, 24))