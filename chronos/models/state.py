from dataclasses import dataclass

@dataclass
class State:
    current_time: int
    remaining_tasks: list
    schedule: list
    cost: float

    def key(self):
        return (self.current_time, tuple(sorted(t.id for t in self.remaining_tasks)))