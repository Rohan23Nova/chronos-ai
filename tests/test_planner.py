import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar


class TestPlanner(unittest.TestCase):

    def setUp(self):
        self.dsa = Task(1, "DSA", 2, "high", 24, "high")
        self.ai = Task(2, "AI", 3, "medium", 72, "high")
        self.dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

        self.initial_state = State(
            current_time=18,
            remaining_tasks=[self.dsa, self.ai, self.dbms],
            schedule=[],
            cost=0,
        )

        self.problem = PlanningProblem(
            initial_state=self.initial_state,
            planning_start=18,
            available_end=24,
        )

    def test_astar_solves_three_task_problem(self):
        result, expanded = astar(self.problem)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.remaining_tasks), 0)
        self.assertEqual(len(result.schedule), 3)

        scheduled_task_ids = [entry.task_id for entry in result.schedule]
        self.assertEqual(scheduled_task_ids, [3, 1, 2])
        self.assertEqual(result.cost, 9)
        self.assertEqual(expanded, 10)

    def test_astar_backward_compatibility(self):
        result, expanded = astar(self.initial_state, 24)

        self.assertIsNotNone(result)
        self.assertEqual(result.cost, 9)
        self.assertEqual(expanded, 10)


if __name__ == "__main__":
    dsa = Task(1, "DSA", 2, "high", 24, "high")
    ai = Task(2, "AI", 3, "medium", 72, "high")
    dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

    initial_state = State(
        current_time=18,
        remaining_tasks=[dsa, ai, dbms],
        schedule=[],
        cost=0,
    )

    problem = PlanningProblem(
        initial_state=initial_state,
        planning_start=18,
        available_end=24,
    )

    result, expanded = astar(problem)

    print("Final schedule:")
    print(result.schedule)
    print("Final cost:", result.cost)
    print("States expanded:", expanded)