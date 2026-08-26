from dataclasses import dataclass

@dataclass
class State:
    current_time: int
    remaining_tasks: list
    schedule: list
    cost: float