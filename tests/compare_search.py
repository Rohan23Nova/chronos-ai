from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar
from chronos.search.ucs import ucs


def run_comparison():
    dsa = Task(1, "DSA", 2, "high", 24, "high")
    ai = Task(2, "AI", 3, "medium", 72, "high")
    dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

    initial_state = State(
        current_time=18,
        remaining_tasks=[dsa, ai, dbms],
        schedule=[],
        cost=0,
    )

    problem = PlanningProblem(
        initial_state=initial_state,
        planning_start=18,
        available_end=24,
    )

    ucs_result, ucs_expanded = ucs(problem)
    astar_result, astar_expanded = astar(problem)

    print("Search Comparison")
    print("=================")
    print()
    print("UCS")
    print(f"Solution found: {ucs_result is not None}")
    if ucs_result:
        print(f"Final cost: {ucs_result.cost}")
        print(f"States expanded: {ucs_expanded}")
        print(f"Final schedule: {ucs_result.schedule}")
    else:
        print(f"States expanded: {ucs_expanded}")

    print()
    print("A*")
    print(f"Solution found: {astar_result is not None}")
    if astar_result:
        print(f"Final cost: {astar_result.cost}")
        print(f"States expanded: {astar_expanded}")
        print(f"Final schedule: {astar_result.schedule}")
    else:
        print(f"States expanded: {astar_expanded}")


if __name__ == "__main__":
    run_comparison()
