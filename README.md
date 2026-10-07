# Chronos AI

An Intelligent Personal Planning Agent using Heuristic Search,
Knowledge Representation, Planning, and Explainable AI.

## Project Status

🚧 Under Development

Chronos AI is a semester project for the Artificial Intelligence (INT3120)
course at Manipal University Jaipur.

The goal is to build an intelligent planning agent that generates optimized
personal schedules based on tasks, deadlines, priorities, durations,
constraints, and user preferences.

## AI Approach

Chronos AI is being developed around:

- Intelligent Agents
- Problem Formulation
- State-Space Search
- BFS
- DFS
- Uniform Cost Search
- Greedy Best-First Search
- A* Search
- Domain-Specific Heuristics
- Constraint Handling
- Knowledge Representation
- Rule-Based Reasoning
- Planning
- Explainable AI
- Simple Feedback-Based Adaptation

## Current Progress

### Completed

- [x] Project architecture
- [x] BFS implementation
- [x] DFS implementation
- [x] Task data model
- [x] Schedule entry model
- [x] State representation
- [x] Successor generation
- [x] Hard constraint handling
- [x] PlanningProblem abstraction
- [x] Uniform Cost Search (UCS)
- [x] A* planning engine
- [x] Domain-specific heuristic
- [x] Search comparison and state expansion measurement
- [x] Rule-based knowledge system
- [x] Knowledge-aware heuristic integration
- [x] Explainable scheduling decisions
- [x] Feedback-based adaptation
- [x] SQLite persistence
- [x] Streamlit interface
- [x] Evaluation benchmarks
- [x] Experiments and evaluation

### Planned

- [ ] Planning layer extensions

## Integrated Planning Architecture

Chronos couples symbolic domain knowledge with state-space search:

```text
Knowledge Representation
        ↓
Rule-Based Inference (Forward Chaining)
        ↓
Knowledge-Aware Heuristic
        ↓
A* Search
        ↓
Constraint-Valid Schedule
```

- **Domain Rules**: Derive symbolic properties for pending tasks (`urgency`, `risk`, `deadline_pressure`, `attention`).
- **Knowledge-Aware Heuristic**: Consumes derived task properties alongside workload and deadline pressures to guide A* towards promising scheduling choices. Note that this domain-specific heuristic is designed for guidance and is not claimed to be admissible, nor is A* guaranteed optimal under this heuristic.
- **Mandatory Hard Constraints**: Planning window limits and task deadlines strictly prune infeasible successors during search.
- **Heuristic-Free Baseline**: Uniform Cost Search (UCS) operates solely on path cost $g(n)$, providing a benchmark to evaluate heuristic effects.

## Knowledge Representation & Reasoning

Chronos incorporates a lightweight, deterministic symbolic reasoning subsystem:

- **Symbolic Facts**: Represents relational statements in predicate form `Fact(predicate, entity_id, value)` (e.g., `priority(task, high)`, `deadline_pressure(task, high)`).
- **Domain Rules**: Declarative if-then production rules defining domain dependencies between priority, difficulty, deadlines, urgency, and execution risk.
- **Forward Chaining**: A deterministic deductive inference engine that iteratively fires rules against known facts until reaching a stable state (fixed point).
- **Derived Task Properties**: Infers high-level scheduling properties (such as risk levels, deadline pressure, and immediate attention flags) to inform subsequent planning decisions.

## Search & Evaluation

Chronos supports classical state-space search strategies operating over the `PlanningProblem` abstraction:

- **Uniform Cost Search (UCS)**: Explores state space based on accumulated path cost $g(n)$, prioritizing lower delay and priority-weighted waiting penalties.
- **A* Search**: Guides search using evaluation function $f(n) = g(n) + h(n)$, combining accumulated path cost with domain-specific heuristic estimates.
- **Domain-Specific Heuristic**: Evaluates workload pressure against available window time and task deadline urgency.
- **Search-State Expansion Measurement**: Search algorithms track and report total state expansions, enabling empirical evaluation and comparison between uninformed and informed search.

## Explainable Planning

Chronos features an Explainable AI / Explainable Planning subsystem (`chronos.explainability`) that transforms internal planning states, constraint checks, and symbolic inferences into inspectable, human-readable explanations:

- **Task-Level Reasoning**: Explains why a task was placed at a specific time slot, accounting for its duration, priority, deadline, difficulty, waiting time, and cost contribution.
- **Knowledge-Derived Factors**: Highlights how forward-chained domain facts (`urgency`, `risk`, `deadline_pressure`, `attention`) influenced prioritization.
- **Constraint Explanations**: Diagnoses candidate feasibility against the planning horizon and task deadlines with exact numerical boundaries.
- **Scheduling & Order Reasoning**: Explains pairwise task ordering (e.g., why task A preceded task B) using legitimate, grounded factors such as higher priority, earlier deadline, higher urgency, immediate attention, or mutual delay penalty reduction—never claiming unsupported reasons.
- **Cost Transparency**: Details individual task waiting costs ($w_i \times \text{waiting\_time}$) and total schedule cost.
- **Optional Planning Trace**: A lightweight search trace (`SearchTrace`) captures expanded nodes, candidate acceptances, and pruned/rejected actions with explicit rejection rationales.

