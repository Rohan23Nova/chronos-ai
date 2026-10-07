import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.models.schedule import ScheduleEntry
from chronos.planning.heuristic import (
    heuristic,
    get_heuristic_breakdown,
    priority_weight,
)
from chronos.knowledge import get_default_engine, Fact


class TestHeuristic(unittest.TestCase):

    def setUp(self):
        self.dsa = Task(1, "DSA", 2, "high", 24, "high")
        self.ai = Task(2, "AI", 3, "medium", 72, "high")
        self.dbms = Task(3, "DBMS", 1, "medium", 48, "medium")
        self.engine = get_default_engine()

    def test_existing_workload_pressure_behavior(self):
        # 1. Existing workload-pressure behavior still works
        # Total duration = 2 + 3 + 1 = 6
        # Available time = 22 - 18 = 4 -> workload pressure = 6 - 4 = 2.0
        state = State(18, [self.dsa, self.ai, self.dbms], [], 0)
        breakdown = get_heuristic_breakdown(state, available_end=22, knowledge_engine=None)
        self.assertEqual(breakdown["workload_pressure"], 2.0)

        # Available time = 30 - 18 = 12 -> workload pressure = 0
        breakdown_plenty = get_heuristic_breakdown(state, available_end=30, knowledge_engine=None)
        self.assertEqual(breakdown_plenty["workload_pressure"], 0.0)

    def test_high_priority_receives_high_urgency(self):
        # 2. A high-priority task receives high urgency
        task_high = Task(1, "High Task", 2, "high", 30, "medium")
        task_low = Task(2, "Low Task", 2, "low", 30, "medium")

        state_high = State(18, [task_high], [], 0)
        state_low = State(18, [task_low], [], 0)

        h_high = heuristic(state_high, available_end=30, knowledge_engine=None)
        h_low = heuristic(state_low, available_end=30, knowledge_engine=None)

        self.assertGreater(h_high, h_low)
        self.assertEqual(priority_weight("high"), 3)
        self.assertEqual(priority_weight("low"), 1)

    def test_high_difficulty_receives_high_risk(self):
        # 3. A high-difficulty task receives high risk
        # Far deadline (100) so deadline pressure does not trigger
        task_diff_high = Task(1, "Hard Task", 2, "medium", 100, "high")
        task_diff_med = Task(2, "Med Task", 2, "medium", 100, "medium")

        state_diff_high = State(18, [task_diff_high], [], 0)
        state_diff_med = State(18, [task_diff_med], [], 0)

        b_high = get_heuristic_breakdown(state_diff_high, 100, knowledge_engine=self.engine)
        b_med = get_heuristic_breakdown(state_diff_med, 100, knowledge_engine=self.engine)

        # High difficulty derives risk=high (adds 0.5), medium derives risk=medium (adds 0.2)
        self.assertGreater(b_high["knowledge_pressure"], b_med["knowledge_pressure"])
        self.assertIn(Fact("risk", 1, "high"), b_high["task_facts"][1])
        self.assertIn(Fact("risk", 2, "medium"), b_med["task_facts"][2])

    def test_high_urgency_and_deadline_pressure_immediate_attention(self):
        # 4. A task with high urgency and high deadline pressure produces immediate-attention reasoning
        # DSA at time 18: priority="high" and deadline=24 (time left: 6 <= threshold 6)
        state = State(18, [self.dsa], [], 0)
        breakdown = get_heuristic_breakdown(state, 24, knowledge_engine=self.engine)

        facts = breakdown["task_facts"][self.dsa.id]
        self.assertIn(Fact("urgency", 1, "high"), facts)
        self.assertIn(Fact("deadline_pressure", 1, "high"), facts)
        self.assertIn(Fact("attention", 1, "immediate"), facts)
        # Immediate attention (2.0) + risk high (0.5) = 2.5 knowledge pressure
        self.assertGreaterEqual(breakdown["knowledge_pressure"], 2.0)

    def test_heuristic_consumes_derived_knowledge(self):
        # 5. The heuristic can consume derived knowledge
        state = State(18, [self.dsa, self.ai, self.dbms], [], 0)

        h_without_knowledge = heuristic(state, 24, knowledge_engine=None)
        h_with_knowledge = heuristic(state, 24, knowledge_engine=self.engine)

        self.assertGreater(h_with_knowledge, h_without_knowledge)

    def test_completed_tasks_do_not_contribute_to_heuristic(self):
        # 6. Completed tasks do not contribute to the remaining-task heuristic
        state_all = State(18, [self.dsa, self.ai, self.dbms], [], 0)
        h_all = heuristic(state_all, 24, knowledge_engine=self.engine)

        # DSA has been scheduled; only AI and DBMS remain
        state_partial = State(
            20,
            [self.ai, self.dbms],
            [ScheduleEntry(task_id=1, start_time=18, end_time=20)],
            0,
        )
        h_partial = heuristic(state_partial, 24, knowledge_engine=self.engine)

        # DSA's immediate attention and risk are eliminated from h_partial
        self.assertLess(h_partial, h_all)

        # Goal state with no remaining tasks returns exactly 0
        state_goal = State(
            24,
            [],
            [
                ScheduleEntry(task_id=3, start_time=18, end_time=19),
                ScheduleEntry(task_id=1, start_time=19, end_time=21),
                ScheduleEntry(task_id=2, start_time=21, end_time=24),
            ],
            9,
        )
        self.assertEqual(heuristic(state_goal, 24, knowledge_engine=self.engine), 0)

    def test_heuristic_remains_deterministic(self):
        # 7. The heuristic remains deterministic
        state = State(18, [self.dsa, self.ai, self.dbms], [], 0)

        h1 = heuristic(state, 24, knowledge_engine=self.engine)
        h2 = heuristic(state, 24, knowledge_engine=self.engine)
        h3 = heuristic(state, 24, knowledge_engine=self.engine)

        self.assertEqual(h1, h2)
        self.assertEqual(h2, h3)

    def test_heuristic_backward_compatibility_without_engine(self):
        # 8. The heuristic works when no Knowledge Engine is provided
        state = State(18, [self.dsa, self.ai, self.dbms], [], 0)

        # Direct legacy call: heuristic(state, available_end)
        h_legacy = heuristic(state, 24)
        h_none = heuristic(state, 24, knowledge_engine=None)

        self.assertEqual(h_legacy, h_none)
        self.assertGreater(h_legacy, 0)

    def test_knowledge_trace_breakdown(self):
        # Step 10 trace: Task -> initial facts -> derived facts -> heuristic contribution
        state = State(18, [self.dsa], [], 0)
        breakdown = get_heuristic_breakdown(state, available_end=24, knowledge_engine=self.engine)

        self.assertIn(self.dsa.id, breakdown["task_facts"])
        facts = breakdown["task_facts"][self.dsa.id]

        # Verify initial and derived facts exist in trace
        predicates = {f.predicate for f in facts}
        self.assertTrue({"priority", "difficulty", "deadline"}.issubset(predicates))
        self.assertTrue({"urgency", "risk", "deadline_pressure", "attention"}.issubset(predicates))

        # Check total composition
        expected_total = (
            breakdown["workload_pressure"]
            + breakdown["urgency_pressure"]
            + breakdown["knowledge_pressure"]
        )
        self.assertAlmostEqual(breakdown["total"], expected_total)

    def test_heuristic_without_adaptation_remains_valid(self):
        # 1. Existing heuristic behavior remains valid without adaptation
        state = State(18, [self.dsa, self.ai, self.dbms], [], 0)
        h_base = heuristic(state, 24, knowledge_engine=self.engine)
        bd = get_heuristic_breakdown(state, 24, knowledge_engine=self.engine)

        self.assertEqual(bd["adaptation_pressure"], 0)
        self.assertEqual(h_base, bd["total"])

    def test_adaptation_can_be_disabled(self):
        # 2. Adaptation can be disabled
        state = State(18, [self.dsa], [], 0)
        from chronos.adaptation import AdaptationModel, POSTPONED
        model = AdaptationModel()
        model.record_feedback(self.dsa.id, POSTPONED)

        h_with_model = heuristic(state, 24, knowledge_engine=self.engine, adaptation_model=model)
        h_disabled = heuristic(state, 24, knowledge_engine=self.engine, adaptation_model=None)

        self.assertGreater(h_with_model, h_disabled)

    def test_feedback_changes_adaptation_pressure_and_direction(self):
        # 3 & 4. Feedback changes adaptation pressure in a deterministic direction
        state = State(18, [self.dsa], [], 0)
        from chronos.adaptation import AdaptationModel, POSTPONED, COMPLETED_EARLY
        model_pos = AdaptationModel()
        model_pos.record_feedback(self.dsa.id, POSTPONED)
        model_pos.record_feedback(self.dsa.id, POSTPONED)

        bd_pos = get_heuristic_breakdown(state, 24, knowledge_engine=self.engine, adaptation_model=model_pos)
        self.assertGreater(bd_pos["adaptation_pressure"], 0)
        self.assertIn(self.dsa.id, bd_pos["task_adaptations"])

        # Model with early completion
        model_neg = AdaptationModel()
        model_neg.record_feedback(self.dsa.id, COMPLETED_EARLY)
        bd_neg = get_heuristic_breakdown(state, 24, knowledge_engine=self.engine, adaptation_model=model_neg)
        self.assertLess(bd_neg["adaptation_pressure"], 0)

    def test_hard_constraints_remain_unaffected_by_adaptation(self):
        # 5. Hard constraints remain unaffected by adaptation pressure
        from chronos.adaptation import AdaptationModel, POSTPONED
        from chronos.planning.problem import PlanningProblem
        from chronos.search.astar import astar

        model = AdaptationModel()
        for _ in range(5):
            model.record_feedback(self.dsa.id, POSTPONED)
            model.record_feedback(self.ai.id, POSTPONED)
            model.record_feedback(self.dbms.id, POSTPONED)

        prob = PlanningProblem(
            initial_state=State(18, [self.dsa, self.ai, self.dbms], [], 0),
            planning_start=18,
            available_end=24,
        )
        res, exp = astar(prob, adaptation_model=model)
        self.assertIsNotNone(res)
        self.assertEqual(len(res.remaining_tasks), 0)
        # Verify hard constraints strictly satisfied
        self.assertLessEqual(res.schedule[-1].end_time, 24)
        for entry in res.schedule:
            task = next(t for t in [self.dsa, self.ai, self.dbms] if t.id == entry.task_id)
            self.assertLessEqual(entry.end_time, task.deadline)


if __name__ == "__main__":
    unittest.main()