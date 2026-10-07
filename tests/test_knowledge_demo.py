import unittest
from chronos.models.task import Task
from chronos.knowledge import (
    Fact,
    get_default_engine,
    task_to_facts,
)


from chronos.models.state import State
from chronos.planning.heuristic import get_heuristic_breakdown


def run_demo():
    engine = get_default_engine()
    current_time = 18

    dsa = Task(1, "DSA", 2, "high", 24, "high")
    ai = Task(2, "AI", 3, "medium", 72, "high")
    dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

    tasks = [dsa, ai, dbms]

    print("==================================================")
    print("Chronos AI: Symbolic Knowledge & Heuristic Trace Demo")
    print("==================================================")
    print(f"Planning Context Current Time: {current_time}\n")

    for task in tasks:
        initial = task_to_facts(task, current_time=current_time)
        derived = engine.get_derived_facts(initial)

        # Single-task state to isolate this task's heuristic contribution
        single_task_state = State(current_time, [task], [], 0)
        breakdown = get_heuristic_breakdown(single_task_state, available_end=24, knowledge_engine=engine)

        print(f"Task {task.id}: {task.name}")
        print(
            f"  Attributes : priority={task.priority}, difficulty={task.difficulty}, "
            f"duration={task.duration}, deadline={task.deadline}"
        )
        print(f"  Time Left  : {task.deadline - current_time} units")
        print("  Initial Facts:")
        for f in sorted(initial, key=lambda x: str(x)):
            print(f"    - {f}")
        print("  Derived Facts (Forward Chaining):")
        for f in sorted(derived, key=lambda x: str(x)):
            print(f"    - {f}")
        print("  Heuristic Contribution:")
        print(f"    - Base Urgency Pressure : {breakdown['urgency_pressure']:.2f}")
        print(f"    - Knowledge Risk/Attention Pressure : +{breakdown['knowledge_pressure']:.2f}")
        print(f"    - Task Total Heuristic : {breakdown['total']:.2f}")
        print()

    # Overall State Heuristic
    all_state = State(current_time, tasks, [], 0)
    all_breakdown = get_heuristic_breakdown(all_state, available_end=24, knowledge_engine=engine)
    print("--------------------------------------------------")
    print(f"Composite Initial State Heuristic (Available End 24): {all_breakdown['total']:.2f}")
    print(f"  - Workload Pressure  : {all_breakdown['workload_pressure']:.2f}")
    print(f"  - Base Urgency       : {all_breakdown['urgency_pressure']:.2f}")
    print(f"  - Knowledge Pressure : +{all_breakdown['knowledge_pressure']:.2f}")
    print("==================================================\n")


class TestKnowledgeDemo(unittest.TestCase):

    def test_canonical_tasks_reasoning(self):
        engine = get_default_engine()
        current_time = 18

        dsa = Task(1, "DSA", 2, "high", 24, "high")
        ai = Task(2, "AI", 3, "medium", 72, "high")
        dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

        # DSA Reasoning:
        dsa_initial = task_to_facts(dsa, current_time=current_time)
        dsa_derived = engine.get_derived_facts(dsa_initial)

        self.assertIn(Fact("urgency", 1, "high"), dsa_derived)
        self.assertIn(Fact("risk", 1, "high"), dsa_derived)
        self.assertIn(Fact("deadline_pressure", 1, "high"), dsa_derived)
        self.assertIn(Fact("attention", 1, "immediate"), dsa_derived)

        # AI Reasoning:
        ai_initial = task_to_facts(ai, current_time=current_time)
        ai_derived = engine.get_derived_facts(ai_initial)

        self.assertIn(Fact("risk", 2, "high"), ai_derived)
        self.assertNotIn(Fact("urgency", 2, "high"), ai_derived)
        self.assertNotIn(Fact("attention", 2, "immediate"), ai_derived)

        # DBMS Reasoning:
        dbms_initial = task_to_facts(dbms, current_time=current_time)
        dbms_derived = engine.get_derived_facts(dbms_initial)

        self.assertIn(Fact("risk", 3, "medium"), dbms_derived)
        self.assertNotIn(Fact("attention", 3, "immediate"), dbms_derived)


if __name__ == "__main__":
    run_demo()
