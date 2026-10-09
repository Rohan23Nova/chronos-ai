import unittest
import os

try:
    import streamlit
    from streamlit.testing.v1 import AppTest
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from chronos.models.task import Task
from chronos.storage import DatabaseManager, build_adaptation_model
from chronos.ui.helpers import execute_planning


class TestStreamlitApp(unittest.TestCase):

    def setUp(self):
        # Ensure temporary/isolated database or verify default database works
        self.db = DatabaseManager()
        self.db.initialize_database()

    def test_app_headless_run(self):
        if not STREAMLIT_AVAILABLE:
            self.skipTest("Streamlit not installed in this Python environment.")

        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        at = AppTest.from_file(app_path)
        at.run(timeout=10)
        self.assertEqual(len(at.exception), 0)

    def test_app_navigation_sections(self):
        if not STREAMLIT_AVAILABLE:
            self.skipTest("Streamlit not installed in this Python environment.")

        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        sections = [
            "Dashboard",
            "Tasks",
            "Plan Schedule",
            "Feedback",
            "Planning History",
            "Explainability",
            "Evaluation",
        ]

        for section in sections:
            at = AppTest.from_file(app_path)
            at.run(timeout=10)
            self.assertEqual(len(at.exception), 0)

            # Switch navigation radio
            at.sidebar.radio[0].set_value(section)
            at.run(timeout=10)
            self.assertEqual(len(at.exception), 0, f"Error navigating to {section}")

    def test_app_theme_switching(self):
        if not STREAMLIT_AVAILABLE:
            self.skipTest("Streamlit not installed in this Python environment.")

        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        at = AppTest.from_file(app_path)
        at.run(timeout=10)
        self.assertEqual(len(at.exception), 0)

        if hasattr(at.sidebar, "segmented_control") and len(at.sidebar.segmented_control) > 0:
            at.sidebar.segmented_control[0].set_value("☀️ Light")
            at.run(timeout=10)
            self.assertEqual(len(at.exception), 0)

            at.sidebar.segmented_control[0].set_value("🌙 Dark")
            at.run(timeout=10)
            self.assertEqual(len(at.exception), 0)

    def test_full_workflow_lifecycle(self):
        """
        Verify the 18-step workflow specified in Phase 22:
        1. Add tasks
        2. Confirm persistence
        3. Plan schedule with A*
        4. Confirm final cost & states expanded
        5. Confirm planning run stored
        6. Explainability inspection
        7. Record feedback
        8. Confirm feedback persists and adaptation adjustment updates
        9. Re-plan with adaptation model loaded
        10. Confirm history contains runs
        """
        # 1-2. Add tasks & confirm persistence
        t1 = Task(id=101, name="Workflow DSA", duration=2, priority="high", deadline=24, difficulty="high")
        t2 = Task(id=102, name="Workflow AI", duration=3, priority="medium", deadline=72, difficulty="high")
        t3 = Task(id=103, name="Workflow DBMS", duration=1, priority="medium", deadline=48, difficulty="medium")

        for t in [t1, t2, t3]:
            existing = self.db.get_task(t.id)
            if not existing:
                self.db.add_task(t)

        stored = self.db.get_task(101)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.name, "Workflow DSA")

        # 3-5. Plan schedule with A*
        plan_res = execute_planning(
            tasks=[t1, t2, t3],
            planning_start=18,
            available_end=24,
            algorithm="A*",
        )
        self.assertTrue(plan_res["success"])
        self.assertEqual(plan_res["result_state"].cost, 9)
        self.assertGreater(plan_res["expanded"], 0)

        sched_id = self.db.save_schedule(
            problem=plan_res["problem"],
            result_state=plan_res["result_state"],
            algorithm="A*",
            states_expanded=plan_res["expanded"],
        )
        self.assertIsNotNone(sched_id)

        # 6. Verify explanation
        explanation = plan_res["explanation"]
        self.assertIsNotNone(explanation)
        self.assertEqual(len(explanation.task_explanations), 3)
        self.assertIn("FEASIBLE", explanation.task_explanations[0].constraint_status)

        # 7-8. Add feedback & verify adaptation adjustment
        from chronos.adaptation.feedback import FeedbackRecord, POSTPONED
        fb = FeedbackRecord(task_id=101, feedback_type=POSTPONED)
        self.db.save_feedback(fb)

        records = self.db.get_feedback(101)
        self.assertGreaterEqual(len(records), 1)

        model = build_adaptation_model(records)
        profile = model.get_task_profile(101)
        self.assertGreater(profile.postponement_count, 0)
        self.assertGreater(profile.net_adjustment, 0.0)

        # 9. Re-plan with adaptation model
        plan_res_adapted = execute_planning(
            tasks=[t1, t2, t3],
            planning_start=18,
            available_end=24,
            algorithm="A*",
            adaptation_model=model,
        )
        self.assertTrue(plan_res_adapted["success"])
        self.assertIsNotNone(plan_res_adapted["result_state"])

        # 10. Planning history
        history = self.db.get_planning_history()
        self.assertGreaterEqual(len(history), 1)

        # Clean up test tasks
        for tid in [101, 102, 103]:
            self.db.delete_task(tid)


if __name__ == "__main__":
    unittest.main()
