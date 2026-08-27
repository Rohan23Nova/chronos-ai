def dfs(graph, start , goal):
    stack= []
    stack.append(start)
    visited ={start}
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

graph = {
    "A": ["B", "C"],
    "B": ["D", "E"],
    "C": ["F"],
    "D": [],
    "E": [],
    "F": []
}
print(dfs(graph,"A","F"))