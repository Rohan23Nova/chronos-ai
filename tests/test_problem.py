import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.models.schedule import ScheduleEntry
from chronos.planning.problem import PlanningProblem


class TestPlanningProblem(unittest.TestCase):

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

    def test_planning_problem_initialization(self):
        self.assertIsInstance(self.problem, PlanningProblem)

    def test_correct_planning_start(self):
        self.assertEqual(self.problem.planning_start, 18)

    def test_correct_available_end(self):
        self.assertEqual(self.problem.available_end, 24)

    def test_correct_initial_state(self):
        self.assertEqual(self.problem.initial_state, self.initial_state)
        self.assertEqual(self.problem.initial_state.current_time, 18)
        self.assertEqual(len(self.problem.initial_state.remaining_tasks), 3)

    def test_goal_detection(self):
        # State with remaining tasks -> False
        self.assertFalse(self.problem.is_goal(self.initial_state))

        # State with no remaining tasks -> True
        goal_state = State(
            current_time=24,
            remaining_tasks=[],
            schedule=[
                ScheduleEntry(task_id=3, start_time=18, end_time=19),
                ScheduleEntry(task_id=1, start_time=19, end_time=21),
                ScheduleEntry(task_id=2, start_time=21, end_time=24),
            ],
            cost=9,
        )
        self.assertTrue(self.problem.is_goal(goal_state))

    def test_successor_generation_through_planning_problem(self):
        successors = self.problem.get_successors(self.initial_state)
        self.assertEqual(len(successors), 3)

        scheduled_task_ids = [s.schedule[-1].task_id for s in successors]
        self.assertCountEqual(scheduled_task_ids, [1, 2, 3])

    def test_planning_window_constraints(self):
        # Restrict window so AI (duration 3) cannot finish before available_end 20
        constrained_problem = PlanningProblem(
            initial_state=self.initial_state,
            planning_start=18,
            available_end=20,
        )
        successors = constrained_problem.get_successors(self.initial_state)
        self.assertEqual(len(successors), 2)
        scheduled_task_ids = [s.schedule[-1].task_id for s in successors]
        self.assertNotIn(self.ai.id, scheduled_task_ids)
        self.assertIn(self.dsa.id, scheduled_task_ids)
        self.assertIn(self.dbms.id, scheduled_task_ids)

    def test_deadline_constraints(self):
        # late_task duration 2 finishes at 18+2=20 > 19
        late_task = Task(4, "Late Task", 2, "high", 19, "high")
        state = State(
            current_time=18,
            remaining_tasks=[self.dsa, late_task],
            schedule=[],
            cost=0,
        )
        problem = PlanningProblem(
            initial_state=state,
            planning_start=18,
            available_end=24,
        )
        successors = problem.get_successors(state)
        self.assertEqual(len(successors), 1)
        self.assertEqual(successors[0].schedule[-1].task_id, self.dsa.id)

    def test_planning_start_used_for_cost(self):
        # Priority "high" has weight 3
        custom_task = Task(10, "Custom Task", 2, "high", 50, "high")
        state = State(
            current_time=12,
            remaining_tasks=[custom_task],
            schedule=[],
            cost=0,
        )
        problem = PlanningProblem(
            initial_state=state,
            planning_start=10,
            available_end=30,
        )
        successors = problem.get_successors(state)
        self.assertEqual(len(successors), 1)
        # Expected waiting_time = current_time (12) - planning_start (10) = 2
        # Cost = weight (3) * waiting_time (2) = 6
        self.assertEqual(successors[0].cost, 6)


if __name__ == "__main__":
    unittest.main()
