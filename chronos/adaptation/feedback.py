from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FeedbackType(str, Enum):
    """Supported feedback events for adaptive preference learning."""
    COMPLETED_ON_TIME = "completed_on_time"
    COMPLETED_EARLY = "completed_early"
    POSTPONED = "postponed"
    NOT_COMPLETED = "not_completed"
    TOO_DIFFICULT = "too_difficult"
    TOO_EASY = "too_easy"
    SCHEDULE_ACCEPTABLE = "schedule_acceptable"
    SCHEDULE_UNACCEPTABLE = "schedule_unacceptable"


# Explicit string constants for direct access
COMPLETED_ON_TIME = FeedbackType.COMPLETED_ON_TIME.value
COMPLETED_EARLY = FeedbackType.COMPLETED_EARLY.value
POSTPONED = FeedbackType.POSTPONED.value
NOT_COMPLETED = FeedbackType.NOT_COMPLETED.value
TOO_DIFFICULT = FeedbackType.TOO_DIFFICULT.value
TOO_EASY = FeedbackType.TOO_EASY.value
SCHEDULE_ACCEPTABLE = FeedbackType.SCHEDULE_ACCEPTABLE.value
SCHEDULE_UNACCEPTABLE = FeedbackType.SCHEDULE_UNACCEPTABLE.value


@dataclass(frozen=True)
class FeedbackRecord:
    """
    Structured feedback record capturing user evaluation of a task or schedule.
    """
    task_id: int
    feedback_type: str
    rating: Optional[float] = None
    scheduled_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    comment: Optional[str] = None
    step: Optional[int] = None


@dataclass
class TaskProfile:
    """
    Interpretable statistical profile and derived adaptive signals for a task.
    """
    task_id: int
    postponement_count: int = 0
    too_difficult_count: int = 0
    too_easy_count: int = 0
    completed_early_count: int = 0
    completed_on_time_count: int = 0
    not_completed_count: int = 0
    schedule_acceptable_count: int = 0
    schedule_unacceptable_count: int = 0

    postponement_pressure: float = 0.0
    difficulty_pressure: float = 0.0
    reliability_score: float = 0.0
    net_adjustment: float = 0.0


class AdaptationModel:
    """
    Deterministic feedback-based adaptive preference model.
    Maintains interpretable statistics from user feedback and derives bounded
    scheduling adjustments [-2.0, +2.0] without deep learning or external frameworks.
    """

    def __init__(self):
        self._history: List[FeedbackRecord] = []
        self._profiles: Dict[int, TaskProfile] = {}

    def record_feedback(
        self,
        task_id: int,
        feedback_type: str,
        rating: Optional[float] = None,
        scheduled_duration: Optional[int] = None,
        actual_duration: Optional[int] = None,
        comment: Optional[str] = None,
        step: Optional[int] = None,
    ) -> FeedbackRecord:
        """
        Record a user feedback event and update the corresponding task profile.
        """
        # Normalize feedback_type string if passed as Enum
        if isinstance(feedback_type, FeedbackType):
            feedback_type = feedback_type.value

        record = FeedbackRecord(
            task_id=task_id,
            feedback_type=feedback_type,
            rating=rating,
            scheduled_duration=scheduled_duration,
            actual_duration=actual_duration,
            comment=comment,
            step=step,
        )
        self._history.append(record)
        self._update_profile(task_id, feedback_type)
        return record

    def _update_profile(self, task_id: int, feedback_type: str) -> None:
        """Increment count and recalculate deterministic adaptive scores."""
        profile = self._profiles.setdefault(task_id, TaskProfile(task_id=task_id))

        if feedback_type == POSTPONED:
            profile.postponement_count += 1
        elif feedback_type == TOO_DIFFICULT:
            profile.too_difficult_count += 1
        elif feedback_type == TOO_EASY:
            profile.too_easy_count += 1
        elif feedback_type == COMPLETED_EARLY:
            profile.completed_early_count += 1
        elif feedback_type == COMPLETED_ON_TIME:
            profile.completed_on_time_count += 1
        elif feedback_type == NOT_COMPLETED:
            profile.not_completed_count += 1
        elif feedback_type == SCHEDULE_ACCEPTABLE:
            profile.schedule_acceptable_count += 1
        elif feedback_type == SCHEDULE_UNACCEPTABLE:
            profile.schedule_unacceptable_count += 1

        self._recalculate_scores(profile)

    def _recalculate_scores(self, profile: TaskProfile) -> None:
        """
        Transparent scoring calculation with explicit bounds:
        - Postponement pressure: +0.5 per postponement, capped at +1.5
        - Difficulty pressure: +0.4 per too_difficult, -0.2 per too_easy, bounded [-0.5, +1.0]
        - Non-completion penalty: +0.4 per not_completed, capped at +1.0
        - Completion relief: -0.3 per completed_early, -0.1 per completed_on_time, capped at -0.8
        - Schedule penalty: +0.2 per unacceptable, -0.1 per acceptable
        Total adjustment bounded in [-2.0, +2.0].
        """
        postponement_p = min(1.5, profile.postponement_count * 0.5)

        difficulty_p = min(1.0, profile.too_difficult_count * 0.4) - min(0.5, profile.too_easy_count * 0.2)

        not_completed_p = min(1.0, profile.not_completed_count * 0.4)

        completion_relief = min(0.8, profile.completed_early_count * 0.3 + profile.completed_on_time_count * 0.1)

        schedule_p = min(0.5, profile.schedule_unacceptable_count * 0.2) - min(0.3, profile.schedule_acceptable_count * 0.1)

        # Reliability score: higher when on-time / early, lower when postponed / not completed
        pos_signals = profile.completed_on_time_count + (profile.completed_early_count * 1.5)
        neg_signals = (profile.postponement_count * 1.0) + (profile.not_completed_count * 1.5)
        total_signals = pos_signals + neg_signals
        if total_signals > 0:
            profile.reliability_score = round((pos_signals - neg_signals) / total_signals, 2)
        else:
            profile.reliability_score = 0.0

        raw_adj = postponement_p + difficulty_p + not_completed_p + schedule_p - completion_relief

        # Clamp net adjustment to [-2.0, +2.0]
        clamped_adj = max(-2.0, min(2.0, round(raw_adj, 2)))

        profile.postponement_pressure = round(postponement_p, 2)
        profile.difficulty_pressure = round(difficulty_p, 2)
        profile.net_adjustment = clamped_adj

    def get_task_profile(self, task_id: int) -> TaskProfile:
        """Retrieve task profile or return an empty neutral profile if none exists."""
        if task_id in self._profiles:
            return self._profiles[task_id]
        return TaskProfile(task_id=task_id)

    def get_adjustment(self, task_id: int) -> float:
        """Get net adaptive score adjustment for a task."""
        if task_id in self._profiles:
            return self._profiles[task_id].net_adjustment
        return 0.0

    def get_feedback_history(self, task_id: Optional[int] = None) -> List[FeedbackRecord]:
        """Return full feedback history or filtered by task_id."""
        if task_id is None:
            return list(self._history)
        return [r for r in self._history if r.task_id == task_id]

    def reset(self) -> None:
        """Reset all feedback history and learned profiles."""
        self._history.clear()
        self._profiles.clear()
