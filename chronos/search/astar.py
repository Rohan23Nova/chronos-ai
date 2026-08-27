import heapq

from chronos.planning.problem import is_goal
from chronos.planning.successor import generate_successors
from chronos.planning.heuristic import heuristic

def astar(initial_state, available_end):

    frontier = []
    counter = 0

    heapq.heappush(
        frontier,
        (0, counter, initial_state)
    )
    expanded = 0
    while frontier:

        _, _, current = heapq.heappop(frontier)
        expanded += 1
        if is_goal(current):
            print("States expanded:", expanded)
            return current

        for successor in generate_successors(
            current,
            available_end
        ):

            counter += 1

            g = successor.cost
            h = heuristic(successor, available_end)
            f = g + h

            heapq.heappush(
                frontier,
                (f, counter, successor)
            )

    return None