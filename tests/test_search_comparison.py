import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar
from chronos.search.ucs import ucs
from chronos.constraints.checker import fits_available_time, meets_deadline


class TestSearchComparison(unittest.TestCase):

    def setUp(self):
        # The canonical 3-task problem
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

    def test_both_algorithms_operate_on_same_problem(self):
        # 8. Both algorithms operate on the exact same PlanningProblem instance
        ucs_result, ucs_expanded = ucs(self.problem)
        astar_result, astar_expanded = astar(self.problem)

        self.assertIsNotNone(ucs_result)
        self.assertIsNotNone(astar_result)

    def test_ucs_finds_valid_solution(self):
        # 1. UCS finds a solution
        ucs_result, ucs_expanded = ucs(self.problem)

        self.assertIsNotNone(ucs_result)
        # 3. Contains all required tasks
        self.assertEqual(len(ucs_result.remaining_tasks), 0)
        self.assertEqual(len(ucs_result.schedule), 3)

        scheduled_task_ids = [entry.task_id for entry in ucs_result.schedule]
        self.assertCountEqual(scheduled_task_ids, [1, 2, 3])

        # 5. Returns a valid final cost
        self.assertIsInstance(ucs_result.cost, (int, float))
        self.assertEqual(ucs_result.cost, 9)

        # 6. Reports states expanded
        self.assertIsInstance(ucs_expanded, int)
        self.assertGreater(ucs_expanded, 0)

    def test_astar_finds_valid_solution(self):
        # 2. A* finds a solution
        astar_result, astar_expanded = astar(self.problem)

        self.assertIsNotNone(astar_result)
        # 3. Contains all required tasks
        self.assertEqual(len(astar_result.remaining_tasks), 0)
        self.assertEqual(len(astar_result.schedule), 3)

        scheduled_task_ids = [entry.task_id for entry in astar_result.schedule]
        self.assertCountEqual(scheduled_task_ids, [1, 2, 3])

        # 5. Returns a valid final cost
        self.assertIsInstance(astar_result.cost, (int, float))
        self.assertEqual(astar_result.cost, 9)

        # 6. Reports states expanded
        self.assertIsInstance(astar_expanded, int)
        self.assertGreater(astar_expanded, 0)

    def test_both_schedules_satisfy_hard_constraints(self):
        # 4. Both schedules satisfy hard constraints (window + deadlines + no overlaps)
        task_map = {1: self.dsa, 2: self.ai, 3: self.dbms}

        for algorithm_name, search_fn in [("UCS", ucs), ("A*", astar)]:
            result, _ = search_fn(self.problem)
            self.assertIsNotNone(result, f"{algorithm_name} failed to find solution")

            prev_end = self.problem.planning_start
            for entry in result.schedule:
                task = task_map[entry.task_id]

                # Fits available planning window
                self.assertGreaterEqual(entry.start_time, prev_end)
                self.assertTrue(
                    fits_available_time(entry.start_time, task.duration, self.problem.available_end),
                    f"{algorithm_name}: Task {task.id} exceeds available window"
                )

                # Meets deadline
                self.assertTrue(
                    meets_deadline(entry.end_time, task.deadline),
                    f"{algorithm_name}: Task {task.id} violates deadline"
                )

                prev_end = entry.end_time

            # Final completion within planning horizon
            self.assertLessEqual(prev_end, self.problem.available_end)

    def test_tie_breaking_prevents_state_comparison_crash(self):
        # 7. Neither crashes because of State comparison in heapq
        # Create multiple tasks with identical durations and priorities to cause equal cost/f-values
        task_a = Task(10, "Task A", 2, "high", 30, "medium")
        task_b = Task(20, "Task B", 2, "high", 30, "medium")

        initial_state = State(
            current_time=18,
            remaining_tasks=[task_a, task_b],
            schedule=[],
            cost=0,
        )
        tie_problem = PlanningProblem(
            initial_state=initial_state,
            planning_start=18,
            available_end=26,
        )

        # Neither should raise TypeError: '<' not supported between instances of 'State'
        try:
            ucs_res, ucs_exp = ucs(tie_problem)
            astar_res, astar_exp = astar(tie_problem)
        except TypeError as e:
            self.fail(f"Search raised TypeError during heap tie-breaking: {e}")

        self.assertIsNotNone(ucs_res)
        self.assertIsNotNone(astar_res)

    def test_infeasible_problem_returns_none(self):
        # Infeasible problem where tasks cannot fit in planning window
        too_long_task = Task(99, "Massive Task", 10, "high", 24, "high")
        state = State(
            current_time=18,
            remaining_tasks=[too_long_task],
            schedule=[],
            cost=0,
        )
        infeasible_prob = PlanningProblem(
            initial_state=state,
            planning_start=18,
            available_end=20,  # only 2 hours available for a 10 hour task
        )

        ucs_res, ucs_exp = ucs(infeasible_prob)
        self.assertIsNone(ucs_res)
        self.assertGreaterEqual(ucs_exp, 1)

        astar_res, astar_exp = astar(infeasible_prob)
        self.assertIsNone(astar_res)
        self.assertGreaterEqual(astar_exp, 1)


if __name__ == "__main__":
    unittest.main()
