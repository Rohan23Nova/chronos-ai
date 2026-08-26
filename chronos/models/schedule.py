from dataclasses import dataclass

@dataclass
class ScheduleEntry:
    task_id: int
    start_time: int
    end_time: int