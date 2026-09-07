"""Current-user Windows startup registration."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys


LOGGER = logging.getLogger(__name__)
STARTUP_VALUE_NAME = "WorkReminder"
STARTUP_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_winreg():
    if os.name != "nt":
        raise OSError("Windows registry is only available on Windows")
    import winreg

    return winreg


def _startup_command() -> str:
    """Return a quoted command suitable for the current-user Run key."""

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        return f'"{executable}"'

    interpreter = Path(sys.executable).resolve()
    script = Path(sys.argv[0]).resolve()
    return f'"{interpreter}" "{script}"'


def is_startup_enabled() -> bool:
    """Return whether the WorkReminder Run value is present."""

    winreg = _get_winreg()
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_KEY_PATH, 0, winreg.KEY_READ
        ) as key:
            winreg.QueryValueEx(key, STARTUP_VALUE_NAME)
            return True
    except FileNotFoundError:
        return False


def enable_startup() -> None:
    """Register WorkReminder for the current Windows user."""

    winreg = _get_winreg()
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        STARTUP_KEY_PATH,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, STARTUP_VALUE_NAME, 0, winreg.REG_SZ, _startup_command())
    LOGGER.info("Startup enabled")


def disable_startup() -> None:
    """Remove WorkReminder from the current user's startup entries."""

    winreg = _get_winreg()
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, STARTUP_VALUE_NAME)
    except FileNotFoundError:
        pass
    LOGGER.info("Startup disabled")

