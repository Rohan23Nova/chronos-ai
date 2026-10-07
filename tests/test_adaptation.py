import unittest
from chronos.adaptation import (
    COMPLETED_EARLY,
    COMPLETED_ON_TIME,
    NOT_COMPLETED,
    POSTPONED,
    SCHEDULE_ACCEPTABLE,
    SCHEDULE_UNACCEPTABLE,
    TOO_DIFFICULT,
    TOO_EASY,
    AdaptationModel,
    FeedbackRecord,
    FeedbackType,
    TaskProfile,
)


class TestAdaptation(unittest.TestCase):

    def setUp(self):
        self.model = AdaptationModel()

    def test_empty_feedback_history_produces_neutral_adjustment(self):
        # 1. Empty feedback history produces neutral adjustment (0.0)
        profile = self.model.get_task_profile(1)
        self.assertEqual(profile.task_id, 1)
        self.assertEqual(profile.postponement_count, 0)
        self.assertEqual(profile.net_adjustment, 0.0)
        self.assertEqual(self.model.get_adjustment(1), 0.0)

    def test_recording_postponed_feedback_changes_task_profile(self):
        # 2. Recording postponed feedback changes the task profile
        rec = self.model.record_feedback(task_id=1, feedback_type=POSTPONED)
        self.assertIsInstance(rec, FeedbackRecord)
        self.assertEqual(rec.task_id, 1)
        self.assertEqual(rec.feedback_type, POSTPONED)

        profile = self.model.get_task_profile(1)
        self.assertEqual(profile.postponement_count, 1)
        self.assertGreater(profile.postponement_pressure, 0.0)
        self.assertGreater(profile.net_adjustment, 0.0)

    def test_repeated_postponement_increases_postponement_pressure(self):
        # 3. Repeated postponement increases postponement pressure
        self.model.record_feedback(1, POSTPONED)
        adj_1 = self.model.get_adjustment(1)

        self.model.record_feedback(1, POSTPONED)
        adj_2 = self.model.get_adjustment(1)

        self.model.record_feedback(1, POSTPONED)
        adj_3 = self.model.get_adjustment(1)

        self.assertGreater(adj_2, adj_1)
        self.assertGreater(adj_3, adj_2)
        profile = self.model.get_task_profile(1)
        self.assertEqual(profile.postponement_count, 3)

    def test_too_difficult_feedback_changes_difficulty_pressure(self):
        # 4. Too-difficult feedback changes difficulty pressure
        self.model.record_feedback(2, TOO_DIFFICULT)
        profile_1 = self.model.get_task_profile(2)
        diff_1 = profile_1.difficulty_pressure
        self.assertEqual(profile_1.too_difficult_count, 1)
        self.assertGreater(diff_1, 0.0)

        self.model.record_feedback(2, TOO_DIFFICULT)
        profile_2 = self.model.get_task_profile(2)
        self.assertEqual(profile_2.too_difficult_count, 2)
        self.assertGreater(profile_2.difficulty_pressure, diff_1)

    def test_completed_early_feedback_changes_learned_profile_appropriately(self):
        # 5. Completed-early feedback changes the learned profile appropriately (reduces pressure)
        self.model.record_feedback(3, COMPLETED_EARLY)
        profile = self.model.get_task_profile(3)
        self.assertEqual(profile.completed_early_count, 1)
        # Should reduce net adjustment
        self.assertLess(profile.net_adjustment, 0.0)
        self.assertGreater(profile.reliability_score, 0.0)

    def test_successful_feedback_does_not_create_arbitrary_negative_values(self):
        # 6. Successful feedback does not create arbitrary negative values (capped)
        for _ in range(10):
            self.model.record_feedback(3, COMPLETED_EARLY)
            self.model.record_feedback(3, COMPLETED_ON_TIME)

        profile = self.model.get_task_profile(3)
        # Relief is bounded to -0.8, clamped within [-2.0, +2.0]
        self.assertGreaterEqual(profile.net_adjustment, -2.0)
        self.assertGreaterEqual(profile.net_adjustment, -0.8)

    def test_scores_remain_within_defined_bounds(self):
        # 7. Scores remain within the defined bounds [-2.0, +2.0]
        for _ in range(20):
            self.model.record_feedback(4, POSTPONED)
            self.model.record_feedback(4, TOO_DIFFICULT)
            self.model.record_feedback(4, NOT_COMPLETED)
            self.model.record_feedback(4, SCHEDULE_UNACCEPTABLE)

        adj = self.model.get_adjustment(4)
        self.assertLessEqual(adj, 2.0)
        self.assertGreaterEqual(adj, -2.0)

    def test_same_feedback_history_produces_same_result(self):
        # 8. Deterministic: same feedback history produces the same result
        model_a = AdaptationModel()
        model_b = AdaptationModel()

        events = [
            (1, POSTPONED),
            (1, TOO_DIFFICULT),
            (2, COMPLETED_EARLY),
            (1, POSTPONED),
            (2, COMPLETED_ON_TIME),
        ]

        for task_id, fb_type in events:
            model_a.record_feedback(task_id, fb_type)
            model_b.record_feedback(task_id, fb_type)

        self.assertEqual(model_a.get_adjustment(1), model_b.get_adjustment(1))
        self.assertEqual(model_a.get_adjustment(2), model_b.get_adjustment(2))

        prof_a = model_a.get_task_profile(1)
        prof_b = model_b.get_task_profile(1)
        self.assertEqual(prof_a.postponement_count, prof_b.postponement_count)
        self.assertEqual(prof_a.net_adjustment, prof_b.net_adjustment)

    def test_different_tasks_maintain_separate_profiles(self):
        # 9. Different tasks maintain separate profiles
        self.model.record_feedback(1, POSTPONED)
        self.model.record_feedback(1, POSTPONED)
        self.model.record_feedback(2, COMPLETED_EARLY)

        prof_1 = self.model.get_task_profile(1)
        prof_2 = self.model.get_task_profile(2)

        self.assertEqual(prof_1.postponement_count, 2)
        self.assertEqual(prof_1.completed_early_count, 0)
        self.assertGreater(prof_1.net_adjustment, 0.0)

        self.assertEqual(prof_2.postponement_count, 0)
        self.assertEqual(prof_2.completed_early_count, 1)
        self.assertLess(prof_2.net_adjustment, 0.0)

    def test_reset_works_correctly(self):
        # 10. Reset works correctly
        self.model.record_feedback(1, POSTPONED)
        self.model.record_feedback(2, TOO_DIFFICULT)

        self.assertEqual(len(self.model.get_feedback_history()), 2)
        self.assertNotEqual(self.model.get_adjustment(1), 0.0)

        self.model.reset()

        self.assertEqual(len(self.model.get_feedback_history()), 0)
        self.assertEqual(self.model.get_adjustment(1), 0.0)
        self.assertEqual(self.model.get_adjustment(2), 0.0)


if __name__ == "__main__":
    unittest.main()
