import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from chronos.models.task import Task
from chronos.models.schedule import ScheduleEntry
from chronos.adaptation.feedback import FeedbackRecord, AdaptationModel


DEFAULT_DB_PATH = os.path.join("data", "chronos.db")


class DatabaseManager:
    """
    SQLite persistence manager for tasks, feedback, schedules, and planning runs.
    Maintains clean separation between storage and core search/planning algorithms.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        if self.db_path != ":memory:":
            dirname = os.path.dirname(self.db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """
        Yield a managed SQLite connection with foreign keys enabled and row_factory set.
        Automatically commits on successful exit, rolls back on error, and closes.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_database(self) -> None:
        """
        Create schema tables if they do not exist. Safe for repeated invocation.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Tasks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    priority TEXT NOT NULL,
                    deadline INTEGER NOT NULL,
                    difficulty TEXT NOT NULL
                );
                """
            )

            # 2. Schedules table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    planning_start INTEGER NOT NULL,
                    available_end INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    states_expanded INTEGER
                );
                """
            )

            # 3. Schedule entries table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
                );
                """
            )

            # 4. Planning runs history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS planning_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    algorithm TEXT NOT NULL,
                    total_cost REAL,
                    states_expanded INTEGER,
                    created_at TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    schedule_id INTEGER,
                    FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE SET NULL
                );
                """
            )

            # 5. Feedback table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    feedback_type TEXT NOT NULL,
                    rating REAL,
                    scheduled_duration INTEGER,
                    actual_duration INTEGER,
                    comment TEXT,
                    step INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
                );
                """
            )

    # --------------------------------------------------
    # Task CRUD
    # --------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Persist a new Task using parameterized SQL."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, name, duration, priority, deadline, difficulty)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (task.id, task.name, task.duration, task.priority, task.deadline, task.difficulty),
            )

    def get_task(self, task_id: int) -> Optional[Task]:
        """Retrieve a task by ID, converting database row back to Task dataclass."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, duration, priority, deadline, difficulty
                FROM tasks
                WHERE id = ?;
                """,
                (task_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return Task(
                id=row["id"],
                name=row["name"],
                duration=row["duration"],
                priority=row["priority"],
                deadline=row["deadline"],
                difficulty=row["difficulty"],
            )

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all persisted tasks."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, duration, priority, deadline, difficulty
                FROM tasks
                ORDER BY id ASC;
                """
            )
            rows = cursor.fetchall()
            return [
                Task(
                    id=row["id"],
                    name=row["name"],
                    duration=row["duration"],
                    priority=row["priority"],
                    deadline=row["deadline"],
                    difficulty=row["difficulty"],
                )
                for row in rows
            ]

    def update_task(self, task: Task) -> bool:
        """Update an existing task's attributes. Returns True if updated."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE tasks
                SET name = ?, duration = ?, priority = ?, deadline = ?, difficulty = ?
                WHERE id = ?;
                """,
                (task.name, task.duration, task.priority, task.deadline, task.difficulty, task.id),
            )
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID. Returns True if deleted."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM tasks
                WHERE id = ?;
                """,
                (task_id,),
            )
            return cursor.rowcount > 0

    # --------------------------------------------------
    # Feedback Persistence
    # --------------------------------------------------

    def save_feedback(self, record: FeedbackRecord) -> int:
        """Persist a FeedbackRecord. Returns inserted row ID."""
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO feedback (
                    task_id, feedback_type, rating, scheduled_duration,
                    actual_duration, comment, step, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.task_id,
                    record.feedback_type,
                    record.rating,
                    record.scheduled_duration,
                    record.actual_duration,
                    record.comment,
                    record.step,
                    now,
                ),
            )
            return cursor.lastrowid

    def get_feedback(self, task_id: int) -> List[FeedbackRecord]:
        """Retrieve all feedback records for a specific task."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT task_id, feedback_type, rating, scheduled_duration,
                       actual_duration, comment, step
                FROM feedback
                WHERE task_id = ?
                ORDER BY id ASC;
                """,
                (task_id,),
            )
            rows = cursor.fetchall()
            return [
                FeedbackRecord(
                    task_id=row["task_id"],
                    feedback_type=row["feedback_type"],
                    rating=row["rating"],
                    scheduled_duration=row["scheduled_duration"],
                    actual_duration=row["actual_duration"],
                    comment=row["comment"],
                    step=row["step"],
                )
                for row in rows
            ]

    def get_all_feedback(self) -> List[FeedbackRecord]:
        """Retrieve all feedback records across all tasks."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT task_id, feedback_type, rating, scheduled_duration,
                       actual_duration, comment, step
                FROM feedback
                ORDER BY id ASC;
                """
            )
            rows = cursor.fetchall()
            return [
                FeedbackRecord(
                    task_id=row["task_id"],
                    feedback_type=row["feedback_type"],
                    rating=row["rating"],
                    scheduled_duration=row["scheduled_duration"],
                    actual_duration=row["actual_duration"],
                    comment=row["comment"],
                    step=row["step"],
                )
                for row in rows
            ]

    # --------------------------------------------------
    # Schedule & Planning Run Persistence
    # --------------------------------------------------

    def save_schedule(
        self,
        problem: Any,
        result_state: Any,
        algorithm: str = "A*",
        states_expanded: Optional[int] = None,
    ) -> int:
        """
        Persist a generated schedule, its entries, and a planning run record.
        Returns the created schedule ID.
        """
        now = datetime.now(timezone.utc).isoformat()
        planning_start = getattr(problem, "planning_start", 18)
        available_end = getattr(problem, "available_end", 24)
        total_cost = result_state.cost if result_state is not None else 0.0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert schedule header
            cursor.execute(
                """
                INSERT INTO schedules (
                    created_at, planning_start, available_end, total_cost, states_expanded
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (now, planning_start, available_end, total_cost, states_expanded),
            )
            schedule_id = cursor.lastrowid

            # Insert individual schedule entries
            if result_state is not None and getattr(result_state, "schedule", None):
                for entry in result_state.schedule:
                    cursor.execute(
                        """
                        INSERT INTO schedule_entries (
                            schedule_id, task_id, start_time, end_time
                        )
                        VALUES (?, ?, ?, ?);
                        """,
                        (schedule_id, entry.task_id, entry.start_time, entry.end_time),
                    )

            # Insert planning run log
            success = 1 if result_state is not None else 0
            cursor.execute(
                """
                INSERT INTO planning_runs (
                    algorithm, total_cost, states_expanded, created_at, success, schedule_id
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (algorithm, total_cost, states_expanded, now, success, schedule_id),
            )

            return schedule_id

    def get_schedule(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve schedule metadata along with its ScheduleEntry objects."""
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, created_at, planning_start, available_end, total_cost, states_expanded
                FROM schedules
                WHERE id = ?;
                """,
                (schedule_id,),
            )
            sched_row = cur.fetchone()
            if sched_row is None:
                return None

            entry_cur = conn.execute(
                """
                SELECT task_id, start_time, end_time
                FROM schedule_entries
                WHERE schedule_id = ?
                ORDER BY start_time ASC;
                """,
                (schedule_id,),
            )
            entries = [
                ScheduleEntry(
                    task_id=erow["task_id"],
                    start_time=erow["start_time"],
                    end_time=erow["end_time"],
                )
                for erow in entry_cur.fetchall()
            ]

            return {
                "id": sched_row["id"],
                "created_at": sched_row["created_at"],
                "planning_start": sched_row["planning_start"],
                "available_end": sched_row["available_end"],
                "total_cost": sched_row["total_cost"],
                "states_expanded": sched_row["states_expanded"],
                "entries": entries,
            }

    def get_planning_history(self) -> List[Dict[str, Any]]:
        """Retrieve historical planning runs metadata."""
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, algorithm, total_cost, states_expanded, created_at, success, schedule_id
                FROM planning_runs
                ORDER BY id DESC;
                """
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "algorithm": row["algorithm"],
                    "total_cost": row["total_cost"],
                    "states_expanded": row["states_expanded"],
                    "created_at": row["created_at"],
                    "success": bool(row["success"]),
                    "schedule_id": row["schedule_id"],
                }
                for row in rows
            ]


def build_adaptation_model(records: Iterable[FeedbackRecord]) -> AdaptationModel:
    """
    Reconstruct an AdaptationModel from persisted FeedbackRecord objects.
    Maintains AdaptationModel as the single source of truth for scoring logic.
    """
    model = AdaptationModel()
    for r in records:
        model.record_feedback(
            task_id=r.task_id,
            feedback_type=r.feedback_type,
            rating=r.rating,
            scheduled_duration=r.scheduled_duration,
            actual_duration=r.actual_duration,
            comment=r.comment,
            step=r.step,
        )
    return model
