"""Click-through animated desktop reminder."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QApplication, QWidget

GROWTH_SECONDS = 900


def growth_progress(enabled: bool, working: bool, duration: float, limit: float) -> float | None:
    if not enabled or not working or duration <= limit:
        return None
    return min(1.0, (duration - limit) / GROWTH_SECONDS)


class BlackHoleOverlay(QWidget):
    """Transparent desktop overlay that does not intercept input."""

    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._progress = 0.0
        self._animation = QTimer(self)
        self._animation.setInterval(50)
        self._animation.timeout.connect(self.update)

    def set_work_state(self, enabled: bool, working: bool, duration: float, limit: float) -> None:
        progress = growth_progress(enabled, working, duration, limit)
        if progress is None:
            self._animation.stop()
            self.hide()
            return
        self._progress = progress
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.geometry()
        size = max(1, min(700, int(min(area.width(), area.height()) * 0.7)))
        self.setGeometry(area.center().x() - size // 2, area.center().y() - size // 2, size, size)
        if not self.isVisible():
            self.show()
            self._animation.start()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) * (0.07 + 0.25 * self._progress)
        phase = time.monotonic() * 0.7
        halo = QRadialGradient(center, radius * 1.8)
        halo.setColorAt(0.0, QColor(255, 176, 83, 90))
        halo.setColorAt(0.48, QColor(243, 112, 38, 70))
        halo.setColorAt(1.0, QColor(170, 55, 20, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(center, radius * 1.8, radius * 1.8)
        for i in range(10):
            painter.save()
            painter.translate(center)
            painter.rotate(-13 + math.sin(phase + i * 0.6) * 3)
            scale = 1.1 + i * 0.055
            rect = QRectF(-radius * scale * 1.55, -radius * scale * 0.38,
                          radius * scale * 3.1, radius * scale * 0.76)
            painter.setPen(QPen(QColor(255, 190 - i * 8, 105 - i * 5, 170 - i * 10),
                                max(1.0, radius * (0.045 - i * 0.003))))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(rect, int((phase * 25 + i * 29) * 16), 245 * 16)
            painter.restore()
        painter.setBrush(QColor(3, 3, 8, 255))
        painter.setPen(QPen(QColor(255, 215, 153, 235), max(1.5, radius * 0.035)))
        painter.drawEllipse(center, radius * 0.67, radius * 0.67)
