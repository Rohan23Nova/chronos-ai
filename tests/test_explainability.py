import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.models.schedule import ScheduleEntry
from chronos.planning.problem import PlanningProblem
from chronos.search.astar import astar
from chronos.constraints.checker import explain_feasibility
from chronos.knowledge import Fact, get_default_engine
from chronos.explainability import (
    CandidateEvaluation,
    OrderingExplanation,
    ScheduleExplanation,
    SearchTrace,
    TaskExplanation,
    evaluate_candidate,
    explain_schedule,
    explain_task_ordering,
)


class TestExplainability(unittest.TestCase):

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

        self.engine = get_default_engine()

    def test_final_schedule_can_be_explained(self):
        # 1. A final schedule can be explained
        result, expanded = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        self.assertIsInstance(explanation, ScheduleExplanation)
        self.assertEqual(explanation.total_cost, 9)
        self.assertIn("All 3 tasks were successfully scheduled", explanation.problem_summary)

        text = explanation.to_text()
        self.assertIn("CHRONOS PLAN EXPLANATION", text)
        self.assertIn("DBMS: 18-19", text)
        self.assertIn("DSA: 19-21", text)
        self.assertIn("AI: 21-24", text)

    def test_every_scheduled_task_has_an_explanation(self):
        # 2. Every scheduled task has an explanation
        result, _ = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        self.assertEqual(len(explanation.task_explanations), 3)
        explained_ids = [te.task_id for te in explanation.task_explanations]
        self.assertEqual(explained_ids, [3, 1, 2])

        for te in explanation.task_explanations:
            self.assertIsInstance(te, TaskExplanation)
            self.assertGreater(len(te.reasons), 0)

    def test_explanation_contains_real_task_properties(self):
        # 3. Explanation contains real task properties
        result, _ = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        # Inspect DSA (Task 1)
        dsa_exp = next(te for te in explanation.task_explanations if te.task_id == 1)
        self.assertEqual(dsa_exp.task_name, "DSA")
        self.assertEqual(dsa_exp.duration, 2)
        self.assertEqual(dsa_exp.priority, "high")
        self.assertEqual(dsa_exp.deadline, 24)
        self.assertEqual(dsa_exp.difficulty, "high")
        self.assertEqual(dsa_exp.start_time, 19)
        self.assertEqual(dsa_exp.end_time, 21)
        self.assertEqual(dsa_exp.waiting_time, 1)
        self.assertEqual(dsa_exp.cost_contribution, 3)

        # Inspect DBMS (Task 3)
        dbms_exp = next(te for te in explanation.task_explanations if te.task_id == 3)
        self.assertEqual(dbms_exp.task_name, "DBMS")
        self.assertEqual(dbms_exp.duration, 1)
        self.assertEqual(dbms_exp.priority, "medium")
        self.assertEqual(dbms_exp.deadline, 48)
        self.assertEqual(dbms_exp.difficulty, "medium")
        self.assertEqual(dbms_exp.start_time, 18)
        self.assertEqual(dbms_exp.end_time, 19)
        self.assertEqual(dbms_exp.waiting_time, 0)
        self.assertEqual(dbms_exp.cost_contribution, 0)

    def test_knowledge_derived_facts_appear_when_applicable(self):
        # 4. Knowledge-derived facts appear when applicable (Step 13)
        result, _ = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        dsa_exp = next(te for te in explanation.task_explanations if te.task_id == 1)
        derived_predicates = {f.predicate for f in dsa_exp.derived_facts}

        self.assertIn("urgency", derived_predicates)
        self.assertIn("risk", derived_predicates)
        self.assertIn("deadline_pressure", derived_predicates)
        self.assertIn("attention", derived_predicates)

        self.assertIn(Fact("urgency", 1, "high"), dsa_exp.derived_facts)
        self.assertIn(Fact("risk", 1, "high"), dsa_exp.derived_facts)
        self.assertIn(Fact("deadline_pressure", 1, "high"), dsa_exp.derived_facts)
        self.assertIn(Fact("attention", 1, "immediate"), dsa_exp.derived_facts)

        # Check that reasons text reflects derived knowledge
        self.assertTrue(
            any("immediate attention" in r.lower() for r in dsa_exp.reasons)
        )

    def test_hard_constraint_status_is_represented(self):
        # 5. Hard constraint status is represented
        result, _ = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        for te in explanation.task_explanations:
            self.assertEqual(te.constraint_status, "FEASIBLE")

    def test_ordering_explanations_based_on_actual_properties(self):
        # 6. Ordering explanations are based on actual properties
        result, _ = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        self.assertGreater(len(explanation.ordering_explanations), 0)

        # DSA before AI
        dsa_ai = next(
            oe for oe in explanation.ordering_explanations
            if oe.preceding_task_id == 1 and oe.following_task_id == 2
        )
        dsa_ai_reasons_str = " ".join(dsa_ai.reasons)
        self.assertIn("higher priority", dsa_ai_reasons_str)
        self.assertIn("earlier deadline", dsa_ai_reasons_str)
        self.assertIn("higher urgency", dsa_ai_reasons_str)
        self.assertIn("immediate attention", dsa_ai_reasons_str)

        # DBMS before DSA
        dbms_dsa = next(
            oe for oe in explanation.ordering_explanations
            if oe.preceding_task_id == 3 and oe.following_task_id == 1
        )
        dbms_dsa_reasons_str = " ".join(dbms_dsa.reasons)
        self.assertIn("shorter duration", dbms_dsa_reasons_str)
        self.assertIn("delay penalty", dbms_dsa_reasons_str)

    def test_no_explanation_claims_false_reasons(self):
        # 7. No explanation claims a false reason
        result, _ = astar(self.problem)
        explanation = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        # DBMS before DSA: DBMS has medium priority, DSA has high priority.
        # DBMS must NOT claim higher priority!
        dbms_dsa = next(
            oe for oe in explanation.ordering_explanations
            if oe.preceding_task_id == 3 and oe.following_task_id == 1
        )
        for r in dbms_dsa.reasons:
            self.assertNotIn("higher priority", r)
            self.assertNotIn("earlier deadline", r)

        # DBMS before AI: Both have medium priority.
        # Neither should claim higher priority!
        dbms_ai = next(
            oe for oe in explanation.ordering_explanations
            if oe.preceding_task_id == 3 and oe.following_task_id == 2
        )
        for r in dbms_ai.reasons:
            self.assertNotIn("higher priority", r)

    def test_infeasible_candidates_produce_meaningful_reasons(self):
        # 8. Infeasible candidates can produce meaningful rejection reasons
        # Task that exceeds planning horizon
        t_window = Task(4, "BigJob", 7, "low", 50, "low")
        eval_window = evaluate_candidate(t_window, 18, 24)
        self.assertFalse(eval_window.feasible)
        self.assertFalse(eval_window.fits_window)
        self.assertTrue(eval_window.meets_deadline)
        self.assertTrue(any("exceeding the planning horizon of 24" in r for r in eval_window.reasons))

        # Task that violates deadline
        t_deadline = Task(5, "LateJob", 2, "low", 19, "low")
        eval_dl = evaluate_candidate(t_deadline, 18, 24)
        self.assertFalse(eval_dl.feasible)
        self.assertTrue(eval_dl.fits_window)
        self.assertFalse(eval_dl.meets_deadline)
        self.assertTrue(any("violating deadline of 19" in r for r in eval_dl.reasons))

    def test_explanation_does_not_modify_final_schedule(self):
        # 9. Explanation generation does not modify the final schedule
        result, expanded = astar(self.problem)
        original_schedule = list(result.schedule)
        original_cost = result.cost
        original_time = result.current_time

        _ = explain_schedule(self.problem, result, knowledge_engine=self.engine)

        self.assertEqual(result.schedule, original_schedule)
        self.assertEqual(result.cost, original_cost)
        self.assertEqual(result.current_time, original_time)

    def test_planner_behavior_remains_unchanged(self):
        # 10. Existing planner behavior remains unchanged
        result, expanded = astar(self.problem)
        self.assertIsNotNone(result)
        self.assertEqual(result.cost, 9)
        self.assertEqual(expanded, 8)
        self.assertEqual([e.task_id for e in result.schedule], [3, 1, 2])

    def test_constraint_cases_step12(self):
        # Step 12: Specific test cases
        # Case 1: Task that fits the planning window
        t1 = Task(10, "FitsBoth", 2, "high", 24, "high")
        diag1 = explain_feasibility(t1, 18, 24)
        self.assertTrue(diag1["feasible"])
        self.assertTrue(diag1["fits_window"])
        self.assertTrue(diag1["meets_deadline"])
        self.assertIn("fits within planning horizon", diag1["reasons"][0])

        # Case 2: Task that exceeds available time
        t2 = Task(11, "TooLong", 7, "medium", 50, "medium")
        diag2 = explain_feasibility(t2, 18, 24)
        self.assertFalse(diag2["feasible"])
        self.assertFalse(diag2["fits_window"])
        self.assertTrue(diag2["meets_deadline"])
        self.assertIn("exceeding the planning horizon of 24", diag2["reasons"][0])

        # Case 3: Task that violates deadline
        t3 = Task(12, "PastDeadline", 2, "low", 19, "low")
        diag3 = explain_feasibility(t3, 18, 24)
        self.assertFalse(diag3["feasible"])
        self.assertTrue(diag3["fits_window"])
        self.assertFalse(diag3["meets_deadline"])
        self.assertIn("violating deadline of 19", diag3["reasons"][0])

        # Boundary Case A: end_time == available_end
        t4 = Task(13, "ExactWindow", 6, "medium", 24, "medium")
        diag4 = explain_feasibility(t4, 18, 24)
        self.assertTrue(diag4["feasible"])
        self.assertEqual(diag4["end_time"], 24)
        self.assertTrue(diag4["fits_window"])

        # Boundary Case B: end_time == deadline
        t5 = Task(14, "ExactDeadline", 3, "medium", 21, "medium")
        diag5 = explain_feasibility(t5, 18, 24)
        self.assertTrue(diag5["feasible"])
        self.assertEqual(diag5["end_time"], 21)
        self.assertTrue(diag5["meets_deadline"])

    def test_search_trace_integration(self):
        # Step 10: Search trace captures expansions and candidates
        trace = SearchTrace()
        result, expanded = astar(self.problem, trace=trace)

        self.assertEqual(trace.expansions, expanded)
        self.assertGreater(len(trace.steps), 0)

        # On canonical problem all examined branches fit window
        self.assertEqual(len(trace.rejected_candidates), 0)

        # Now test search trace on a problem with pruned candidates
        t1 = Task(20, "Short", 2, "high", 24, "high")
        t2 = Task(21, "Tight", 5, "medium", 24, "medium")
        prob_prune = PlanningProblem(State(18, [t1, t2], [], 0), 18, 24)

        trace_prune = SearchTrace()
        res_prune, _ = astar(prob_prune, trace=trace_prune)
        self.assertIsNone(res_prune)
        self.assertGreater(len(trace_prune.rejected_candidates), 0)

        # Explain the infeasible schedule
        explanation = explain_schedule(prob_prune, res_prune, search_trace=trace_prune)
        self.assertIn("No feasible schedule found", explanation.problem_summary)
        self.assertGreater(len(explanation.rejected_candidates), 0)


def run_explainability_demo():
    dsa = Task(1, "DSA", 2, "high", 24, "high")
    ai = Task(2, "AI", 3, "medium", 72, "high")
    dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

    initial_state = State(18, [dsa, ai, dbms], [], 0)
    problem = PlanningProblem(initial_state, 18, 24)

    trace = SearchTrace()
    result, expanded = astar(problem, trace=trace)

    engine = get_default_engine()
    explanation = explain_schedule(
        problem,
        result,
        knowledge_engine=engine,
        search_trace=trace,
        states_expanded=expanded,
    )

    print(explanation.to_text())


if __name__ == "__main__":
    unittest.main()
