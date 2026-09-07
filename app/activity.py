"""Windows last-input-time detection."""

from __future__ import annotations

import ctypes
import os


class ActivityError(RuntimeError):
    """Raised when Windows cannot provide the last input timestamp."""


class _LastInputInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_idle_seconds() -> float:
    """Return seconds since the last keyboard or mouse input.

    The Windows API exposes a system tick count, not input contents.  Both
    values are treated as unsigned 32-bit counters so subtraction remains
    correct across the tick counter wraparound.
    """

    if os.name != "nt":
        raise ActivityError("WorkReminder requires Windows")

    info = _LastInputInfo()
    info.cbSize = ctypes.sizeof(_LastInputInfo)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        error_code = ctypes.get_last_error()
        raise ActivityError(f"GetLastInputInfo failed with error {error_code}")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetTickCount.restype = ctypes.c_uint
    current_ticks = int(kernel32.GetTickCount())
    elapsed_ticks = (current_ticks - int(info.dwTime)) & 0xFFFFFFFF
    return elapsed_ticks / 1000.0

