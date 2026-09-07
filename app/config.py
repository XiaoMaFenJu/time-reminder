"""Persistent user configuration for WorkReminder."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
APP_NAME = "WorkReminder"


@dataclass(frozen=True)
class Config:
    """Settings persisted in the user-level JSON configuration file."""

    work_limit_minutes: int = 45
    break_threshold_minutes: int = 5
    launch_at_startup: bool = False
    notifications_enabled: bool = True
    poll_interval_seconds: int = 3

    def validate(self) -> None:
        """Validate settings and raise ``ValueError`` for invalid values."""

        if not isinstance(self.work_limit_minutes, int) or isinstance(
            self.work_limit_minutes, bool
        ) or not 1 <= self.work_limit_minutes <= 480:
            raise ValueError("work_limit_minutes must be an integer from 1 to 480")
        if not isinstance(self.break_threshold_minutes, int) or isinstance(
            self.break_threshold_minutes, bool
        ) or not 1 <= self.break_threshold_minutes <= 120:
            raise ValueError("break_threshold_minutes must be an integer from 1 to 120")
        if not isinstance(self.launch_at_startup, bool):
            raise ValueError("launch_at_startup must be a boolean")
        if not isinstance(self.notifications_enabled, bool):
            raise ValueError("notifications_enabled must be a boolean")
        if not isinstance(self.poll_interval_seconds, int) or isinstance(
            self.poll_interval_seconds, bool
        ) or not 1 <= self.poll_interval_seconds <= 60:
            raise ValueError("poll_interval_seconds must be an integer from 1 to 60")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Build and validate a config from JSON data."""

        config = cls(
            work_limit_minutes=data.get("work_limit_minutes", cls.work_limit_minutes),
            break_threshold_minutes=data.get(
                "break_threshold_minutes", cls.break_threshold_minutes
            ),
            launch_at_startup=data.get("launch_at_startup", cls.launch_at_startup),
            notifications_enabled=data.get(
                "notifications_enabled", cls.notifications_enabled
            ),
            poll_interval_seconds=data.get(
                "poll_interval_seconds", cls.poll_interval_seconds
            ),
        )
        config.validate()
        return config


def get_config_dir() -> Path:
    """Return the recommended per-user WorkReminder data directory."""

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    # This fallback keeps development and basic tests usable outside Windows.
    return Path.home() / ".config" / APP_NAME


def get_config_path() -> Path:
    """Return the configuration file path."""

    return get_config_dir() / "config.json"


def get_log_path() -> Path:
    """Return the application log path."""

    return get_config_dir() / "workreminder.log"


def load_config(path: Path | None = None) -> Config:
    """Load configuration, recovering safely from missing or bad JSON."""

    config_path = path or get_config_path()
    if not config_path.exists():
        config = Config()
        save_config(config, config_path)
        return config

    try:
        with config_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("configuration root must be an object")
        return Config.from_dict(data)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        LOGGER.exception("Failed to load config; using defaults")
        return Config()


def save_config(config: Config, path: Path | None = None) -> None:
    """Validate and save configuration as readable UTF-8 JSON."""

    config.validate()
    config_path = path or get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as file:
        json.dump(asdict(config), file, ensure_ascii=False, indent=2)
        file.write("\n")

