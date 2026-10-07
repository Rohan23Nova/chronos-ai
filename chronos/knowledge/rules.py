from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Set

# Deterministic threshold for deadline proximity.
# A task with remaining time to deadline <= 6 time units is under high deadline pressure.
DEFAULT_DEADLINE_PRESSURE_THRESHOLD = 6


@dataclass(frozen=True)
class Fact:
    """
    Symbolic fact representation: (predicate, entity_id, value).
    Example: Fact("priority", 1, "high") represents priority(1, high).
    """
    predicate: str
    entity_id: Any
    value: Any

    def __repr__(self) -> str:
        return f"Fact({self.predicate!r}, {self.entity_id!r}, {self.value!r})"

    def __str__(self) -> str:
        return f"{self.predicate}({self.entity_id}, {self.value})"


class Rule:
    """
    Explicit, inspectable, deterministic rule.
    A rule evaluates its conditions against a knowledge base for an entity
    and derives a conclusion fact when all conditions are satisfied.
    """
    def __init__(
        self,
        name: str,
        conditions: List[Callable[[Any, Set[Fact]], bool]],
        conclusion: Callable[[Any], Fact],
        description: str = "",
    ):
        self.name = name
        self.conditions = conditions
        self.conclusion = conclusion
        self.description = description

    def __repr__(self) -> str:
        return f"Rule(name={self.name!r})"

    def matches(self, entity_id: Any, facts: Set[Fact]) -> bool:
        """Check if all conditions are satisfied for the given entity in facts."""
        return all(cond(entity_id, facts) for cond in self.conditions)

    def apply(self, entity_id: Any) -> Fact:
        """Produce the conclusion fact for the given entity."""
        return self.conclusion(entity_id)


def has_fact(predicate: str, value: Any) -> Callable[[Any, Set[Fact]], bool]:
    """Condition callable checking whether Fact(predicate, entity_id, value) is present."""
    def condition(entity_id: Any, facts: Set[Fact]) -> bool:
        return Fact(predicate, entity_id, value) in facts

    condition.__doc__ = f"{predicate}(task, {value})"
    return condition


def deadline_near(
    threshold: int = DEFAULT_DEADLINE_PRESSURE_THRESHOLD,
) -> Callable[[Any, Set[Fact]], bool]:
    """Condition callable checking whether time_to_deadline <= threshold."""
    def condition(entity_id: Any, facts: Set[Fact]) -> bool:
        for f in facts:
            if f.predicate == "time_to_deadline" and f.entity_id == entity_id:
                return f.value <= threshold
        return False

    condition.__doc__ = f"time_to_deadline(task) <= {threshold}"
    return condition


def conclude(predicate: str, value: Any) -> Callable[[Any], Fact]:
    """Conclusion callable generating Fact(predicate, entity_id, value)."""
    def make_fact(entity_id: Any) -> Fact:
        return Fact(predicate, entity_id, value)

    make_fact.__doc__ = f"{predicate}(task, {value})"
    return make_fact


def task_to_facts(task: Any, current_time: Optional[int] = None) -> Set[Fact]:
    """
    Generate initial symbolic facts from a Task and optional planning context.
    """
    facts = {
        Fact("priority", task.id, task.priority),
        Fact("difficulty", task.id, task.difficulty),
        Fact("duration", task.id, task.duration),
        Fact("deadline", task.id, task.deadline),
    }

    if current_time is not None:
        facts.add(Fact("time_to_deadline", task.id, task.deadline - current_time))

    return facts


def get_default_rules(
    deadline_threshold: int = DEFAULT_DEADLINE_PRESSURE_THRESHOLD,
) -> List[Rule]:
    """
    Construct the domain-specific rule set for Chronos AI.
    """
    return [
        # RULE 1: High Priority -> High Urgency
        Rule(
            name="high_priority",
            conditions=[has_fact("priority", "high")],
            conclusion=conclude("urgency", "high"),
            description="Tasks with high priority have high urgency",
        ),
        # RULE 2: Low Priority -> Low Urgency
        Rule(
            name="low_priority",
            conditions=[has_fact("priority", "low")],
            conclusion=conclude("urgency", "low"),
            description="Tasks with low priority have low urgency",
        ),
        # RULE 3: High Difficulty -> High Risk
        Rule(
            name="high_difficulty",
            conditions=[has_fact("difficulty", "high")],
            conclusion=conclude("risk", "high"),
            description="Tasks with high difficulty have high risk",
        ),
        # RULE 4: Medium Difficulty -> Medium Risk
        Rule(
            name="medium_difficulty",
            conditions=[has_fact("difficulty", "medium")],
            conclusion=conclude("risk", "medium"),
            description="Tasks with medium difficulty have medium risk",
        ),
        # RULE 5: Deadline Pressure
        Rule(
            name="deadline_pressure",
            conditions=[deadline_near(threshold=deadline_threshold)],
            conclusion=conclude("deadline_pressure", "high"),
            description=f"Tasks with deadline within {deadline_threshold} units have high deadline pressure",
        ),
        # RULE 6: High Urgency + High Deadline Pressure -> Immediate Attention
        Rule(
            name="immediate_attention",
            conditions=[
                has_fact("urgency", "high"),
                has_fact("deadline_pressure", "high"),
            ],
            conclusion=conclude("attention", "immediate"),
            description="Tasks with high urgency and high deadline pressure require immediate attention",
        ),
    ]
