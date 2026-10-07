import unittest
from chronos.models.task import Task
from chronos.adaptation.feedback import FeedbackRecord, AdaptationModel
from chronos.ui.helpers import (
    validate_task_input,
    execute_planning,
    format_schedule_rows,
    format_task_rows,
    format_feedback_rows,
    PRIORITY_MAP,
    DIFFICULTY_MAP,
    FEEDBACK_TYPE_MAP,
)


class TestUIHelpers(unittest.TestCase):

    def setUp(self):
        self.dsa = Task(1, "DSA", 2, "high", 24, "high")
        self.ai = Task(2, "AI", 3, "medium", 72, "high")
        self.dbms = Task(3, "DBMS", 1, "medium", 48, "medium")
        self.tasks = [self.dsa, self.ai, self.dbms]

    def test_validate_task_input_valid(self):
        valid, err = validate_task_input(
            task_id=4,
            name="Operating Systems",
            duration=2,
            priority="high",
            difficulty="medium",
            deadline=20,
            existing_ids={1, 2, 3},
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_validate_task_input_invalid_id(self):
        valid, err = validate_task_input(
            task_id=0,
            name="Valid Name",
            duration=2,
            priority="low",
            difficulty="low",
            deadline=20,
        )
        self.assertFalse(valid)
        self.assertIn("Task ID must be a positive integer", err)

    def test_validate_task_input_duplicate_id(self):
        valid, err = validate_task_input(
            task_id=2,
            name="Duplicate Task",
            duration=2,
            priority="low",
            difficulty="low",
            deadline=20,
            existing_ids={1, 2, 3},
        )
        self.assertFalse(valid)
        self.assertIn("already exists", err)

    def test_validate_task_input_empty_name(self):
        valid, err = validate_task_input(
            task_id=5,
            name="   ",
            duration=2,
            priority="low",
            difficulty="low",
            deadline=20,
        )
        self.assertFalse(valid)
        self.assertIn("Task name cannot be empty", err)

    def test_validate_task_input_deadline_less_than_duration(self):
        valid, err = validate_task_input(
            task_id=5,
            name="Too Short Deadline",
            duration=5,
            priority="low",
            difficulty="low",
            deadline=3,
        )
        self.assertFalse(valid)
        self.assertIn("Deadline", err)

    def test_execute_planning_astar(self):
        res = execute_planning(
            tasks=self.tasks,
            planning_start=18,
            available_end=24,
            algorithm="A*",
        )
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["result_state"])
        self.assertEqual(res["result_state"].cost, 9)
        self.assertEqual(len(res["result_state"].schedule), 3)
        self.assertIsNotNone(res["explanation"])

    def test_execute_planning_ucs(self):
        res = execute_planning(
            tasks=self.tasks,
            planning_start=18,
            available_end=24,
            algorithm="UCS",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["result_state"].cost, 9)

    def test_execute_planning_bfs(self):
        res = execute_planning(
            tasks=self.tasks,
            planning_start=18,
            available_end=24,
            algorithm="BFS",
        )
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["result_state"])

    def test_execute_planning_dfs(self):
        res = execute_planning(
            tasks=self.tasks,
            planning_start=18,
            available_end=24,
            algorithm="DFS",
        )
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["result_state"])

    def test_execute_planning_with_adaptation(self):
        model = AdaptationModel()
        model.record_feedback(task_id=1, feedback_type="postponed")
        res = execute_planning(
            tasks=self.tasks,
            planning_start=18,
            available_end=24,
            algorithm="A*",
            adaptation_model=model,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["result_state"].cost, 9)

    def test_format_helpers(self):
        plan_res = execute_planning(
            tasks=self.tasks,
            planning_start=18,
            available_end=24,
            algorithm="A*",
        )
        sched_rows = format_schedule_rows(plan_res["result_state"], self.tasks)
        self.assertEqual(len(sched_rows), 3)
        self.assertEqual(sched_rows[0]["Name"], "DBMS")

        task_rows = format_task_rows(self.tasks)
        self.assertEqual(len(task_rows), 3)

        records = [
            FeedbackRecord(task_id=1, feedback_type="completed_on_time", rating=5.0)
        ]
        fb_rows = format_feedback_rows(records, self.tasks)
        self.assertEqual(len(fb_rows), 1)
        self.assertEqual(fb_rows[0]["Feedback Type"], "Completed on time")


if __name__ == "__main__":
    unittest.main()
