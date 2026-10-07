import unittest
from chronos.models.task import Task
from chronos.models.state import State
from chronos.planning.problem import PlanningProblem
from chronos.planning.heuristic import get_heuristic_breakdown
from chronos.search.astar import astar
from chronos.knowledge import get_default_engine
from chronos.explainability import explain_schedule
from chronos.adaptation import (
    AdaptationModel,
    POSTPONED,
    TOO_DIFFICULT,
    COMPLETED_EARLY,
)


def run_demo():
    print("==================================================")
    print("Chronos AI: Feedback-Based Adaptation Demo")
    print("==================================================")

    # 1. Tasks & Initial Planning Setup
    dsa = Task(1, "DSA", 2, "high", 24, "high")
    ai = Task(2, "AI", 3, "medium", 72, "high")
    dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

    state = State(18, [dsa, ai, dbms], [], 0)
    engine = get_default_engine()
    model = AdaptationModel()

    print("\n--- 1. Initial State & Profile (No Feedback) ---")
    initial_profile = model.get_task_profile(dsa.id)
    print(f"Task DSA Profile:")
    print(f"  Postponements: {initial_profile.postponement_count}")
    print(f"  Difficulty reports: {initial_profile.too_difficult_count}")
    print(f"  Adaptive adjustment: {initial_profile.net_adjustment:+.2f}")

    initial_bd = get_heuristic_breakdown(state, 24, knowledge_engine=engine, adaptation_model=model)
    print(f"Initial Composite Heuristic:")
    print(f"  Workload pressure   : {initial_bd['workload_pressure']:.2f}")
    print(f"  Urgency pressure    : {initial_bd['urgency_pressure']:.2f}")
    print(f"  Knowledge pressure  : {initial_bd['knowledge_pressure']:.2f}")
    print(f"  Adaptation pressure : {initial_bd['adaptation_pressure']:.2f}")
    print(f"  Total heuristic     : {initial_bd['total']:.2f}")

    # 2. Simulate User Feedback Events
    print("\n--- 2. User Records Feedback Events for DSA ---")
    print("  -> User postponed DSA (event 1)")
    model.record_feedback(dsa.id, POSTPONED)
    print("  -> User postponed DSA (event 2)")
    model.record_feedback(dsa.id, POSTPONED)
    print("  -> User postponed DSA (event 3)")
    model.record_feedback(dsa.id, POSTPONED)
    print("  -> User reported DSA was too difficult (event 1)")
    model.record_feedback(dsa.id, TOO_DIFFICULT)
    print("  -> User reported DSA was too difficult (event 2)")
    model.record_feedback(dsa.id, TOO_DIFFICULT)

    # 3. Updated Profile & Scores
    print("\n--- 3. Updated Learned Task Profile ---")
    updated_profile = model.get_task_profile(dsa.id)
    print(f"Task DSA Profile:")
    print(f"  Postponements         : {updated_profile.postponement_count}")
    print(f"  Too-difficult reports : {updated_profile.too_difficult_count}")
    print(f"  Postponement pressure : +{updated_profile.postponement_pressure:.2f}")
    print(f"  Difficulty pressure   : +{updated_profile.difficulty_pressure:.2f}")
    print(f"  Net adaptive adjustment: {updated_profile.net_adjustment:+.2f}")

    # 4. Updated Heuristic Breakdown
    print("\n--- 4. Heuristic Breakdown with Adaptive Pressure ---")
    adapted_bd = get_heuristic_breakdown(state, 24, knowledge_engine=engine, adaptation_model=model)
    print(f"Adapted Composite Heuristic:")
    print(f"  Workload pressure   : {adapted_bd['workload_pressure']:.2f}")
    print(f"  Urgency pressure    : {adapted_bd['urgency_pressure']:.2f}")
    print(f"  Knowledge pressure  : {adapted_bd['knowledge_pressure']:.2f}")
    print(f"  Adaptation pressure : {adapted_bd['adaptation_pressure']:+.2f} (from DSA: {adapted_bd['task_adaptations'][dsa.id]:+.2f})")
    print(f"  Total heuristic     : {adapted_bd['total']:.2f}")

    # 5. Planning & Explainability with Learned Preferences
    print("\n--- 5. A* Plan Explanation Exposing Learned Signals ---")
    problem = PlanningProblem(state, 18, 24)
    result, expanded = astar(problem, adaptation_model=model)

    explanation = explain_schedule(
        problem,
        result,
        knowledge_engine=engine,
        adaptation_model=model,
        states_expanded=expanded,
    )
    print(explanation.to_text())
    print("==================================================")


class TestAdaptationDemo(unittest.TestCase):

    def test_adaptation_demo_flow(self):
        dsa = Task(1, "DSA", 2, "high", 24, "high")
        ai = Task(2, "AI", 3, "medium", 72, "high")
        dbms = Task(3, "DBMS", 1, "medium", 48, "medium")

        state = State(18, [dsa, ai, dbms], [], 0)
        engine = get_default_engine()
        model = AdaptationModel()

        # Initial check
        bd_init = get_heuristic_breakdown(state, 24, knowledge_engine=engine, adaptation_model=model)
        self.assertEqual(bd_init["adaptation_pressure"], 0.0)

        # Record feedback
        model.record_feedback(dsa.id, POSTPONED)
        model.record_feedback(dsa.id, POSTPONED)
        model.record_feedback(dsa.id, POSTPONED)
        model.record_feedback(dsa.id, TOO_DIFFICULT)
        model.record_feedback(dsa.id, TOO_DIFFICULT)

        # Check adapted profile
        prof = model.get_task_profile(dsa.id)
        self.assertEqual(prof.postponement_count, 3)
        self.assertEqual(prof.too_difficult_count, 2)
        self.assertGreater(prof.net_adjustment, 0.0)

        # Check heuristic breakdown
        bd_adapt = get_heuristic_breakdown(state, 24, knowledge_engine=engine, adaptation_model=model)
        self.assertGreater(bd_adapt["adaptation_pressure"], 0.0)
        self.assertGreater(bd_adapt["total"], bd_init["total"])

        # Check explanation
        prob = PlanningProblem(state, 18, 24)
        result, exp = astar(prob, adaptation_model=model)
        expl = explain_schedule(prob, result, knowledge_engine=engine, adaptation_model=model)

        dsa_exp = next(te for te in expl.task_explanations if te.task_id == dsa.id)
        self.assertGreater(len(dsa_exp.adaptation_notes), 0)
        self.assertTrue(any("postponed 3 time(s)" in note for note in dsa_exp.adaptation_notes))


if __name__ == "__main__":
    run_demo()
