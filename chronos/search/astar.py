import heapq

from chronos.planning.problem import is_goal
from chronos.planning.successor import generate_successors


def astar(initial_state, available_end):

    frontier = []
    counter = 0

    heapq.heappush(
        frontier,
        (0, counter, initial_state)
    )

    while frontier:

        _, _, current = heapq.heappop(frontier)

        if is_goal(current):
            return current

        for successor in generate_successors(
            current,
            available_end
        ):

            counter += 1

            g = successor.cost
            h = 0
            f = g + h

            heapq.heappush(
                frontier,
                (f, counter, successor)
            )

    return None