> [!NOTE]
> Explanations are strictly grounded in concrete algorithmic decisions and state-space evaluations computed by Chronos. The system does not use black-box language models or claim human-level or causal certainty beyond what the planning algorithms actually compute.

## Feedback-Based Adaptation

Chronos implements a transparent, deterministic feedback-based adaptive preference mechanism (`chronos.adaptation`):

- **Structured Feedback Records**: Captures explicit user feedback events (`completed_on_time`, `completed_early`, `postponed`, `not_completed`, `too_difficult`, `too_easy`, `schedule_acceptable`, `schedule_unacceptable`).
- **Interpretable Statistical Profiles**: Aggregates event counts per task into transparent metrics, including postponement frequency, difficulty complaints, and a normalized reliability score.
- **Bounded Adaptive Pressure**: Derives deterministic scheduling adjustments bounded strictly within `[-2.0, +2.0]`. Tasks repeatedly postponed or marked too difficult receive increased scheduling consideration, whereas tasks consistently completed early or on time receive an appropriate relief discount.
- **Heuristic Influence**: Seamlessly integrates into the A* planning heuristic as an additional term:
  $$\text{total\_heuristic} = \text{workload\_pressure} + \text{urgency\_pressure} + \text{knowledge\_pressure} + \text{adaptation\_pressure}$$
- **Explainable Adaptation**: Learned preferences and historical statistics are exposed directly through the explainability subsystem, detailing exact historical counts and numerical pressures.

> [!NOTE]
> This adaptation subsystem is a lightweight, interpretable preference update mechanism based on empirical user feedback counts. It does not perform black-box statistical model training, neural learning, or reinforcement learning.

## Persistence & Storage

Chronos provides a lightweight, local SQLite persistence layer (`chronos.storage`) using Python's standard library `sqlite3`:

- **Decoupled Architecture**: SQLite operates purely as an external persistence boundary. The core search algorithms (A*, UCS), heuristics, and knowledge reasoning are completely decoupled from database access and can execute in memory without opening a database.
- **Task Management**: Persists, retrieves, updates, and deletes tasks via parameterized SQL queries, mapping rows directly to the standard `Task` dataclass.
- **Feedback History**: Stores user evaluations (`FeedbackRecord`) with automated foreign-key validation and cascading semantics.
- **Schedule & Run History**: Logs generated schedules, individual schedule entries, and planning run performance metrics (`algorithm`, `total_cost`, `states_expanded`, `success`).
- **Adaptation Reconstruction**: Provides `build_adaptation_model(...)` to re-instantiate the exact learned `AdaptationModel` from persisted feedback without duplicating scoring formulas.

> [!NOTE]
> The database layer is strictly for persistent storage and metadata retrieval. It contains zero AI planning, heuristic, or constraint checking logic.

## Streamlit UI

Chronos provides an interactive, desktop-oriented web dashboard (`app.py`) built with Streamlit.

The UI serves strictly as a **presentation and application layer**:
- It collects user parameters, invokes Chronos's underlying algorithms, and visualizes the results.
- **No AI logic resides in `app.py`**; all planning, heuristic evaluations, knowledge rule forward-chaining, explainability generation, and adaptation remain inside the `chronos/` core modules.

### Installation & Launch

1. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the Streamlit application:
   ```bash
   streamlit run app.py
   ```

### Major UI Sections

1. **Dashboard**: High-level overview displaying stored tasks, planning runs, generated schedules, and feedback records, alongside the latest planning run summary.
2. **Tasks**: Manage the task catalogue (view stored tasks, add new tasks with validation, delete tasks, or seed canonical benchmark tasks).
3. **Plan Schedule**: Select tasks, specify planning windows, choose search algorithms (A*, UCS, BFS, DFS), execute state-space search, inspect metrics, and visualize schedule timelines.
4. **Feedback**: Submit structured feedback on tasks (e.g. completed early, postponed, too difficult), update task adaptation profiles, and observe net adaptive heuristic adjustments.
5. **Planning History**: Audit previous planning runs, algorithm comparisons, costs, and state expansions, with drill-down into historical schedules.
6. **Explainability**: Inspect verified explanations for scheduled plans, including task-level scheduling rationales, symbolic derived facts, pairwise ordering decisions, constraint rejections, and search trace data.
7. **Evaluation**: Visual dashboard presenting empirical benchmark results, comparison tables, and generated scaling curves.

## Controlled Evaluation & Benchmarks

Chronos incorporates a dedicated, reproducible evaluation suite (`chronos.evaluation`) measuring search efficiency, solution quality, heuristic impact, feedback adaptation, constraint pruning, and problem scaling.

All reported numbers are produced by actual executions on deterministic synthetic scenarios; no values are fabricated or hard-coded.

### Evaluation Suite Architecture

