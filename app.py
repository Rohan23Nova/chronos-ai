"""
Chronos AI - Streamlit Web Application
An Intelligent Personal Planning Agent presentation layer backed by
state-space search, symbolic knowledge reasoning, explainable AI,
feedback-based adaptation, and SQLite persistent storage.

Redesigned with Linear-inspired minimalism, Notion clarity, and dual light/dark themes.
"""

import os
from typing import List, Optional

import streamlit as st
import pandas as pd

from chronos.models.task import Task
from chronos.storage import DatabaseManager, build_adaptation_model
from chronos.ui.helpers import (
    PRIORITY_MAP,
    PRIORITY_REVERSE_MAP,
    DIFFICULTY_MAP,
    DIFFICULTY_REVERSE_MAP,
    FEEDBACK_TYPE_MAP,
    FEEDBACK_TYPE_REVERSE_MAP,
    validate_task_input,
    execute_planning,
    format_schedule_rows,
    format_task_rows,
    format_feedback_rows,
)
from chronos.adaptation.feedback import FeedbackRecord
from chronos.ui.theme import get_theme, ALGORITHM_COLORS
from chronos.ui.styles import get_theme_css
from chronos.ui.components import (
    render_header,
    render_badge,
    render_empty_state,
    render_timeline_slot,
    render_card,
)


# ---------------------------------------------------------------------------
# Page Configuration & Database Setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Chronos AI - Personal Planning Agent",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_database() -> DatabaseManager:
    """Initialize and return the persistent database manager."""
    db = DatabaseManager()
    db.initialize_database()
    return db


db = get_database()


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

if "latest_plan" not in st.session_state:
    st.session_state["latest_plan"] = None

if "feedback_task_id" not in st.session_state:
    st.session_state["feedback_task_id"] = None

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Dark"


# ---------------------------------------------------------------------------
# Sidebar & Theme Configuration
# ---------------------------------------------------------------------------

# Theme Switcher (using segmented control to keep radio[0] as navigation anchor)
theme_selection = st.sidebar.segmented_control(
    "Theme Mode",
    options=["🌙 Dark", "☀️ Light"],
    default="🌙 Dark" if st.session_state["theme_mode"] == "Dark" else "☀️ Light",
    label_visibility="collapsed",
)

active_theme = "Light" if theme_selection == "☀️ Light" else "Dark"
st.session_state["theme_mode"] = active_theme

# Inject Theme CSS Styles
st.markdown(get_theme_css(active_theme), unsafe_allow_html=True)

