"""System-tray notification wrapper."""

from __future__ import annotations

from PySide6.QtWidgets import QSystemTrayIcon


class Notifier:
    """Show the one supported WorkReminder reminder."""

    def __init__(self, tray_icon: QSystemTrayIcon, enabled: bool = True) -> None:
        self._tray_icon = tray_icon
        self.enabled = enabled

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def show_reminder(self, work_duration_seconds: float) -> None:
        """Display a reminder unless notifications are disabled."""

        if not self.enabled:
            return
        minutes = max(1, round(work_duration_seconds / 60))
        self._tray_icon.showMessage(
            "该休息一下了",
            f"你已经连续工作 {minutes} 分钟，建议起身活动一下。",
            QSystemTrayIcon.MessageIcon.Information,
            10_000,
        )
