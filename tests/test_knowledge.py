import unittest
from chronos.models.task import Task
from chronos.knowledge import (
    Fact,
    Rule,
    RuleEngine,
    get_default_engine,
    task_to_facts,
    has_fact,
    conclude,
)


class TestKnowledgeRepresentation(unittest.TestCase):

    def setUp(self):
        self.engine = get_default_engine()

    def test_high_priority_derives_high_urgency(self):
        # 1. High-priority task derives high urgency
        task = Task(1, "DSA", duration=2, priority="high", deadline=50, difficulty="low")
        facts = self.engine.infer(task, current_time=18)
        self.assertIn(Fact("urgency", 1, "high"), facts)
        self.assertNotIn(Fact("urgency", 1, "low"), facts)

    def test_low_priority_derives_low_urgency(self):
        # 2. Low-priority task derives low urgency
        task = Task(2, "Reading", duration=1, priority="low", deadline=50, difficulty="low")
        facts = self.engine.infer(task, current_time=18)
        self.assertIn(Fact("urgency", 2, "low"), facts)
        self.assertNotIn(Fact("urgency", 2, "high"), facts)

    def test_high_difficulty_derives_high_risk(self):
        # 3. High-difficulty task derives high risk
        task = Task(3, "AI Systems", duration=3, priority="medium", deadline=50, difficulty="high")
        facts = self.engine.infer(task, current_time=18)
        self.assertIn(Fact("risk", 3, "high"), facts)
        self.assertNotIn(Fact("risk", 3, "medium"), facts)

    def test_medium_difficulty_derives_medium_risk(self):
        # 4. Medium-difficulty task derives medium risk
        task = Task(4, "DBMS Lab", duration=1, priority="medium", deadline=50, difficulty="medium")
        facts = self.engine.infer(task, current_time=18)
        self.assertIn(Fact("risk", 4, "medium"), facts)
        self.assertNotIn(Fact("risk", 4, "high"), facts)

    def test_near_deadline_derives_high_deadline_pressure(self):
        # 5. Near deadline derives high deadline pressure
        # deadline 24 at current_time 18 -> time_to_deadline = 6 <= threshold 6
        near_task = Task(5, "Urgent Project", duration=2, priority="medium", deadline=24, difficulty="low")
        near_facts = self.engine.infer(near_task, current_time=18)
        self.assertIn(Fact("deadline_pressure", 5, "high"), near_facts)

        # deadline 50 at current_time 18 -> time_to_deadline = 32 > threshold 6
        far_task = Task(6, "Relaxed Project", duration=2, priority="medium", deadline=50, difficulty="low")
        far_facts = self.engine.infer(far_task, current_time=18)
        self.assertNotIn(Fact("deadline_pressure", 6, "high"), far_facts)

    def test_high_urgency_and_deadline_pressure_derives_immediate_attention(self):
        # 6. High urgency + high deadline pressure derives immediate attention
        # Requires multi-step forward chaining:
        # Cycle 1: priority(high) -> urgency(high), time_to_deadline(6) -> deadline_pressure(high)
        # Cycle 2: urgency(high) AND deadline_pressure(high) -> attention(immediate)
        urgent_task = Task(7, "DSA Exam", duration=2, priority="high", deadline=24, difficulty="high")
        facts = self.engine.infer(urgent_task, current_time=18)

        self.assertIn(Fact("urgency", 7, "high"), facts)
        self.assertIn(Fact("deadline_pressure", 7, "high"), facts)
        self.assertIn(Fact("attention", 7, "immediate"), facts)

    def test_rules_reach_stable_state_and_do_not_loop_indefinitely(self):
        # 7. Rules reach a stable state and do not loop indefinitely
        # Even with cyclic or redundant rules, forward chaining halts at a fixed point
        cyclic_rule_1 = Rule(
            name="cycle_1",
            conditions=[has_fact("a", True)],
            conclusion=conclude("b", True),
        )
        cyclic_rule_2 = Rule(
            name="cycle_2",
            conditions=[has_fact("b", True)],
            conclusion=conclude("a", True),
        )

        test_engine = RuleEngine([cyclic_rule_1, cyclic_rule_2])
        initial_facts = {Fact("a", 100, True)}

        # Must terminate cleanly without infinite loop
        final_facts = test_engine.forward_chain(initial_facts)
        self.assertIn(Fact("a", 100, True), final_facts)
        self.assertIn(Fact("b", 100, True), final_facts)

        # Running again on the result produces the exact same set
        second_run = test_engine.forward_chain(final_facts)
        self.assertEqual(final_facts, second_run)

    def test_facts_are_not_duplicated(self):
        # 8. Facts are not duplicated
        task = Task(8, "Test Task", duration=2, priority="high", deadline=24, difficulty="high")
        initial = task_to_facts(task, current_time=18)
        # Add duplicate entries to input list
        initial_with_dups = list(initial) + list(initial)

        derived = self.engine.forward_chain(initial_with_dups)
        self.assertIsInstance(derived, set)

        # Check there is exactly one Fact("urgency", 8, "high")
        urgency_facts = [f for f in derived if f.predicate == "urgency" and f.entity_id == 8]
        self.assertEqual(len(urgency_facts), 1)

    def test_task_with_no_matching_rules_has_no_unrelated_conclusions(self):
        # 9. A task with no matching rules does not receive unrelated conclusions
        # priority="medium", difficulty="low", far deadline (100)
        calm_task = Task(9, "Casual Reading", duration=1, priority="medium", deadline=100, difficulty="low")
        initial = task_to_facts(calm_task, current_time=18)
        derived = self.engine.get_derived_facts(initial)

        # None of the default rules fire
        self.assertEqual(len(derived), 0)

    def test_different_tasks_remain_logically_separate(self):
        # 10. Different tasks remain logically separate
        task_a = Task(10, "Critical Task", duration=2, priority="high", deadline=24, difficulty="high")
        task_b = Task(20, "Low Task", duration=1, priority="low", deadline=80, difficulty="medium")

        all_facts = self.engine.infer_all([task_a, task_b], current_time=18)

        # Task A properties
        self.assertIn(Fact("urgency", 10, "high"), all_facts)
        self.assertIn(Fact("deadline_pressure", 10, "high"), all_facts)
        self.assertIn(Fact("attention", 10, "immediate"), all_facts)
        self.assertIn(Fact("risk", 10, "high"), all_facts)

        # Task B properties
        self.assertIn(Fact("urgency", 20, "low"), all_facts)
        self.assertIn(Fact("risk", 20, "medium"), all_facts)

        # Verify cross-contamination did NOT occur:
        # Task B must NOT have high urgency, high deadline pressure, or immediate attention
        self.assertNotIn(Fact("urgency", 20, "high"), all_facts)
        self.assertNotIn(Fact("deadline_pressure", 20, "high"), all_facts)
        self.assertNotIn(Fact("attention", 20, "immediate"), all_facts)


if __name__ == "__main__":
    unittest.main()
