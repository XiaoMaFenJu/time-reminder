"""Simple settings dialog."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from .config import Config, save_config
from .startup import disable_startup, enable_startup


class SettingsWindow(QDialog):
    """Edit and persist the user-facing WorkReminder settings."""

    config_saved = Signal(object)

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("WorkReminder 设置")
        self.setModal(False)
        self.resize(360, 180)
        self._config = config

        self.work_limit = QSpinBox()
        self.work_limit.setRange(1, 480)
        self.work_limit.setSuffix(" 分钟")
        self.work_limit.setValue(config.work_limit_minutes)

        self.break_threshold = QSpinBox()
        self.break_threshold.setRange(1, 120)
        self.break_threshold.setSuffix(" 分钟")
        self.break_threshold.setValue(config.break_threshold_minutes)

        self.notifications = QCheckBox("启用提醒")
        self.notifications.setChecked(config.notifications_enabled)
        self.startup = QCheckBox("开机启动")
        self.startup.setChecked(config.launch_at_startup)

        form = QFormLayout()
        form.addRow("连续工作提醒时间：", self.work_limit)
        form.addRow("休息判定时间：", self.break_threshold)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.notifications)
        layout.addWidget(self.startup)
        layout.addWidget(buttons)

    def _save(self) -> None:
        new_config = replace(
            self._config,
            work_limit_minutes=self.work_limit.value(),
            break_threshold_minutes=self.break_threshold.value(),
            notifications_enabled=self.notifications.isChecked(),
            launch_at_startup=self.startup.isChecked(),
        )
        try:
            if new_config.launch_at_startup != self._config.launch_at_startup:
                if new_config.launch_at_startup:
                    enable_startup()
                else:
                    disable_startup()
            save_config(new_config)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"设置未能保存：{exc}")
            return

        self._config = new_config
        self.config_saved.emit(new_config)
        self.accept()
