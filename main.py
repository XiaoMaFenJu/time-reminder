"""Application entry point for WorkReminder."""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import time

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QStyle

from app.activity import get_idle_seconds
from app.config import Config, get_config_dir, get_log_path, load_config, save_config
from app.notifier import Notifier
from app.settings_window import SettingsWindow
from app.startup import disable_startup, enable_startup
from app.tracker import TrackerEvent, WorkTracker
from app.tray import TrayController


LOGGER = logging.getLogger("workreminder")


def configure_logging() -> None:
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


class WorkReminderApp:
    """Coordinate activity sampling, tracker state, notifications and tray UI."""

    def __init__(self, application: QApplication, config: Config) -> None:
        self.application = application
        self.config = config
        self.settings_window: SettingsWindow | None = None

        self.tracker = WorkTracker(
            work_limit_minutes=config.work_limit_minutes,
            break_threshold_minutes=config.break_threshold_minutes,
        )
        icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
        icon = QIcon(str(icon_path)) if icon_path.exists() else application.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )
        self.tray = TrayController(icon, config)
        self.notifier = Notifier(self.tray.icon, config.notifications_enabled)
        self.timer = QTimer(self.application)
        self.timer.timeout.connect(self._poll)

        self.tray.settings_requested.connect(self.open_settings)
        self.tray.notifications_toggled.connect(self._toggle_notifications)
        self.tray.startup_toggled.connect(self._toggle_startup)
        self.tray.quit_requested.connect(self.quit)

    def start(self) -> None:
        self.tray.show()
        self.timer.start(self.config.poll_interval_seconds * 1000)
        LOGGER.info("WorkReminder started")
        self._poll()

    def _poll(self) -> None:
        try:
            idle_seconds = get_idle_seconds()
            event = self.tracker.update(time.monotonic(), idle_seconds)
        except Exception:
            LOGGER.exception("Activity polling failed")
            return

        if event is TrackerEvent.SESSION_STARTED:
            LOGGER.info("Work session started")
        elif event is TrackerEvent.SESSION_ENDED:
            LOGGER.info("Work session ended")
        elif event is TrackerEvent.REMINDER_DUE:
            LOGGER.info("Work reminder triggered")
            self.notifier.show_reminder(self.tracker.get_work_duration_seconds())

        self.tray.update_status(
            self.tracker.is_working(), self.tracker.get_work_duration_seconds()
        )

    def open_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.config_saved.connect(self._apply_config)
            self.settings_window.finished.connect(self._settings_closed)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _settings_closed(self) -> None:
        self.settings_window = None

    def _apply_config(self, config: Config) -> None:
        self.config = config
        self.tracker.set_limits(
            work_limit_minutes=config.work_limit_minutes,
            break_threshold_minutes=config.break_threshold_minutes,
        )
        self.notifier.set_enabled(config.notifications_enabled)
        self.tray.set_config(config)
        self.timer.setInterval(config.poll_interval_seconds * 1000)
        LOGGER.info("Configuration modified")

    def _toggle_notifications(self, enabled: bool) -> None:
        config = Config(
            work_limit_minutes=self.config.work_limit_minutes,
            break_threshold_minutes=self.config.break_threshold_minutes,
            launch_at_startup=self.config.launch_at_startup,
            notifications_enabled=enabled,
            poll_interval_seconds=self.config.poll_interval_seconds,
        )
        try:
            save_config(config)
        except Exception as exc:
            self.tray.set_config(self.config)
            self.tray.show_message("保存失败", str(exc))
            return
        self._apply_config(config)

    def _toggle_startup(self, enabled: bool) -> None:
        try:
            if enabled:
                enable_startup()
            else:
                disable_startup()
            config = Config(
                work_limit_minutes=self.config.work_limit_minutes,
                break_threshold_minutes=self.config.break_threshold_minutes,
                launch_at_startup=enabled,
                notifications_enabled=self.config.notifications_enabled,
                poll_interval_seconds=self.config.poll_interval_seconds,
            )
            save_config(config)
        except Exception as exc:
            self.tray.set_config(self.config)
            self.tray.show_message("开机启动设置失败", str(exc))
            return
        self._apply_config(config)
        LOGGER.info("Startup setting modified")

    def quit(self) -> None:
        LOGGER.info("WorkReminder exiting")
        self.timer.stop()
        self.tray.hide()
        self.application.quit()


def main() -> int:
    configure_logging()
    config = load_config()
    application = QApplication(sys.argv)
    application.setApplicationName("WorkReminder")
    application.setQuitOnLastWindowClosed(False)

    lock_path = get_config_dir() / "WorkReminder.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(lock_path))
    if not lock.tryLock(100):
        QMessageBox.warning(None, "WorkReminder", "WorkReminder 已经在运行。")
        return 0

    controller = WorkReminderApp(application, config)
    controller.start()
    result = application.exec()
    lock.unlock()
    return result


if __name__ == "__main__":
    sys.exit(main())

