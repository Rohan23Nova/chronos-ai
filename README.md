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

### In Progress

- [ ] Evaluation benchmarks

### Planned

- [ ] Planning layer extensions
- [ ] SQLite persistence
- [ ] Streamlit interface
- [ ] Experiments and evaluation

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

## Technology

- Python
- Streamlit
- SQLite
- NumPy / Pandas where useful
- Matplotlib / Plotly where useful

## Project Philosophy

The core AI algorithms are implemented and understood directly rather than
relying on black-box optimization libraries.

The project focuses on building a small but technically meaningful AI
planning system that can be understood, evaluated, and explained.

## Repository Structure

```text
chronos-ai/
├── chronos/
│   ├── models/
│   ├── planning/
│   ├── search/
│   ├── knowledge/
│   ├── constraints/
│   ├── explainability/
│   └── adaptation/
│
├── tests/
├── docs/
└── README.md
```