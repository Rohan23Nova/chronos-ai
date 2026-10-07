import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.successor import generate_successors


class TestSuccessor(unittest.TestCase):

    def setUp(self):
        self.dsa = Task(1, "DSA", 2, "high", 24, "high")
        self.ai = Task(2, "AI", 3, "medium", 72, "high")
        self.dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

    def test_generate_successors_valid_tasks(self):
        state = State(
            current_time=18,
            remaining_tasks=[self.dsa, self.ai, self.dbms],
            schedule=[],
            cost=0,
        )
        successors = generate_successors(state, 23)
        # All 3 tasks finish before 23 and before their respective deadlines
        self.assertEqual(len(successors), 3)

        scheduled_task_ids = [s.schedule[-1].task_id for s in successors]
        self.assertCountEqual(scheduled_task_ids, [1, 2, 3])

    def test_successor_rejects_task_exceeding_planning_window(self):
        state = State(
            current_time=18,
            remaining_tasks=[self.dsa, self.ai, self.dbms],
            schedule=[],
            cost=0,
        )
        # With available_end=20:
        # dsa (duration 2) ends at 20 <= 20 -> feasible
        # ai (duration 3) ends at 21 > 20 -> infeasible (exceeds window)
        # dbms (duration 1) ends at 19 <= 20 -> feasible
        successors = generate_successors(state, 20)
        self.assertEqual(len(successors), 2)

        scheduled_task_ids = [s.schedule[-1].task_id for s in successors]
        self.assertNotIn(self.ai.id, scheduled_task_ids)
        self.assertIn(self.dsa.id, scheduled_task_ids)
        self.assertIn(self.dbms.id, scheduled_task_ids)

    def test_successor_rejects_task_violating_deadline(self):
        # late_task duration 2 finishes at 18 + 2 = 20 > deadline 19
        late_task = Task(4, "Late Task", 2, "high", 19, "high")
        state = State(
            current_time=18,
            remaining_tasks=[self.dsa, late_task],
            schedule=[],
            cost=0,
        )
        successors = generate_successors(state, 24)
        # Only dsa is feasible; late_task must be rejected
        self.assertEqual(len(successors), 1)
        self.assertEqual(successors[0].schedule[-1].task_id, self.dsa.id)

    def test_successor_accepts_task_exactly_meeting_deadline(self):
        # exact_task duration 2 finishes at 18 + 2 = 20 == deadline 20
        exact_task = Task(5, "Exact Task", 2, "high", 20, "high")
        state = State(
            current_time=18,
            remaining_tasks=[exact_task],
            schedule=[],
            cost=0,
        )
        successors = generate_successors(state, 24)
        self.assertEqual(len(successors), 1)
        self.assertEqual(successors[0].schedule[-1].task_id, exact_task.id)
        self.assertEqual(successors[0].current_time, 20)

    def test_successor_rejects_all_infeasible_tasks(self):
        # Both tasks infeasible
        too_long = Task(6, "Too Long", 5, "low", 50, "low")  # end 23 > 20
        past_deadline = Task(7, "Past Deadline", 2, "low", 19, "low")  # end 20 > 19
        state = State(
            current_time=18,
            remaining_tasks=[too_long, past_deadline],
            schedule=[],
            cost=0,
        )
        successors = generate_successors(state, 20)
        self.assertEqual(len(successors), 0)

    def test_successor_preserves_state_structure(self):
        state = State(
            current_time=18,
            remaining_tasks=[self.dsa],
            schedule=[],
            cost=0,
        )
        successors = generate_successors(state, 24)
        self.assertEqual(len(successors), 1)
        succ = successors[0]
        self.assertEqual(succ.current_time, 20)
        self.assertEqual(succ.remaining_tasks, [])
        self.assertEqual(len(succ.schedule), 1)
        self.assertEqual(succ.schedule[0].task_id, 1)
        self.assertEqual(succ.schedule[0].start_time, 18)
        self.assertEqual(succ.schedule[0].end_time, 20)
        self.assertEqual(succ.cost, 0)


if __name__ == "__main__":
    unittest.main()