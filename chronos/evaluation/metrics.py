"""
Metrics and data representation for Chronos AI evaluation experiments.
"""

import csv
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ExperimentResult:
    """
    Structured outcome record for a single evaluation benchmark execution.
    """
    experiment_name: str
    scenario: str
    algorithm: str
    task_count: int
    solution_found: bool
    final_cost: Optional[float]
    states_expanded: int
    runtime_ms: float
    schedule_order: Optional[List[int]] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        """Reconstruct ExperimentResult from dictionary."""
        return cls(
            experiment_name=data["experiment_name"],
            scenario=data["scenario"],
            algorithm=data["algorithm"],
            task_count=data["task_count"],
            solution_found=bool(data["solution_found"]),
            final_cost=data.get("final_cost"),
            states_expanded=int(data["states_expanded"]),
            runtime_ms=float(data["runtime_ms"]),
            schedule_order=data.get("schedule_order"),
            notes=data.get("notes", ""),
        )


def results_to_json(results: List[ExperimentResult], filepath: str) -> None:
    """Serialize a list of ExperimentResult records to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    payload = [r.to_dict() for r in results]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_results_from_json(filepath: str) -> List[ExperimentResult]:
    """Load a list of ExperimentResult records from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ExperimentResult.from_dict(item) for item in data]


def results_to_csv(results: List[ExperimentResult], filepath: str) -> None:
    """Serialize a list of ExperimentResult records to CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = [
        "experiment_name",
        "scenario",
        "algorithm",
        "task_count",
        "solution_found",
        "final_cost",
        "states_expanded",
        "runtime_ms",
        "schedule_order",
        "notes",
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = r.to_dict()
            # Serialize schedule order as string for CSV
            if row["schedule_order"] is not None:
                row["schedule_order"] = str(row["schedule_order"])
            else:
                row["schedule_order"] = ""
            writer.writerow(row)
