from collections import deque

def bfs(graph, start, goal):
    queue = deque()

    queue.append(start)
  
    visited = {start}

    parent = {}

    while len(queue) > 0:
        
      
        current = queue.popleft()
  
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
                
                
                queue.append(neighbor)

    
    return None
graph = {
    "A": ["B", "C"],
    "B": ["D", "E"],
    "C": ["F"],
    "D": [],
    "E": [],
    "F": []
}

print(bfs(graph, "A", "F"))