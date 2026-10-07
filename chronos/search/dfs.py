def dfs(graph, start=None, goal=None):
    """
    Depth-First Search (DFS).
    Supports both PlanningProblem search and canonical graph search.
    """
    # PlanningProblem execution: dfs(problem)
    if start is None or hasattr(graph, "initial_state"):
        problem = graph
        frontier = [problem.initial_state]
        expanded = 0
        visited = {problem.initial_state.key()}

        while frontier:
            current = frontier.pop()
            expanded += 1

            if problem.is_goal(current):
                return current, expanded

            for successor in problem.get_successors(current):
                key = successor.key()
                if key not in visited:
                    visited.add(key)
                    frontier.append(successor)

        return None, expanded

    # Canonical graph search: dfs(graph, start, goal)
    stack = []
    stack.append(start)
    visited = {start}
    parent = {}

    while len(stack) > 0:
        current = stack.pop()

        if current == goal:
            path = []
            node = goal
            while node != start:
                path.append(node)
                node = parent[node]
            path.append(start)
            path.reverse()
            return path

        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)

    return None


if __name__ == "__main__":
    graph = {
        "A": ["B", "C"],
        "B": ["D", "E"],
        "C": ["F"],
        "D": [],
        "E": [],
        "F": [],
    }
    print(dfs(graph, "A", "F"))