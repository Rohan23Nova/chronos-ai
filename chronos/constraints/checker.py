def fits_available_time(start_time, duration, available_end):
    return start_time + duration <= available_end


def meets_deadline(end_time, deadline):
    return end_time <= deadline


def is_feasible(task, start_time, available_end):
    end_time = start_time + task.duration

    return (
        fits_available_time(
            start_time,
            task.duration,
            available_end
        )
        and
        meets_deadline(
            end_time,
            task.deadline
        )
    )