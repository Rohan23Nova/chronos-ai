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

### In Progress

- [ ] Cost model
- [ ] A* planning engine

### Planned

- [ ] Scheduling heuristic
- [ ] Constraint handling
- [ ] Rule-based knowledge system
- [ ] Planning layer
- [ ] Explainable scheduling decisions
- [ ] Feedback-based adaptation
- [ ] SQLite persistence
- [ ] Streamlit interface
- [ ] Experiments and evaluation

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
│   ├── heuristic/
│   ├── explain/
│   └── learning/
│
├── tests/
├── docs/
└── README.md