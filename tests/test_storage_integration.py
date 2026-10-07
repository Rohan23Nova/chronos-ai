import os
import tempfile
import unittest

from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar
from chronos.adaptation import (
    AdaptationModel,
    FeedbackRecord,
    POSTPONED,
    TOO_DIFFICULT,
    COMPLETED_EARLY,
)
from chronos.storage import DatabaseManager, build_adaptation_model


class TestStorageIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "integration_chronos.db")
        self.db = DatabaseManager(self.db_path)
        self.db.initialize_database()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_storage_planning_adaptation_lifecycle(self):
        # 1. Create and persist tasks
        tasks = [
            Task(1, "DSA", 2, "high", 24, "high"),
            Task(2, "AI", 3, "medium", 72, "high"),
            Task(3, "DBMS", 1, "medium", 48, "medium"),
        ]
        for t in tasks:
            self.db.add_task(t)

        # 2. Load tasks from SQLite
        loaded_tasks = self.db.get_all_tasks()
        self.assertEqual(len(loaded_tasks), 3)
        self.assertEqual([t.name for t in loaded_tasks], ["DSA", "AI", "DBMS"])

        # 3. Build PlanningProblem from loaded tasks
        initial_state = State(
            current_time=18,
            remaining_tasks=loaded_tasks,
            schedule=[],
            cost=0.0,
        )
        problem = PlanningProblem(
            initial_state=initial_state,
            planning_start=18,
            available_end=24,
        )

        # 4. Run A* search
        result, expanded = astar(problem)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.remaining_tasks), 0)
        self.assertEqual(len(result.schedule), 3)
        self.assertEqual(result.cost, 9)

        # 5. Save the resulting schedule and verify
        schedule_id = self.db.save_schedule(problem, result, algorithm="A*", states_expanded=expanded)
        self.assertGreater(schedule_id, 0)

        saved_schedule = self.db.get_schedule(schedule_id)
        self.assertIsNotNone(saved_schedule)
        self.assertEqual(saved_schedule["total_cost"], 9)
        self.assertEqual(len(saved_schedule["entries"]), 3)
        self.assertEqual(
            [e.task_id for e in saved_schedule["entries"]],
            [3, 1, 2]
        )

        # 6. Save user feedback to SQLite
        feedback_events = [
            FeedbackRecord(task_id=1, feedback_type=POSTPONED),
            FeedbackRecord(task_id=1, feedback_type=POSTPONED),
            FeedbackRecord(task_id=1, feedback_type=TOO_DIFFICULT),
            FeedbackRecord(task_id=2, feedback_type=COMPLETED_EARLY),
        ]
        for fb in feedback_events:
            self.db.save_feedback(fb)

        # 7. Load feedback from SQLite
        persisted_feedback = self.db.get_all_feedback()
        self.assertEqual(len(persisted_feedback), 4)

        # 8. Build AdaptationModel from loaded feedback
        reconstructed_model = build_adaptation_model(persisted_feedback)
        self.assertIsInstance(reconstructed_model, AdaptationModel)

        # 9. Verify that the learned adjustment matches direct in-memory adaptation
        direct_model = AdaptationModel()
        for fb in feedback_events:
            direct_model.record_feedback(fb.task_id, fb.feedback_type)

        dsa_adj = reconstructed_model.get_adjustment(1)
        ai_adj = reconstructed_model.get_adjustment(2)
        dbms_adj = reconstructed_model.get_adjustment(3)

        self.assertEqual(dsa_adj, direct_model.get_adjustment(1))
        self.assertEqual(ai_adj, direct_model.get_adjustment(2))
        self.assertEqual(dbms_adj, direct_model.get_adjustment(3))

        self.assertGreater(dsa_adj, 0.0)  # Postponed + Difficult increases pressure
        self.assertLess(ai_adj, 0.0)      # Completed early reduces pressure
        self.assertEqual(dbms_adj, 0.0)   # Neutral for tasks without feedback


def run_integration_demo():
    print("==================================================")
    print("Chronos AI: SQLite Persistence & Lifecycle Demo")
    print("==================================================")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "demo_chronos.db")
        db = DatabaseManager(db_path)
        db.initialize_database()

        print(f"\n1. Initialized SQLite database at: {db_path}")

        # Insert tasks
        tasks = [
            Task(1, "DSA", 2, "high", 24, "high"),
            Task(2, "AI", 3, "medium", 72, "high"),
            Task(3, "DBMS", 1, "medium", 48, "medium"),
        ]
        for t in tasks:
            db.add_task(t)
        print(f"2. Persisted {len(tasks)} tasks.")

        # Load tasks
        loaded_tasks = db.get_all_tasks()
        print(f"3. Loaded {len(loaded_tasks)} tasks from SQLite: {[t.name for t in loaded_tasks]}")

        # Solve planning problem
        problem = PlanningProblem(State(18, loaded_tasks, [], 0.0), 18, 24)
        result, expanded = astar(problem)
        print(f"4. Solved with A*: cost={result.cost}, states_expanded={expanded}")
        print(f"   Order: {[e.task_id for e in result.schedule]}")

        # Persist schedule
        schedule_id = db.save_schedule(problem, result, algorithm="A*", states_expanded=expanded)
        print(f"5. Saved schedule ID: {schedule_id} with {len(result.schedule)} entries.")

        # Persist feedback
        db.save_feedback(FeedbackRecord(1, POSTPONED))
        db.save_feedback(FeedbackRecord(1, POSTPONED))
        db.save_feedback(FeedbackRecord(1, TOO_DIFFICULT))
        db.save_feedback(FeedbackRecord(2, COMPLETED_EARLY))
        print("6. Persisted 4 user feedback records.")

        # Reconstruct adaptation
        reconstructed = build_adaptation_model(db.get_all_feedback())
        print(f"7. Reconstructed AdaptationModel from SQLite:")
        print(f"   - Task 1 (DSA) adjustment: {reconstructed.get_adjustment(1):+.2f}")
        print(f"   - Task 2 (AI) adjustment: {reconstructed.get_adjustment(2):+.2f}")
        print(f"   - Task 3 (DBMS) adjustment: {reconstructed.get_adjustment(3):+.2f}")

        # Planning history
        history = db.get_planning_history()
        print(f"8. Planning runs logged: {len(history)} run(s) found.")
        print("==================================================")


if __name__ == "__main__":
    run_integration_demo()