# Sidebar Header & Branding
st.sidebar.markdown(
    """
    <div style='margin-bottom: 0.5rem;'>
        <div style='font-size: 1.35rem; font-weight: 750; letter-spacing: -0.02em;'>⏱️ Chronos AI</div>
        <div style='font-size: 0.82rem; color: var(--chronos-text-secondary); margin-top: -2px;'>Intelligent Planning Agent</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Architectural Badges
st.sidebar.markdown(
    """
    <div style='margin-bottom: 1.1rem; line-height: 1.8;'>
        <span class='chronos-brand-pill'>A* & UCS</span>
        <span class='chronos-brand-pill'>Knowledge Rules</span>
        <span class='chronos-brand-pill'>Explainable AI</span>
        <span class='chronos-brand-pill'>Adaptive</span>
        <span class='chronos-brand-pill'>SQLite</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Primary Navigation (Preserved as sidebar radio[0] for test compatibility)
nav_selection = st.sidebar.radio(
    "Navigation",
    options=[
        "Dashboard",
        "Tasks",
        "Plan Schedule",
        "Feedback",
        "Planning History",
        "Explainability",
        "Evaluation",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='font-size: 0.8rem; color: var(--chronos-text-secondary); line-height: 1.5;'>
        <div style='font-weight: 650; color: var(--chronos-text-primary); margin-bottom: 0.3rem;'>AI Architecture</div>
        • State-space graph search<br/>
        • Knowledge-guided heuristic<br/>
        • Forward-chaining rules<br/>
        • Hard temporal constraints<br/>
        • Deterministic adaptation<br/>
        • Persistent SQLite storage
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# 1. Dashboard View
# ---------------------------------------------------------------------------

if nav_selection == "Dashboard":
    render_header(
        title="System Dashboard",
        subtitle="Real-time summary of stored tasks, generated schedules, and planning activity.",
        badges=[
            ("State-Space Planner", "primary"),
            ("Knowledge Engine", "cyan"),
            ("Persistent Storage", "success"),
        ],
    )

    tasks = db.get_all_tasks()
    history = db.get_planning_history()
    all_feedback = db.get_all_feedback()
    successful_runs = sum(1 for r in history if r["success"])

    # High-level Metrics Row
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Stored Tasks", len(tasks), help="Total active tasks stored in SQLite database")
    with mcol2:
        st.metric("Planning Runs", len(history), help="Historical search executions")
    with mcol3:
        st.metric("Schedules Found", successful_runs, help="Feasible schedules successfully computed")
    with mcol4:
        st.metric("Feedback Records", len(all_feedback), help="User feedback events recorded for adaptation")

    st.markdown("---")

    if not history:
        render_empty_state(
            icon="⏱️",
            title="Welcome to Chronos AI",
            description=(
                "No planning runs recorded yet. Start by populating your task catalogue, "
                "then run the search engine to compute an optimal schedule."
            ),
            action_hint="Navigate to Tasks in the sidebar to add or seed benchmark tasks.",
        )
    else:
        latest = history[0]
        status_label = "SOLVED" if latest["success"] else "INFEASIBLE"
        status_badge_type = "success" if latest["success"] else "danger"

        st.subheader("Latest Planning Run")

        lcol1, lcol2, lcol3, lcol4, lcol5 = st.columns(5)
        with lcol1:
            st.metric("Algorithm", latest["algorithm"])
        with lcol2:
            st.metric("Search Status", status_label)
        with lcol3:
            st.metric(
                "Final Waiting Cost",
                f"{latest['total_cost']:.1f}" if latest["total_cost"] is not None else "N/A",
            )
        with lcol4:
            st.metric(
                "States Expanded",
                latest["states_expanded"] if latest["states_expanded"] is not None else 0,
            )
        with lcol5:
            st.metric("Run ID", f"#{latest['id']}")

        st.caption(f"Executed at: {latest['created_at']}")

        if latest["schedule_id"]:
            sched_data = db.get_schedule(latest["schedule_id"])
            if sched_data and sched_data["entries"]:
                st.markdown("#### Latest Generated Schedule")
                task_map = {t.id: t for t in tasks}

                # Visual Timeline Preview
                for entry in sched_data["entries"]:
                    t = task_map.get(entry.task_id)
                    render_timeline_slot(
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        task_name=t.name if t else f"Task #{entry.task_id}",
                        priority=t.priority if t else "medium",
                        difficulty=t.difficulty if t else "medium",
                        deadline=t.deadline if t else None,
                    )

                # Tabular Details
                sched_rows = []
                for idx, entry in enumerate(sched_data["entries"], start=1):
                    t = task_map.get(entry.task_id)
                    sched_rows.append({
                        "Order": idx,
                        "Task ID": entry.task_id,
                        "Task Name": t.name if t else f"Task #{entry.task_id}",
                        "Start Time": f"{entry.start_time:02d}:00",
                        "End Time": f"{entry.end_time:02d}:00",
                        "Duration": f"{entry.end_time - entry.start_time}h",
                        "Priority": t.priority.capitalize() if t else "-",
                        "Deadline": f"Slot {t.deadline}" if t else "-",
                    })
                with st.expander("View Tabular Schedule Data", expanded=False):
                    st.dataframe(pd.DataFrame(sched_rows), width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# 2. Tasks Management View
# ---------------------------------------------------------------------------

elif nav_selection == "Tasks":
    render_header(
        title="Task Management",
        subtitle="Manage stored tasks, durations, deadlines, and priorities for the planning agent.",
        badges=[
            ("SQLite Persisted", "success"),
            ("Hard Constraints", "warning"),
        ],
    )

    tasks = db.get_all_tasks()
    existing_ids = {t.id for t in tasks}

    tab_catalogue, tab_add = st.tabs(["📋 Task Catalogue", "➕ Add New Task"])

    with tab_catalogue:
        col_hdr, col_seed = st.columns([3.5, 1.5])
        with col_hdr:
            st.subheader(f"Stored Tasks Catalogue ({len(tasks)})")
        with col_seed:
            if st.button("🌱 Seed Canonical Tasks", help="Populate canonical benchmark tasks (DSA, AI, DBMS)"):
                canonical_tasks = [
                    Task(id=1, name="DSA", duration=2, priority="high", deadline=24, difficulty="high"),
                    Task(id=2, name="AI", duration=3, priority="medium", deadline=72, difficulty="high"),
                    Task(id=3, name="DBMS", duration=1, priority="medium", deadline=48, difficulty="medium"),
                ]
                for ct in canonical_tasks:
                    if ct.id not in existing_ids:
                        db.add_task(ct)
                st.success("Canonical tasks seeded successfully!")
                st.rerun()

        if tasks:
            task_df = pd.DataFrame(format_task_rows(tasks))
            st.dataframe(task_df, width="stretch", hide_index=True)

            st.markdown("---")
            st.subheader("Delete Task")
            del_col1, del_col2 = st.columns([3.5, 1.5])
            with del_col1:
                task_to_delete = st.selectbox(
                    "Select task to remove",
                    options=tasks,
                    format_func=lambda t: f"#{t.id} - {t.name} (Duration: {t.duration}h, Deadline: Slot {t.deadline})",
                )
            with del_col2:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete Task", type="secondary"):
                    if task_to_delete:
                        db.delete_task(task_to_delete.id)
                        st.success(f"Task #{task_to_delete.id} ('{task_to_delete.name}') deleted.")
                        st.rerun()
        else:
            render_empty_state(
                icon="📋",
                title="No Tasks Found",
                description="The task database is currently empty. Add tasks manually or click 'Seed Canonical Tasks' above.",
                action_hint="Seed the canonical 3 tasks to immediately reproduce benchmark experiments.",
            )

    with tab_add:
        st.subheader("Add a New Task")
        suggested_id = (max(existing_ids) + 1) if existing_ids else 1

        with st.form("add_task_form", clear_on_submit=False):
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                form_id = st.number_input("Task ID", min_value=1, value=suggested_id, step=1)
                form_name = st.text_input("Task Name", placeholder="e.g., Computer Networks Lab")
                form_duration = st.number_input("Duration (hours)", min_value=1, value=2, step=1)
            with fcol2:
                form_priority = st.selectbox("Priority", options=["Low", "Medium", "High"], index=2)
                form_difficulty = st.selectbox("Difficulty", options=["Low", "Medium", "High"], index=1)
                form_deadline = st.number_input("Deadline (time slot)", min_value=1, value=24, step=1)

            submit_task = st.form_submit_button("Add Task", type="primary")

        if submit_task:
            priority_val = PRIORITY_MAP[form_priority]
            difficulty_val = DIFFICULTY_MAP[form_difficulty]
            is_valid, error_msg = validate_task_input(
                task_id=form_id,
                name=form_name,
                duration=form_duration,
                priority=priority_val,
                difficulty=difficulty_val,
                deadline=form_deadline,
                existing_ids=existing_ids,
            )

            if not is_valid:
                st.error(f"Validation Error: {error_msg}")
            else:
                new_task = Task(
                    id=form_id,
                    name=form_name.strip(),
                    duration=form_duration,
                    priority=priority_val,
                    deadline=form_deadline,
                    difficulty=difficulty_val,
                )
                db.add_task(new_task)
                st.success(f"Task #{new_task.id} ('{new_task.name}') successfully added!")
                st.rerun()


# ---------------------------------------------------------------------------
# 3. Plan Schedule View
# ---------------------------------------------------------------------------

elif nav_selection == "Plan Schedule":
    render_header(
        title="Plan Schedule",
        subtitle="Configure planning horizon and solve state-space scheduling using search algorithms.",
        badges=[
            ("A* & UCS", "primary"),
            ("Zero Hallucination", "cyan"),
            ("Deterministic", "success"),
        ],
    )

    tasks = db.get_all_tasks()

    if not tasks:
        st.warning("⚠️ No tasks available in the database. Please add or seed tasks in the **Tasks** section first.")
    else:
        st.subheader("Planning Configuration")
        cfg_col1, cfg_col2, cfg_col3, cfg_col4 = st.columns([3, 1, 1, 1.5])

        with cfg_col1:
            selected_tasks = st.multiselect(
                "Select Tasks to Schedule",
                options=tasks,
                default=tasks,
                format_func=lambda t: f"#{t.id} {t.name} (Dur: {t.duration}h, Pri: {t.priority}, Ddl: {t.deadline})",
            )
        with cfg_col2:
            planning_start = st.number_input("Planning Start", min_value=0, max_value=200, value=18, step=1)
        with cfg_col3:
            available_end = st.number_input("Available End", min_value=1, max_value=200, value=24, step=1)
        with cfg_col4:
            algorithm = st.selectbox(
                "Search Algorithm",
                options=["A*", "UCS", "BFS", "DFS"],
                index=0,
                help="A* uses knowledge rules and adaptation; UCS is uninformed cost search; BFS/DFS are uninformed.",
            )

        if algorithm == "A*":
            st.info(
                "💡 **A* Search**: Guided by the knowledge-aware heuristic, evaluating deadline pressure, "
                "risk, and learned user feedback adjustments from persistent storage."
            )
        elif algorithm == "UCS":
            st.info(
                "⚙️ **Uniform Cost Search (UCS)**: Explores state space strictly ordered by accumulated "
                "waiting cost g(n) without heuristic guidance."
            )

        plan_button = st.button("🚀 Generate Schedule", type="primary")

        if plan_button:
            if not selected_tasks:
                st.error("Please select at least one task to schedule.")
            elif available_end <= planning_start:
                st.error(f"Available end ({available_end}) must be strictly greater than planning start ({planning_start}).")
            else:
                with st.spinner(f"Running {algorithm} search..."):
                    # Load adaptation model from persisted feedback
                    feedback_records = db.get_all_feedback()
                    adaptation_model = build_adaptation_model(feedback_records) if algorithm == "A*" else None

                    try:
                        plan_res = execute_planning(
                            tasks=selected_tasks,
                            planning_start=planning_start,
                            available_end=available_end,
                            algorithm=algorithm,
                            adaptation_model=adaptation_model,
                        )

                        # Persist schedule and run in SQLite
                        saved_sched_id = db.save_schedule(
                            problem=plan_res["problem"],
                            result_state=plan_res["result_state"],
                            algorithm=algorithm,
                            states_expanded=plan_res["expanded"],
                        )
                        plan_res["saved_schedule_id"] = saved_sched_id
                        st.session_state["latest_plan"] = plan_res

                    except Exception as e:
                        st.error(f"Planning execution error: {str(e)}")
                        st.session_state["latest_plan"] = None

        # Display results from current or active session plan
        active_plan = st.session_state.get("latest_plan")
        if active_plan is not None:
            st.markdown("---")
            if active_plan["success"]:
                st.success(f"✅ Feasible schedule successfully generated with **{active_plan['algorithm']}**!")

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Algorithm", active_plan["algorithm"])
                with m2:
                    st.metric("Final Cost", f"{active_plan['result_state'].cost:.1f}")
                with m3:
                    st.metric("States Expanded", active_plan["expanded"])
                with m4:
                    st.metric("Tasks Scheduled", len(active_plan["result_state"].schedule))

                # Visual Timeline
                st.subheader("Schedule Timeline")
                task_map = {t.id: t for t in tasks}
                for entry in active_plan["result_state"].schedule:
                    t = task_map.get(entry.task_id)
                    render_timeline_slot(
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        task_name=t.name if t else f"Task #{entry.task_id}",
                        priority=t.priority if t else "medium",
                        difficulty=t.difficulty if t else "medium",
                        deadline=t.deadline if t else None,
                    )

                st.subheader("Tabular Schedule")
                sched_rows = format_schedule_rows(active_plan["result_state"], tasks)
                st.dataframe(pd.DataFrame(sched_rows), width="stretch", hide_index=True)

                st.info("🔎 Inspect why tasks were scheduled in this exact order in the **Explainability** section.")

            else:
                st.error(
                    f"❌ No feasible schedule found using **{active_plan['algorithm']}**.\n\n"
                    f"All candidate paths violated deadlines or exceeded the available planning window "
                    f"[{active_plan['problem'].planning_start}, {active_plan['problem'].available_end}]."
                )
                st.metric("States Expanded before failure", active_plan["expanded"])


# ---------------------------------------------------------------------------
# 4. Feedback & Adaptation View
# ---------------------------------------------------------------------------

elif nav_selection == "Feedback":
    render_header(
        title="Adaptive Feedback & Learning",
        subtitle="Deterministic preference adaptation from user feedback without neural networks or LLMs.",
        badges=[
            ("Interpretable", "primary"),
            ("Bounded [-2, +2]", "cyan"),
            ("Deterministic", "success"),
        ],
    )

    tasks = db.get_all_tasks()
    all_feedback = db.get_all_feedback()
    model = build_adaptation_model(all_feedback)

    if not tasks:
        st.warning("No tasks stored in the database. Please add tasks before recording feedback.")
    else:
        tab_record, tab_profiles, tab_history = st.tabs([
            "✍️ Record Feedback",
            "📊 Task Adaptation Profiles",
            "📜 Feedback Log",
        ])

        with tab_record:
            st.subheader("Record Feedback for a Task")

            with st.form("feedback_form"):
                fcol1, fcol2 = st.columns(2)
                with fcol1:
                    selected_task = st.selectbox(
                        "Task",
                        options=tasks,
                        format_func=lambda t: f"#{t.id} - {t.name} (Duration: {t.duration}h, Priority: {t.priority})",
                    )
                    feedback_label = st.selectbox(
                        "Feedback Type",
                        options=list(FEEDBACK_TYPE_MAP.keys()),
                        index=0,
                    )
                    rating = st.slider("Satisfaction Rating (1-5)", min_value=1.0, max_value=5.0, value=4.0, step=0.5)

                with fcol2:
                    scheduled_dur = st.number_input("Scheduled Duration (hours)", min_value=1, value=selected_task.duration, step=1)
                    actual_dur = st.number_input("Actual Duration (hours)", min_value=1, value=selected_task.duration, step=1)
                    comment = st.text_input("Comment (Optional)", placeholder="e.g., Task finished ahead of schedule")

                submit_feedback = st.form_submit_button("💾 Save Feedback", type="primary")

            if submit_feedback:
                fb_record = FeedbackRecord(
                    task_id=selected_task.id,
                    feedback_type=FEEDBACK_TYPE_MAP[feedback_label],
                    rating=rating,
                    scheduled_duration=scheduled_dur,
                    actual_duration=actual_dur,
                    comment=comment.strip() if comment else None,
                )
                db.save_feedback(fb_record)
                st.success(f"Feedback recorded for Task #{selected_task.id} ('{selected_task.name}')!")
                st.rerun()

        with tab_profiles:
            st.subheader("Learned Task Adaptation Signals")
            st.markdown(
                "Feedback updates interpretable statistics (postponement pressure, difficulty pressure, "
                "reliability) which derive bounded heuristic adjustments in `[-2.0, +2.0]`."
            )

            profile_task = st.selectbox(
                "Select task to inspect profile",
                options=tasks,
                format_func=lambda t: f"#{t.id} - {t.name}",
            )

            profile = model.get_task_profile(profile_task.id)

            pcol1, pcol2, pcol3, pcol4 = st.columns(4)
            with pcol1:
                st.metric("Net Adjustment", f"{profile.net_adjustment:+.2f}")
            with pcol2:
                st.metric("Postponement Pressure", f"+{profile.postponement_pressure:.2f}")
            with pcol3:
                st.metric("Difficulty Pressure", f"{profile.difficulty_pressure:+.2f}")
            with pcol4:
                st.metric("Reliability Score", f"{profile.reliability_score:.2f}")

            st.markdown("#### Feedback Frequency Breakdown")
            f_counts = {
                "Completed On Time": profile.completed_on_time_count,
                "Completed Early": profile.completed_early_count,
                "Postponed": profile.postponement_count,
                "Not Completed": profile.not_completed_count,
                "Too Difficult": profile.too_difficult_count,
                "Too Easy": profile.too_easy_count,
                "Schedule Acceptable": profile.schedule_acceptable_count,
                "Schedule Unacceptable": profile.schedule_unacceptable_count,
            }
            count_df = pd.DataFrame([{"Event": k, "Count": v} for k, v in f_counts.items()])
            st.dataframe(count_df, width="stretch", hide_index=True)

        with tab_history:
            st.subheader(f"Stored Feedback Records ({len(all_feedback)})")
            if all_feedback:
                fb_df = pd.DataFrame(format_feedback_rows(all_feedback, tasks))
                st.dataframe(fb_df, width="stretch", hide_index=True)
            else:
                render_empty_state(
                    icon="📜",
                    title="No Feedback Saved",
                    description="No user feedback entries exist in the database. Use 'Record Feedback' to log execution outcomes.",
                )


# ---------------------------------------------------------------------------
# 5. Planning History View
# ---------------------------------------------------------------------------

elif nav_selection == "Planning History":
    render_header(
        title="Planning History",
        subtitle="Audit log of past planning runs, algorithm selections, costs, and state expansions.",
        badges=[
            ("Audit Trail", "neutral"),
            ("SQLite Persisted", "success"),
        ],
    )

    history = db.get_planning_history()
    tasks = db.get_all_tasks()
    task_map = {t.id: t.name for t in tasks}

    if not history:
        render_empty_state(
            icon="📜",
            title="No Planning History",
            description="No planning runs stored in the database yet. Generate a schedule in 'Plan Schedule' to log a run.",
        )
    else:
        st.subheader(f"Historical Runs ({len(history)})")
        hist_rows = []
        for r in history:
            hist_rows.append({
                "Run ID": r["id"],
                "Date / Time": r["created_at"],
                "Algorithm": r["algorithm"],
                "Success": "Yes" if r["success"] else "No",
                "Final Cost": f"{r['total_cost']:.1f}" if r["total_cost"] is not None else "-",
                "States Expanded": r["states_expanded"],
                "Schedule ID": r["schedule_id"] if r["schedule_id"] else "-",
            })
        st.dataframe(pd.DataFrame(hist_rows), width="stretch", hide_index=True)

        st.markdown("---")
        st.subheader("Inspect Historical Schedule")
        runs_with_sched = [r for r in history if r["schedule_id"]]
        if runs_with_sched:
            selected_run = st.selectbox(
                "Select Planning Run",
                options=runs_with_sched,
                format_func=lambda r: f"Run #{r['id']} ({r['algorithm']}) - {r['created_at']} - Cost: {r['total_cost']}",
            )

            if selected_run:
                sched_data = db.get_schedule(selected_run["schedule_id"])
                if sched_data:
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        st.metric("Planning Window", f"[{sched_data['planning_start']}, {sched_data['available_end']}]")
                    with sc2:
                        st.metric("Total Cost", f"{sched_data['total_cost']:.1f}")
                    with sc3:
                        st.metric("States Expanded", sched_data["states_expanded"])

                    entries_rows = []
                    for idx, entry in enumerate(sched_data["entries"], start=1):
                        entries_rows.append({
                            "Order": idx,
                            "Task ID": entry.task_id,
                            "Task Name": task_map.get(entry.task_id, f"Task #{entry.task_id}"),
                            "Start Time": f"{entry.start_time:02d}:00",
                            "End Time": f"{entry.end_time:02d}:00",
                            "Duration": f"{entry.end_time - entry.start_time}h",
                        })
                    st.dataframe(pd.DataFrame(entries_rows), width="stretch", hide_index=True)
        else:
            st.info("No successful schedules with saved entries.")


# ---------------------------------------------------------------------------
# 6. Explainability View
# ---------------------------------------------------------------------------

elif nav_selection == "Explainability":
    render_header(
        title="Explainable AI (XAI) & Plan Inspection",
        subtitle="Inspect verified explanations of task orderings, constraint checks, derived facts, and pruning.",
        badges=[
            ("XAI Core", "primary"),
            ("Rule-Grounded", "cyan"),
            ("Constraint-Audited", "success"),
        ],
    )

    active_plan = st.session_state.get("latest_plan")

    if active_plan is None:
        render_empty_state(
            icon="🔎",
            title="No Active Plan to Explain",
            description="Generate a schedule in 'Plan Schedule' to view its explanation, or load the canonical benchmark below.",
        )

        if st.button("🧪 Load Canonical 3-Task Explanation", type="secondary"):
            tasks = [
                Task(id=1, name="DSA", duration=2, priority="high", deadline=24, difficulty="high"),
                Task(id=2, name="AI", duration=3, priority="medium", deadline=72, difficulty="high"),
                Task(id=3, name="DBMS", duration=1, priority="medium", deadline=48, difficulty="medium"),
            ]
            plan_res = execute_planning(
                tasks=tasks,
                planning_start=18,
                available_end=24,
                algorithm="A*",
            )
            st.session_state["latest_plan"] = plan_res
            st.rerun()

    else:
        explanation = active_plan["explanation"]

        st.subheader("Plan Feasibility & Problem Summary")
        if active_plan["success"]:
            st.success(f"**Feasible Plan**: {explanation.problem_summary}")
        else:
            st.error(f"**Infeasible Plan**: {explanation.problem_summary}")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Algorithm", active_plan["algorithm"])
        with m2:
            st.metric(
                "Total Waiting Cost",
                f"{explanation.total_cost:.1f}" if explanation.total_cost != float("inf") else "∞",
            )
        with m3:
            st.metric("Planning Window", f"[{explanation.planning_start}, {explanation.available_end}]")
        with m4:
            st.metric(
                "States Expanded",
                explanation.states_expanded if explanation.states_expanded is not None else 0,
            )

        st.markdown("---")

        tab_tasks, tab_ordering, tab_rejections, tab_trace = st.tabs([
            "📌 Task-Level Explanations",
            "↔️ Pairwise Ordering Decisions",
            "🚫 Constraint Checks & Pruning",
            "🔍 Search Trace & Raw Report",
        ])

        with tab_tasks:
            st.subheader("Task-Level Explanations")
            if explanation.task_explanations:
                for te in explanation.task_explanations:
                    with st.expander(
                        f"**{te.task_name}** (#{te.task_id}) — Slot [{te.start_time}:00 – {te.end_time}:00]",
                        expanded=True,
                    ):
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.write(f"**Duration:** {te.duration}h")
                            st.write(f"**Priority:** {te.priority.capitalize()}")
                        with c2:
                            st.write(f"**Deadline:** Slot {te.deadline}")
                            st.write(f"**Difficulty:** {te.difficulty.capitalize()}")
                        with c3:
                            st.write(f"**Waiting Time:** {te.waiting_time}h")
                            st.write(f"**Cost Contribution:** {te.cost_contribution:.1f}")
                        with c4:
                            st.write(f"**Constraint Status:** `{te.constraint_status}`")
                            st.write(f"**Adaptive Adj:** {te.adaptation_adjustment:+.2f}")

                        st.markdown("**Symbolic Derived Facts:**")
                        if te.derived_facts:
                            fact_tags = " ".join([
                                render_badge(f"{f.predicate}={f.value}", "cyan")
                                for f in te.derived_facts
                            ])
                            st.markdown(fact_tags, unsafe_allow_html=True)
                        else:
                            st.caption("None derived")

                        st.markdown("**Scheduling Rationale:**")
                        for r in te.reasons:
                            st.markdown(f"- {r}")

                        if te.adaptation_notes:
                            st.markdown("**Adaptive Feedback Notes:**")
                            for an in te.adaptation_notes:
                                st.markdown(f"- 📈 {an}")
            else:
                st.info("No task explanations available (plan was infeasible).")

        with tab_ordering:
            st.subheader("Pairwise Task Ordering Decisions")
            if explanation.ordering_explanations:
                for oe in explanation.ordering_explanations:
                    st.markdown(
                        f"#### Why **{oe.preceding_task_name}** was scheduled before **{oe.following_task_name}**:"
                    )
                    for r in oe.reasons:
                        st.markdown(f"- {r}")
            else:
                st.info("No pairwise orderings available.")

        with tab_rejections:
            st.subheader("Pruning & Hard Constraint Rejections")
            if explanation.rejected_candidates:
                st.write(f"Pruned **{len(explanation.rejected_candidates)}** infeasible branch candidates:")
                rej_rows = []
                for rc in explanation.rejected_candidates:
                    rej_rows.append({
                        "Task ID": rc.task_id,
                        "Task Name": rc.task_name,
                        "Evaluated Start": rc.start_time,
                        "Finish Time": rc.end_time,
                        "Deadline": rc.deadline,
                        "Fits Window": "Yes" if rc.fits_window else "No",
                        "Meets Deadline": "Yes" if rc.meets_deadline else "No",
                        "Reason": "; ".join(rc.reasons),
                    })
                st.dataframe(pd.DataFrame(rej_rows), width="stretch", hide_index=True)
            else:
                st.success("No candidate actions were pruned during this planning run.")

        with tab_trace:
            st.subheader("Search Trace & Complete Text Explanation")
            trace = active_plan.get("trace")
            if trace is not None:
                st.write(f"**Search Expansions:** {trace.expansions}")
                st.write(f"**Candidate Decisions Evaluated:** {len(trace.steps)}")

            with st.expander("📄 Full Text Explanation Report", expanded=False):
                st.code(explanation.to_text(), language="text")


# ---------------------------------------------------------------------------
# 7. Evaluation & Benchmarks View
# ---------------------------------------------------------------------------

elif nav_selection == "Evaluation":
    render_header(
        title="Evaluation & Benchmarks",
        subtitle="Empirical evaluation of search algorithms, knowledge rules, feedback adaptation, constraints, and scaling.",
        badges=[
            ("Reproducible", "primary"),
            ("Scientific AI", "cyan"),
            ("Admissibility Note", "warning"),
        ],
    )

    results_file = os.path.join("evaluation", "results", "benchmark_results.json")
    figures_dir = os.path.join("evaluation", "figures")

    col_btn, col_info = st.columns([1.5, 4])
    with col_btn:
        if st.button("⚡ Run / Refresh Benchmarks", type="primary"):
            with st.spinner("Executing evaluation benchmarks and generating theme plots..."):
                from chronos.evaluation.experiments import run_all_experiments
                from chronos.evaluation.plots import generate_all_plots
                all_results = run_all_experiments(save_results=True, generate_figures=True)
                generate_all_plots(all_results, figures_dir=figures_dir, theme_mode=active_theme)
                st.success("Benchmarks executed successfully!")
                st.rerun()

    st.info(
        "🔬 **Methodological Principles & Caveats**:\n\n"
        "- **Empirical Measurements**: All numbers represent real measured runs from synthetic, reproducible benchmarks.\n"
        "- **Heuristic Admissibility**: The domain-specific heuristic is designed for guidance and is **not proven admissible**. A* is not guaranteed globally optimal.\n"
        "- **State Expansions**: States expanded is the primary machine-independent metric for comparing search effort.\n"
        "- **Runtime**: Measured in milliseconds via high-resolution timers and is machine-dependent."
    )

    if not os.path.exists(results_file):
        st.warning("No benchmark results found on disk. Click **Run / Refresh Benchmarks** above to generate them.")
    else:
        from chronos.evaluation.metrics import load_results_from_json
        from chronos.evaluation.plots import generate_all_plots

        bench_results = load_results_from_json(results_file)

        # Check for theme-specific figure; generate on demand if missing
        theme_alg_plot = os.path.join(figures_dir, f"algorithm_comparison_{active_theme.lower()}.png")
        if not os.path.exists(theme_alg_plot):
            generate_all_plots(bench_results, figures_dir=figures_dir, theme_mode=active_theme)

        tab_alg, tab_kn, tab_adapt, tab_cons, tab_scale = st.tabs([
            "1️⃣ Algorithm Comparison",
            "2️⃣ Knowledge Heuristic",
            "3️⃣ Feedback Adaptation",
            "4️⃣ Constraints",
            "5️⃣ Scaling",
        ])

        with tab_alg:
            st.subheader("Experiment 1: Search Algorithm Comparison")
            st.markdown("Comparing A*, UCS, BFS, and DFS on identical PlanningProblem scenarios.")
            alg_data = [r.to_dict() for r in bench_results if r.experiment_name == "algorithm_comparison"]
            if alg_data:
                st.dataframe(pd.DataFrame(alg_data), width="stretch", hide_index=True)

            alg_plot = (
                theme_alg_plot
                if os.path.exists(theme_alg_plot)
                else os.path.join(figures_dir, "algorithm_comparison.png")
            )
            if os.path.exists(alg_plot):
                st.image(alg_plot, caption=f"States Expanded by Algorithm across Scenarios ({active_theme} Theme)")

        with tab_kn:
            st.subheader("Experiment 2: Knowledge-Aware Heuristic Impact")
            st.markdown("Evaluating A* with symbolic domain rules enabled vs disabled.")
            kn_data = [r.to_dict() for r in bench_results if r.experiment_name == "knowledge_heuristic"]
            if kn_data:
                st.dataframe(pd.DataFrame(kn_data), width="stretch", hide_index=True)

        with tab_adapt:
            st.subheader("Experiment 3: Feedback-Based Adaptation")
            st.markdown("Comparing baseline A* with A* under learned user feedback adjustments.")
            adapt_data = [r.to_dict() for r in bench_results if r.experiment_name == "adaptation_experiment"]
            if adapt_data:
                st.dataframe(pd.DataFrame(adapt_data), width="stretch", hide_index=True)

        with tab_cons:
            st.subheader("Experiment 4: Hard Constraint Enforcement")
            st.markdown("Validating candidate pruning and failure reporting on infeasible vs feasible problems.")
            cons_data = [r.to_dict() for r in bench_results if r.experiment_name == "constraint_handling"]
            if cons_data:
                st.dataframe(pd.DataFrame(cons_data), width="stretch", hide_index=True)

        with tab_scale:
            st.subheader("Experiment 5: Problem Scaling (3 to 8 Tasks)")
            st.markdown("Measuring state expansions and runtime as task count increases.")
            scale_data = [r.to_dict() for r in bench_results if r.experiment_name == "scaling_experiment"]
            if scale_data:
                st.dataframe(pd.DataFrame(scale_data), width="stretch", hide_index=True)

            sc_col1, sc_col2 = st.columns(2)
            with sc_col1:
                p1_theme = os.path.join(figures_dir, f"states_expanded_vs_tasks_{active_theme.lower()}.png")
                p1 = p1_theme if os.path.exists(p1_theme) else os.path.join(figures_dir, "states_expanded_vs_tasks.png")
                if os.path.exists(p1):
                    st.image(p1, caption=f"States Expanded vs Task Count ({active_theme} Theme)")
            with sc_col2:
                p2_theme = os.path.join(figures_dir, f"runtime_vs_tasks_{active_theme.lower()}.png")
                p2 = p2_theme if os.path.exists(p2_theme) else os.path.join(figures_dir, "runtime_vs_tasks.png")
                if os.path.exists(p2):
                    st.image(p2, caption=f"Runtime (ms) vs Task Count ({active_theme} Theme)")
