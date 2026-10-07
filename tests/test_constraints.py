import unittest
from chronos.models.task import Task
from chronos.constraints.checker import (
    fits_available_time,
    meets_deadline,
    is_feasible,
)


class TestConstraints(unittest.TestCase):

    def setUp(self):
        self.dsa = Task(
            id=1,
            name="DSA",
            duration=2,
            priority="high",
            deadline=24,
            difficulty="high",
        )

    def test_valid_task(self):
        # Valid task fits in window (18 + 2 = 20 <= 23) and meets deadline (20 <= 24)
        self.assertTrue(fits_available_time(18, self.dsa.duration, 23))
        self.assertTrue(
            meets_deadline(18 + self.dsa.duration, self.dsa.deadline)
        )
        self.assertTrue(is_feasible(self.dsa, 18, 23))

    def test_task_exceeding_planning_window(self):
        # Exceeds available planning window: 23 + 2 = 25 > 24
        self.assertFalse(fits_available_time(23, self.dsa.duration, 24))
        self.assertFalse(is_feasible(self.dsa, 23, 24))

    def test_task_violating_deadline(self):
        # Fits in window (18 + 3 = 21 <= 24), but violates deadline (21 > 20)
        urgent_task = Task(
            id=2,
            name="Urgent Task",
            duration=3,
            priority="high",
            deadline=20,
            difficulty="high",
        )
        self.assertTrue(fits_available_time(18, urgent_task.duration, 24))
        self.assertFalse(
            meets_deadline(18 + urgent_task.duration, urgent_task.deadline)
        )
        self.assertFalse(is_feasible(urgent_task, 18, 24))

    def test_task_exactly_meeting_deadline(self):
        # Task ends exactly at deadline: 18 + 2 = 20 == 20
        exact_deadline_task = Task(
            id=3,
            name="Exact Deadline Task",
            duration=2,
            priority="high",
            deadline=20,
            difficulty="high",
        )
        self.assertTrue(fits_available_time(18, exact_deadline_task.duration, 24))
        self.assertTrue(
            meets_deadline(
                18 + exact_deadline_task.duration, exact_deadline_task.deadline
            )
        )
        self.assertTrue(is_feasible(exact_deadline_task, 18, 24))

    def test_task_exactly_meeting_planning_window(self):
        # Task ends exactly at available_end: 18 + 2 = 20 == 20
        exact_window_task = Task(
            id=4,
            name="Exact Window Task",
            duration=2,
            priority="high",
            deadline=24,
            difficulty="high",
        )
        self.assertTrue(fits_available_time(18, exact_window_task.duration, 20))
        self.assertTrue(
            meets_deadline(
                18 + exact_window_task.duration, exact_window_task.deadline
            )
        )
        self.assertTrue(is_feasible(exact_window_task, 18, 20))


if __name__ == "__main__":
    unittest.main()