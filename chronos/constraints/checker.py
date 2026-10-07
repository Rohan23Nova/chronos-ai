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


def explain_feasibility(task, start_time, available_end):
    """
    Evaluate candidate task feasibility against hard constraints and return
    a structured diagnostic explanation based on actual task and horizon data.
    """
    end_time = start_time + task.duration
    fits_window = fits_available_time(start_time, task.duration, available_end)
    meets_dl = meets_deadline(end_time, task.deadline)
    feasible = fits_window and meets_dl

    reasons = []
    if not fits_window:
        reasons.append(
            f"scheduling {task.name} at time {start_time} would finish at {end_time}, "
            f"exceeding the planning horizon of {available_end}"
        )
    if not meets_dl:
        reasons.append(
            f"scheduling {task.name} at time {start_time} would finish at {end_time}, "
            f"violating deadline of {task.deadline}"
        )

    if feasible:
        reasons.append(
            f"fits within planning horizon of {available_end} and meets deadline of {task.deadline}"
        )

    return {
        "task_id": task.id,
        "task_name": task.name,
        "start_time": start_time,
        "end_time": end_time,
        "duration": task.duration,
        "deadline": task.deadline,
        "available_end": available_end,
        "fits_window": fits_window,
        "meets_deadline": meets_dl,
        "feasible": feasible,
        "reasons": reasons,
    }