from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.successor import generate_successors


dsa = Task(1, "DSA", 2, "high", 24, "high")
ai = Task(2, "AI", 3, "medium", 72, "high")
dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

state = State(
    current_time=18,
    remaining_tasks=[dsa, ai, dbms],
    schedule=[],
    cost=0
)

successors = generate_successors(state, 23)

for successor in successors:
    print(successor)