import heapq

from chronos.planning.heuristic import heuristic


def astar(problem, available_end=None):
    if available_end is not None:
        from chronos.planning.problem import PlanningProblem
        problem = PlanningProblem(
            initial_state=problem,
            planning_start=problem.current_time,
            available_end=available_end
        )

    frontier = []
    counter = 0
    expanded = 0

    initial_state = problem.initial_state
    available_end = problem.available_end

    initial_h = heuristic(initial_state, available_end)

    heapq.heappush(
        frontier,
        (initial_h, counter, initial_state)
    )

    while frontier:

        _, _, current = heapq.heappop(frontier)

        expanded += 1

        if problem.is_goal(current):
            return current, expanded

        for successor in problem.get_successors(current):

            counter += 1

            g = successor.cost
            h = heuristic(successor, available_end)
            f = g + h

            heapq.heappush(
                frontier,
                (f, counter, successor)
            )

    return None, expanded