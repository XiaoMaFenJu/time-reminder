from app.tracker import TrackerEvent, WorkTracker


def test_first_active_sample_starts_a_session() -> None:
    tracker = WorkTracker()

    event = tracker.update(now=100.0, idle_seconds=0.0)

    assert event is TrackerEvent.SESSION_STARTED
    assert tracker.is_working()
    assert tracker.get_work_duration_seconds() == 0.0


def test_short_idle_does_not_reset_and_active_sample_advances_duration() -> None:
    tracker = WorkTracker(work_limit_minutes=45, break_threshold_minutes=5)
    tracker.update(now=0.0, idle_seconds=0.0)

    assert tracker.update(now=30.0, idle_seconds=9.0) is TrackerEvent.NONE
    assert tracker.get_work_duration_seconds() == 30.0

    # Idle longer than the active threshold but shorter than the break
    # threshold pauses effective work time without ending the session.
    assert tracker.update(now=120.0, idle_seconds=30.0) is TrackerEvent.NONE
    assert tracker.is_working()
    assert tracker.get_work_duration_seconds() == 30.0


def test_idle_at_break_threshold_ends_the_session() -> None:
    tracker = WorkTracker(break_threshold_minutes=5)
    tracker.update(now=0.0, idle_seconds=0.0)

    assert tracker.update(now=300.0, idle_seconds=300.0) is TrackerEvent.SESSION_ENDED
    assert not tracker.is_working()
    assert tracker.get_work_duration_seconds() == 0.0


def test_reaching_work_limit_emits_one_reminder() -> None:
    tracker = WorkTracker(work_limit_minutes=1)
    tracker.update(now=0.0, idle_seconds=0.0)

    assert tracker.update(now=60.0, idle_seconds=0.0) is TrackerEvent.REMINDER_DUE
    assert tracker.update(now=61.0, idle_seconds=0.0) is TrackerEvent.NONE


def test_a_session_does_not_remind_twice() -> None:
    tracker = WorkTracker(work_limit_minutes=1)
    tracker.update(now=0.0, idle_seconds=0.0)
    tracker.update(now=60.0, idle_seconds=0.0)

    for now in (120.0, 180.0, 240.0):
        assert tracker.update(now=now, idle_seconds=0.0) is TrackerEvent.NONE


def test_a_new_session_can_remind_again() -> None:
    tracker = WorkTracker(work_limit_minutes=1, break_threshold_minutes=5)
    tracker.update(now=0.0, idle_seconds=0.0)
    assert tracker.update(now=60.0, idle_seconds=0.0) is TrackerEvent.REMINDER_DUE

    assert tracker.update(now=360.0, idle_seconds=300.0) is TrackerEvent.SESSION_ENDED
    assert tracker.update(now=400.0, idle_seconds=0.0) is TrackerEvent.SESSION_STARTED
    assert tracker.update(now=460.0, idle_seconds=0.0) is TrackerEvent.REMINDER_DUE


def test_leaving_before_work_limit_does_not_accumulate_wall_clock_time() -> None:
    tracker = WorkTracker(work_limit_minutes=45, break_threshold_minutes=5)
    tracker.update(now=0.0, idle_seconds=0.0)
    tracker.update(now=43 * 60, idle_seconds=0.0)

    # The user has been away for two minutes, so last_active_time remains at
    # 43 minutes even though the session itself has not ended.
    assert tracker.update(now=45 * 60, idle_seconds=120.0) is TrackerEvent.NONE
    assert tracker.get_work_duration_seconds() == 43 * 60
    assert tracker.update(now=47 * 60, idle_seconds=240.0) is TrackerEvent.NONE
    assert tracker.update(now=48 * 60, idle_seconds=300.0) is TrackerEvent.SESSION_ENDED


def test_break_threshold_is_strictly_below_until_the_boundary() -> None:
    tracker = WorkTracker(break_threshold_minutes=5)
    tracker.update(now=0.0, idle_seconds=0.0)

    assert tracker.update(now=299.0, idle_seconds=299.0) is TrackerEvent.NONE
    assert tracker.is_working()
    assert tracker.update(now=300.0, idle_seconds=300.0) is TrackerEvent.SESSION_ENDED


def test_invalid_parameters_and_samples_are_rejected() -> None:
    for kwargs in (
        {"work_limit_minutes": 0},
        {"break_threshold_minutes": 0},
        {"active_threshold_seconds": -1},
    ):
        try:
            WorkTracker(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid tracker parameters should fail")

    tracker = WorkTracker()
    for now, idle in ((0.0, -1.0), (float("nan"), 0.0), (0.0, float("inf"))):
        try:
            tracker.update(now=now, idle_seconds=idle)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid tracker samples should fail")

