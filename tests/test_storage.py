import os
import sqlite3
import tempfile
import unittest

from chronos.models.task import Task
from chronos.models.state import State
from chronos.models.schedule import ScheduleEntry
from chronos.planning.problem import PlanningProblem
from chronos.adaptation import FeedbackRecord, POSTPONED, TOO_DIFFICULT
from chronos.storage import DatabaseManager, build_adaptation_model


class TestStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_chronos.db")
        self.db = DatabaseManager(self.db_path)
        self.db.initialize_database()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_initialization(self):
        # 1. Database initialization creates required tables
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name ASC;"
            )
            tables = {row["name"] for row in cursor.fetchall()}

        expected_tables = {"tasks", "schedules", "schedule_entries", "planning_runs", "feedback"}
        self.assertTrue(expected_tables.issubset(tables))

    def test_task_insertion(self):
        # 2. Task insertion
        task = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(task)

        retrieved = self.db.get_task(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, 1)
        self.assertEqual(retrieved.name, "DSA")

    def test_task_retrieval(self):
        # 3. Task retrieval converts rows back to Task dataclass
        task = Task(2, "AI", 3, "medium", 72, "high")
        self.db.add_task(task)

        retrieved = self.db.get_task(2)
        self.assertIsInstance(retrieved, Task)
        self.assertEqual(retrieved.id, 2)
        self.assertEqual(retrieved.name, "AI")
        self.assertEqual(retrieved.duration, 3)
        self.assertEqual(retrieved.priority, "medium")
        self.assertEqual(retrieved.deadline, 72)
        self.assertEqual(retrieved.difficulty, "high")

    def test_get_all_tasks(self):
        # 4. Get all tasks
        t1 = Task(1, "DSA", 2, "high", 24, "high")
        t2 = Task(2, "AI", 3, "medium", 72, "high")
        t3 = Task(3, "DBMS", 1, "medium", 48, "medium")

        self.db.add_task(t1)
        self.db.add_task(t2)
        self.db.add_task(t3)

        tasks = self.db.get_all_tasks()
        self.assertEqual(len(tasks), 3)
        self.assertEqual([t.id for t in tasks], [1, 2, 3])

    def test_task_update(self):
        # 5. Task update
        task = Task(1, "DSA Practice", 2, "high", 24, "high")
        self.db.add_task(task)

        updated_task = Task(1, "DSA Advanced", 3, "high", 30, "high")
        success = self.db.update_task(updated_task)
        self.assertTrue(success)

        retrieved = self.db.get_task(1)
        self.assertEqual(retrieved.name, "DSA Advanced")
        self.assertEqual(retrieved.duration, 3)
        self.assertEqual(retrieved.deadline, 30)

    def test_task_deletion(self):
        # 6. Task deletion
        task = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(task)

        self.assertTrue(self.db.delete_task(1))
        self.assertIsNone(self.db.get_task(1))
        self.assertFalse(self.db.delete_task(1))

    def test_feedback_persistence(self):
        # 7. Feedback persistence
        task = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(task)

        record = FeedbackRecord(
            task_id=1,
            feedback_type=POSTPONED,
            rating=4.0,
            scheduled_duration=2,
            actual_duration=None,
            comment="Postponed due to interview",
            step=1,
        )
        row_id = self.db.save_feedback(record)
        self.assertGreater(row_id, 0)

    def test_feedback_retrieval(self):
        # 8. Feedback retrieval
        t1 = Task(1, "DSA", 2, "high", 24, "high")
        t2 = Task(2, "AI", 3, "medium", 72, "high")
        self.db.add_task(t1)
        self.db.add_task(t2)

        r1 = FeedbackRecord(1, POSTPONED, step=1)
        r2 = FeedbackRecord(1, TOO_DIFFICULT, step=2)
        r3 = FeedbackRecord(2, POSTPONED, step=3)

        self.db.save_feedback(r1)
        self.db.save_feedback(r2)
        self.db.save_feedback(r3)

        fb_1 = self.db.get_feedback(1)
        self.assertEqual(len(fb_1), 2)
        self.assertEqual(fb_1[0].feedback_type, POSTPONED)
        self.assertEqual(fb_1[1].feedback_type, TOO_DIFFICULT)

        all_fb = self.db.get_all_feedback()
        self.assertEqual(len(all_fb), 3)

    def test_schedule_persistence(self):
        # 9. Schedule persistence
        t1 = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(t1)

        problem = PlanningProblem(
            initial_state=State(18, [t1], [], 0),
            planning_start=18,
            available_end=24,
        )
        result_state = State(
            current_time=20,
            remaining_tasks=[],
            schedule=[ScheduleEntry(1, 18, 20)],
            cost=0.0,
        )

        schedule_id = self.db.save_schedule(problem, result_state, algorithm="A*", states_expanded=3)
        self.assertGreater(schedule_id, 0)

        sched_info = self.db.get_schedule(schedule_id)
        self.assertIsNotNone(sched_info)
        self.assertEqual(sched_info["id"], schedule_id)
        self.assertEqual(sched_info["planning_start"], 18)
        self.assertEqual(sched_info["available_end"], 24)
        self.assertEqual(sched_info["total_cost"], 0.0)
        self.assertEqual(sched_info["states_expanded"], 3)

    def test_schedule_entry_persistence(self):
        # 10. Schedule entry persistence
        t1 = Task(1, "DSA", 2, "high", 24, "high")
        t2 = Task(2, "AI", 3, "medium", 72, "high")
        self.db.add_task(t1)
        self.db.add_task(t2)

        problem = PlanningProblem(
            initial_state=State(18, [t1, t2], [], 0),
            planning_start=18,
            available_end=24,
        )
        result_state = State(
            current_time=23,
            remaining_tasks=[],
            schedule=[ScheduleEntry(1, 18, 20), ScheduleEntry(2, 20, 23)],
            cost=4.0,
        )

        schedule_id = self.db.save_schedule(problem, result_state, algorithm="A*")
        sched_info = self.db.get_schedule(schedule_id)
        entries = sched_info["entries"]

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].task_id, 1)
        self.assertEqual(entries[0].start_time, 18)
        self.assertEqual(entries[0].end_time, 20)
        self.assertEqual(entries[1].task_id, 2)
        self.assertEqual(entries[1].start_time, 20)
        self.assertEqual(entries[1].end_time, 23)

    def test_planning_history_persistence(self):
        # 11. Planning history persistence
        t1 = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(t1)

        prob = PlanningProblem(State(18, [t1], [], 0), 18, 24)
        state = State(20, [], [ScheduleEntry(1, 18, 20)], 0.0)

        self.db.save_schedule(prob, state, algorithm="A*", states_expanded=5)
        self.db.save_schedule(prob, state, algorithm="UCS", states_expanded=7)

        history = self.db.get_planning_history()
        self.assertEqual(len(history), 2)
        # Most recent first
        self.assertEqual(history[0]["algorithm"], "UCS")
        self.assertEqual(history[1]["algorithm"], "A*")
        self.assertTrue(history[0]["success"])

    def test_foreign_key_behavior(self):
        # 12. Foreign-key behavior where applicable
        # Inserting feedback for a non-existent task raises IntegrityError
        record = FeedbackRecord(task_id=999, feedback_type=POSTPONED)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_feedback(record)

        # Deleting a task cascades to its feedback
        task = Task(10, "TempTask", 2, "low", 24, "low")
        self.db.add_task(task)
        self.db.save_feedback(FeedbackRecord(10, POSTPONED))
        self.assertEqual(len(self.db.get_feedback(10)), 1)

        self.db.delete_task(10)
        self.assertEqual(len(self.db.get_feedback(10)), 0)

    def test_repeated_database_initialization(self):
        # 13. Repeated database initialization is safe
        task = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(task)

        # Re-initialize multiple times
        self.db.initialize_database()
        self.db.initialize_database()

        # Existing data preserved
        retrieved = self.db.get_task(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "DSA")

    def test_data_survives_closing_and_reopening(self):
        # 14. Data survives closing and reopening the database connection
        task = Task(1, "DSA", 2, "high", 24, "high")
        self.db.add_task(task)
        self.db.save_feedback(FeedbackRecord(1, POSTPONED))

        # Instantiate a new DatabaseManager pointing to the exact same file
        new_db_manager = DatabaseManager(self.db_path)
        retrieved_task = new_db_manager.get_task(1)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.name, "DSA")

        feedback_records = new_db_manager.get_feedback(1)
        self.assertEqual(len(feedback_records), 1)
        self.assertEqual(feedback_records[0].feedback_type, POSTPONED)


if __name__ == "__main__":
    unittest.main()
