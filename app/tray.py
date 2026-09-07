"""System-tray UI for WorkReminder."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .config import Config


class TrayController(QObject):
    """Own the tray icon and expose user actions to the application layer."""

    settings_requested = Signal()
    quit_requested = Signal()
    notifications_toggled = Signal(bool)
    startup_toggled = Signal(bool)

    def __init__(self, icon: QIcon, config: Config, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.icon = QSystemTrayIcon(icon, self)
        self.icon.setToolTip("WorkReminder")

        self.menu = QMenu()
        title_action = self.menu.addAction("WorkReminder")
        title_action.setEnabled(False)
        self.status_action = self.menu.addAction("状态：空闲")
        self.status_action.setEnabled(False)
        self.menu.addSeparator()

        self.settings_action = self.menu.addAction("打开设置")
        self.settings_action.triggered.connect(self.settings_requested)
        self.notifications_action = self.menu.addAction("启用提醒")
        self.notifications_action.setCheckable(True)
        self.notifications_action.triggered.connect(self.notifications_toggled)
        self.startup_action = self.menu.addAction("开机启动")
        self.startup_action.setCheckable(True)
        self.startup_action.triggered.connect(self.startup_toggled)
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("退出")
        self.quit_action.triggered.connect(self.quit_requested)

        self.icon.setContextMenu(self.menu)
        self.set_config(config)

    def show(self) -> None:
        self.icon.show()

    def set_config(self, config: Config) -> None:
        self.config = config
        self.notifications_action.setChecked(config.notifications_enabled)
        self.startup_action.setChecked(config.launch_at_startup)

    def update_status(self, working: bool, work_duration_seconds: float) -> None:
        if not working:
            self.status_action.setText("状态：空闲")
            return
        minutes = max(0, int(work_duration_seconds // 60))
        self.status_action.setText(f"状态：正在工作 {minutes} 分钟")

    def show_message(self, title: str, message: str) -> None:
        self.icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 8_000)

    def hide(self) -> None:
        self.icon.hide()
