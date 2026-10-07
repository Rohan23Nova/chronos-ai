import heapq

from chronos.planning.heuristic import heuristic
from chronos.knowledge import get_default_engine


def astar(problem, available_end=None, knowledge_engine=None, trace=None):
    if available_end is not None:
        from chronos.planning.problem import PlanningProblem
        problem = PlanningProblem(
            initial_state=problem,
            planning_start=problem.current_time,
            available_end=available_end
        )

    # Use default RuleEngine if not explicitly specified; pass False to disable
    if knowledge_engine is None:
        knowledge_engine = get_default_engine()
    elif knowledge_engine is False:
        knowledge_engine = None

    frontier = []
    counter = 0
    expanded = 0
    best_cost = {}

    initial_state = problem.initial_state
    available_end = problem.available_end

    initial_key = initial_state.key()
    best_cost[initial_key] = initial_state.cost

    initial_h = heuristic(initial_state, available_end, knowledge_engine=knowledge_engine)

    heapq.heappush(
        frontier,
        (initial_h, counter, initial_state)
    )

    while frontier:

        f, _, current = heapq.heappop(frontier)

        current_key = current.key()

        if current.cost > best_cost.get(current_key, float("inf")):
            continue

        expanded += 1
        if trace is not None:
            trace.record_expansion(current)

        if problem.is_goal(current):
            return current, expanded

        for successor in problem.get_successors(current, trace=trace):
            succ_key = successor.key()
            g = successor.cost

            if succ_key not in best_cost or g < best_cost[succ_key]:
                best_cost[succ_key] = g
                counter += 1

                h = heuristic(successor, available_end, knowledge_engine=knowledge_engine)
                f = g + h

                heapq.heappush(
                    frontier,
                    (f, counter, successor)
                )

    return None, expanded