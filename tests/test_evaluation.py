import os
import tempfile
import unittest

from chronos.evaluation.metrics import (
    ExperimentResult,
    results_to_csv,
    results_to_json,
    load_results_from_json,
)
from chronos.evaluation.scenarios import (
    get_canonical_scenario,
    get_small_scenario,
    get_medium_scenario,
    get_larger_scenario,
    get_infeasible_scenario,
    get_scaling_scenarios,
    get_all_benchmark_scenarios,
)
from chronos.evaluation.experiments import (
    run_algorithm_comparison,
    run_knowledge_heuristic_experiment,
    run_adaptation_experiment,
    run_constraint_experiment,
    run_scaling_experiment,
)


class TestEvaluation(unittest.TestCase):

    def test_benchmark_scenarios_deterministic(self):
        """Scenarios should always return identical task lists and horizon properties."""
        s1 = get_canonical_scenario()
        s2 = get_canonical_scenario()
        self.assertEqual(s1.task_count, 3)
        self.assertEqual(s1.task_count, s2.task_count)
        self.assertEqual(s1.planning_start, s2.planning_start)
        self.assertEqual(s1.available_end, s2.available_end)

        # Confirm small, medium, larger scenarios
        small = get_small_scenario()
        self.assertEqual(small.task_count, 4)
        medium = get_medium_scenario()
        self.assertEqual(medium.task_count, 6)
        larger = get_larger_scenario()
        self.assertEqual(larger.task_count, 8)

        # Infeasible scenario properties
        infeasible = get_infeasible_scenario()
        self.assertFalse(infeasible.expected_feasible)
        self.assertGreater(infeasible.total_duration, infeasible.window_size)

        # Scaling scenarios: 6 scenarios (sizes 3 through 8)
        scaling = get_scaling_scenarios()
        self.assertEqual(len(scaling), 6)
        for expected_count, sc in zip(range(3, 9), scaling):
            self.assertEqual(sc.task_count, expected_count)

    def test_all_algorithms_invoked(self):
        """Verify algorithm comparison invokes A*, UCS, BFS, and DFS with valid records."""
        canonical = get_canonical_scenario()
        results = run_algorithm_comparison(scenarios=[canonical])
        self.assertEqual(len(results), 4)

        algorithms_tested = {r.algorithm for r in results}
        self.assertEqual(algorithms_tested, {"A*", "UCS", "BFS", "DFS"})

        for r in results:
            self.assertEqual(r.scenario, canonical.name)
            self.assertEqual(r.task_count, 3)
            self.assertTrue(r.solution_found)
            self.assertIsNotNone(r.final_cost)
            self.assertGreaterEqual(r.states_expanded, 0)
            self.assertGreaterEqual(r.runtime_ms, 0.0)
            self.assertIsNotNone(r.schedule_order)
            self.assertEqual(len(r.schedule_order), 3)

    def test_infeasible_scenario_pruning(self):
        """Verify infeasible scenarios report no solution and no final cost."""
        results = run_constraint_experiment()
        self.assertEqual(len(results), 2)

        feasible_res = results[0]
        self.assertTrue(feasible_res.solution_found)
        self.assertIsNotNone(feasible_res.final_cost)

        infeasible_res = results[1]
        self.assertFalse(infeasible_res.solution_found)
        self.assertIsNone(infeasible_res.final_cost)
        self.assertIsNone(infeasible_res.schedule_order)
        self.assertGreater(infeasible_res.states_expanded, 0)

    def test_knowledge_heuristic_experiment(self):
        """Verify knowledge experiment evaluates both enabled and disabled variants."""
        canonical = get_canonical_scenario()
        results = run_knowledge_heuristic_experiment(scenarios=[canonical])
        self.assertEqual(len(results), 2)

        names = {r.algorithm for r in results}
        self.assertEqual(names, {"A* (Knowledge Enabled)", "A* (Knowledge Disabled)"})

        for r in results:
            self.assertTrue(r.solution_found)
            self.assertIsNotNone(r.final_cost)
            self.assertGreater(r.states_expanded, 0)

    def test_adaptation_experiment(self):
        """Verify adaptation experiment loads and tests baseline vs feedback-adapted A*."""
        results = run_adaptation_experiment()
        self.assertEqual(len(results), 2)

        baseline = results[0]
        adapted = results[1]

        self.assertIn("Baseline", baseline.algorithm)
        self.assertIn("Feedback Adapted", adapted.algorithm)
        self.assertTrue(baseline.solution_found)
        self.assertTrue(adapted.solution_found)
        self.assertGreaterEqual(adapted.states_expanded, baseline.states_expanded)

    def test_scaling_experiment(self):
        """Verify scaling experiment runs across task sizes."""
        scenarios = get_scaling_scenarios()[:3]  # Test first 3 sizes (3, 4, 5)
        results = run_scaling_experiment(scaling_scenarios=scenarios)
        self.assertEqual(len(results), 3)

        for idx, (expected_count, r) in enumerate(zip([3, 4, 5], results)):
            self.assertEqual(r.task_count, expected_count)
            self.assertTrue(r.solution_found)
            self.assertGreater(r.states_expanded, 0)
            self.assertIsNotNone(r.final_cost)

    def test_results_serialization(self):
        """Verify results can be serialized to and loaded from JSON and CSV."""
        sample_results = [
            ExperimentResult(
                experiment_name="test_exp",
                scenario="Canonical",
                algorithm="A*",
                task_count=3,
                solution_found=True,
                final_cost=9.0,
                states_expanded=8,
                runtime_ms=0.5,
                schedule_order=[3, 1, 2],
                notes="Test notes",
            ),
            ExperimentResult(
                experiment_name="test_exp",
                scenario="Infeasible",
                algorithm="A*",
                task_count=3,
                solution_found=False,
                final_cost=None,
                states_expanded=3,
                runtime_ms=0.2,
                schedule_order=None,
                notes="Infeasible note",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "results.json")
            csv_path = os.path.join(tmpdir, "results.csv")

            results_to_json(sample_results, json_path)
            self.assertTrue(os.path.exists(json_path))

            loaded = load_results_from_json(json_path)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0].algorithm, "A*")
            self.assertEqual(loaded[0].final_cost, 9.0)
            self.assertIsNone(loaded[1].final_cost)

            results_to_csv(sample_results, csv_path)
            self.assertTrue(os.path.exists(csv_path))


if __name__ == "__main__":
    unittest.main()