- **`chronos/evaluation/scenarios.py`**: Deterministic benchmark specifications:
  - **Canonical (3 tasks)**: Benchmark scenario with DSA (2h), AI (3h), and DBMS (1h).
  - **Small (4 tasks)**: Competing priorities with tight early deadlines.
  - **Medium (6 tasks)**: Trade-offs between high-priority items and large low-priority tasks.
  - **Larger (8 tasks)**: High-complexity planning instance with multiple difficulty tiers.
  - **Infeasible (3 tasks)**: Deliberately overconstrained scenario where total duration exceeds available window.
  - **Scaling Sequence (3 to 8 tasks)**: Progressive task counts measuring state-space growth.
- **`chronos/evaluation/metrics.py`**: Structured `ExperimentResult` schema and CSV/JSON serializers.
- **`chronos/evaluation/plots.py`**: Publication-quality plots saved to `evaluation/figures/`.
- **`chronos/evaluation/experiments.py`**: Suite runner and CLI entry point.

### Running Evaluations

Execute the complete evaluation suite via CLI:

```bash
python3 -m chronos.evaluation.experiments
# Or within the virtual environment:
.venv/bin/python -m chronos.evaluation.experiments
```

This prints formatted summary tables, writes `evaluation/results/benchmark_results.json` and `evaluation/results/benchmark_results.csv`, and generates figures in `evaluation/figures/`.

### Core Experiments & Key Findings

1. **Search Algorithm Comparison (A*, UCS, BFS, DFS)**:
   - **Cost Optimality**: A* and UCS find the lowest-cost feasible schedules across all benchmark problems (e.g. Cost = 9.0 on Canonical, Cost = 14.0 on Small).
   - **Suboptimality of Uninformed Search**: DFS finds feasible paths quickly with fewer expansions (4 on Canonical, 18 on Larger) by plunging down deep branches, but returns significantly higher waiting costs (e.g. Cost = 89.0 vs 84.0 on Larger). BFS expands all frontier nodes layer-by-layer, finding suboptimal schedules (Cost = 87.0 on Larger).
   - **Constraint Infeasibility**: On the overconstrained problem, all four algorithms correctly evaluate and report no solution (`solution_found = False`, states expanded = 3).
2. **Knowledge-Aware Heuristic Impact**:
   - Compares A* with symbolic domain rules enabled vs disabled.
   - Forward-chained rules provide rich semantic classifications (`urgency`, `risk`, `attention`) for explainability while maintaining robust search guidance.
3. **Feedback-Based Adaptation**:
   - Applying repeated postponement and difficulty feedback modifies the task's heuristic weight, shifting search priorities and altering node expansion order (expansions increased from 8 to 9 on Canonical).
4. **Hard Constraint Enforcement**:
   - Confirms that invalid candidate actions violating deadlines or planning horizons are strictly pruned by `explain_feasibility` during successor generation.
5. **Scaling Behavior (3 to 8 tasks)**:
   - Evaluates search expansions as task count increases: $3 \to 7$, $4 \to 16$, $5 \to 32$, $6 \to 64$, $7 \to 128$, $8 \to 256$ states expanded ($O(2^n)$ growth), with runtimes scaling smoothly from 0.31 ms to 37.85 ms.

### Methodological Interpretation Caveats

1. **Heuristic Admissibility**: The domain-specific heuristic is designed for guidance and is **not proven admissible**. A* is therefore not guaranteed to find globally optimal schedules in all possible domains.
2. **State Expansions as Primary Metric**: States expanded provides a machine-independent measure of search effort.
3. **Runtime Measurements**: Wall-clock runtimes (ms) are machine-dependent and subject to OS scheduling.
4. **Scope**: The evaluation demonstrates observed empirical behavior on defined benchmarks, not formal universal guarantees.

## Technology

- Python 3.12+
- Streamlit
- SQLite (Standard Library `sqlite3`)
- Pandas
- Matplotlib

## Project Philosophy

The core AI algorithms are implemented and understood directly rather than
relying on black-box optimization libraries.

The project focuses on building a small but technically meaningful AI
planning system that can be understood, evaluated, and explained.

## Repository Structure

```text
chronos-ai/
├── app.py                      # Streamlit interactive application layer
├── requirements.txt            # Project dependencies
├── evaluation/
│   ├── figures/                # Generated experiment plots (PNG)
│   └── results/                # Serialized benchmark results (JSON, CSV)
├── chronos/
│   ├── models/                 # Core data models (Task, State, ScheduleEntry)
│   ├── planning/               # PlanningProblem, heuristics, and successors
│   ├── search/                 # A*, UCS, BFS, and DFS search algorithms
│   ├── knowledge/              # Symbolic facts, domain rules, and RuleEngine
│   ├── constraints/            # Hard constraint feasibility checkers
│   ├── explainability/         # XAI report generator and SearchTrace
│   ├── adaptation/             # FeedbackRecord and AdaptationModel
│   ├── storage/                # SQLite DatabaseManager and persistence
│   ├── ui/                     # Presentation helpers and planning executor
│   └── evaluation/             # Benchmarks, experiments, metrics, and plots
│
├── tests/                      # Comprehensive unit and integration test suite
├── docs/
└── README.md
```