import heapq


def ucs(problem, available_end=None):
    """
    Uniform Cost Search (UCS) for PlanningProblem.
    Expands nodes in increasing order of accumulated path cost g(n).
    """
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
    best_cost = {}

    initial_state = problem.initial_state

    # Track best-known cost to reach each logical state
    initial_key = initial_state.key()
    best_cost[initial_key] = initial_state.cost

    # Heap entry: (g, counter, state)
    heapq.heappush(
        frontier,
        (initial_state.cost, counter, initial_state)
    )

    while frontier:
        g, _, current = heapq.heappop(frontier)

        current_key = current.key()

        # Skip stale frontier entries if a strictly cheaper path was already expanded
        if current.cost > best_cost.get(current_key, float("inf")):
            continue

        expanded += 1

        if problem.is_goal(current):
            return current, expanded

        for successor in problem.get_successors(current):
            succ_key = successor.key()
            succ_cost = successor.cost

            # Only consider successor if it improves the cost to reach this state
            if succ_key not in best_cost or succ_cost < best_cost[succ_key]:
                best_cost[succ_key] = succ_cost
                counter += 1
                heapq.heappush(
                    frontier,
                    (succ_cost, counter, successor)
                )

    return None, expanded
