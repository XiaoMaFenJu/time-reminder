"""Continuous-work session state machine.

This module deliberately has no GUI or Windows API dependency.  The caller
supplies the current monotonic timestamp and the idle duration reported by
the activity detector, which keeps the state machine straightforward to test.
"""

from __future__ import annotations

from enum import Enum, auto
import math


class TrackerEvent(Enum):
    """State changes that the application may need to handle."""

    NONE = auto()
    SESSION_STARTED = auto()
    REMINDER_DUE = auto()
    SESSION_ENDED = auto()


class WorkTracker:
    """Track one continuous-work session.

    A session starts only after an active sample (``idle_seconds`` below the
    active threshold).  During a session, inactive samples shorter than the
    break threshold pause effective work duration; they do not advance
    ``last_active_time``.  A session ends at the break-threshold boundary.
    """

    def __init__(
        self,
        work_limit_minutes: float = 45,
        break_threshold_minutes: float = 5,
        active_threshold_seconds: float = 10,
    ) -> None:
        work_limit = self._finite_number(work_limit_minutes, "work_limit_minutes")
        break_threshold = self._finite_number(
            break_threshold_minutes, "break_threshold_minutes"
        )
        active_threshold = self._finite_number(
            active_threshold_seconds, "active_threshold_seconds"
        )

        if work_limit <= 0:
            raise ValueError("work_limit_minutes must be greater than zero")
        if break_threshold <= 0:
            raise ValueError("break_threshold_minutes must be greater than zero")
        if active_threshold < 0:
            raise ValueError("active_threshold_seconds must not be negative")

        self.work_limit_seconds = work_limit * 60
        self.break_threshold_seconds = break_threshold * 60
        self.active_threshold_seconds = active_threshold

        self._session_start: float | None = None
        self._last_active_time: float | None = None
        self._reminded = False

    def update(self, now: float, idle_seconds: float) -> TrackerEvent:
        """Apply one activity sample and return the resulting event.

        ``now`` must be a monotonic timestamp supplied by the caller.  The
        method does not call a clock itself, so deterministic tests can use
        ordinary numeric timestamps.
        """

        now_value = self._finite_number(now, "now")
        idle_value = self._finite_number(idle_seconds, "idle_seconds")
        if idle_value < 0:
            raise ValueError("idle_seconds must not be negative")

        if self._session_start is None:
            if idle_value < self.active_threshold_seconds:
                self._session_start = now_value
                self._last_active_time = now_value
                self._reminded = False
                return TrackerEvent.SESSION_STARTED
            return TrackerEvent.NONE

        if idle_value < self.active_threshold_seconds:
            self._last_active_time = now_value

        # Check session termination before reminder eligibility.  At the
        # exact break boundary the old session is over and cannot emit a
        # reminder from that sample.
        if idle_value >= self.break_threshold_seconds:
            self._session_start = None
            self._last_active_time = None
            self._reminded = False
            return TrackerEvent.SESSION_ENDED

        if (
            self.get_work_duration_seconds() >= self.work_limit_seconds
            and not self._reminded
        ):
            self._reminded = True
            return TrackerEvent.REMINDER_DUE

        return TrackerEvent.NONE

    def get_work_duration_seconds(self) -> float:
        """Return effective work duration for the current session."""

        if self._session_start is None or self._last_active_time is None:
            return 0.0
        return max(0.0, self._last_active_time - self._session_start)

    def set_limits(
        self, work_limit_minutes: float, break_threshold_minutes: float
    ) -> None:
        """Update limits without discarding the current session."""

        work_limit = self._finite_number(work_limit_minutes, "work_limit_minutes")
        break_threshold = self._finite_number(
            break_threshold_minutes, "break_threshold_minutes"
        )
        if work_limit <= 0:
            raise ValueError("work_limit_minutes must be greater than zero")
        if break_threshold <= 0:
            raise ValueError("break_threshold_minutes must be greater than zero")
        self.work_limit_seconds = work_limit * 60
        self.break_threshold_seconds = break_threshold * 60

    def is_working(self) -> bool:
        """Return whether a work session is currently active."""

        return self._session_start is not None

    @staticmethod
    def _finite_number(value: float, name: str) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a number") from exc
        if not math.isfinite(numeric_value):
            raise ValueError(f"{name} must be finite")
        return numeric_value
