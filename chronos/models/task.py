from dataclasses import dataclass

@dataclass
class Task:
    id: int
    name: str
    duration: int
    priority: str
    deadline: int
    difficulty: str