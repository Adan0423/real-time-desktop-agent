from __future__ import annotations

from collections.abc import Callable


class RTDAFloatingControl:
    """Always-on-top control for the RTDA extension runtime.

    The floating control intentionally stays separate from the main dashboard:
    it is a compact background indicator that lets the user see whether the
    RTDA extension/complement is alive and perform the core runtime actions.
    """

    def __init__(
        self,
        *,
        on_open: Callable[[], None],
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

        self._running = False
        self._paused = False
        self._positioned = False
        self.widget = _create_floating_widget()
        self.widget.setWindowTitle("RTDA")
        self.widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.widget.resize(344, 118)

        self.orb = _create_pulse_orb()
        self.title = QLabel("RTDA Extension")
        self.title.setObjectName("floatingTitle")
        self.status = QLabel("Idle - ready")
        self.status.setObjectName("floatingStatus")
        self.metrics = QLabel("0.0 FPS - -")
        self.metrics.setObjectName("floatingMetrics")

        self.open_button = QPushButton("Open")
        self.run_button = QPushButton("Run")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.quit_button = QPushButton("Quit")
        for button in (self.open_button, self.run_button, self.pause_button, self.stop_button, self.quit_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setObjectName("floatingButton")

        self.open_button.clicked.connect(on_open)
        self.run_button.clicked.connect(on_start)
        self.pause_button.clicked.connect(on_pause)
        self.stop_button.clicked.connect(on_stop)
        self.quit_button.clicked.connect(on_quit)

        copy = QVBoxLayout()
        copy.setContentsMargins(0, 0, 0, 0)
        copy.setSpacing(2)
        copy.addWidget(self.title)
        copy.addWidget(self.status)
        copy.addWidget(self.metrics)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(6)
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.quit_button)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        right.addLayout(copy)
        right.addLayout(buttons)

        root = QHBoxLayout()
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(14)
        root.addWidget(self.orb)
        root.addLayout(right, 1)
        self.widget.setLayout(root)
        self.widget.setStyleSheet(_FLOATING_STYLE)

        self.timer = QTimer()
        self.timer.setInterval(70)
        self.timer.timeout.connect(self.orb.tick)
        self.timer.start()
        self.set_status(running=False, paused=False, fps=0.0, resolution="-", latency_ms=None, dropped=0)

    def show(self) -> None:
        if not self._positioned:
            self._move_to_default_position()
        self.widget.show()
        self.widget.raise_()

    def hide(self) -> None:
        self.widget.hide()

    def set_status(
        self,
        *,
        running: bool,
        paused: bool,
        fps: float,
        resolution: str,
        latency_ms: float | None,
        dropped: int,
    ) -> None:
        self._running = running
        self._paused = paused
        if running and paused:
            label = "Paused"
            tone = "paused"
        elif running:
            label = "Active"
            tone = "active"
        else:
            label = "Idle"
            tone = "idle"
        latency = "-" if latency_ms is None else f"{latency_ms:.1f} ms"
        self.status.setText(f"{label} - local MCP")
        self.metrics.setText(f"{fps:.1f} FPS - {resolution} - {latency} - drop {dropped}")
        self.pause_button.setText("Resume" if paused else "Pause")
        self.pause_button.setEnabled(running)
        self.stop_button.setEnabled(running)
        self.run_button.setEnabled(not running)
        self.orb.set_tone(tone)

    def _move_to_default_position(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen is None:
            self._positioned = True
            return
        available = screen.availableGeometry()
        self.widget.move(available.right() - self.widget.width() - 28, available.top() + 28)
        self._positioned = True


def _create_floating_widget():
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QWidget

    class FloatingWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._drag_origin: QPoint | None = None

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event) -> None:
            if self._drag_origin is not None:
                self.move(event.globalPosition().toPoint() - self._drag_origin)
                event.accept()

        def mouseReleaseEvent(self, event) -> None:
            self._drag_origin = None
            event.accept()

        def paintEvent(self, _event) -> None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect().adjusted(1, 1, -1, -1)
            painter.setPen(QPen(QColor("#2a3750"), 1))
            painter.setBrush(QColor(8, 12, 19, 235))
            painter.drawRoundedRect(rect, 14, 14)
            painter.end()

    return FloatingWidget()


def _create_pulse_orb():
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import QWidget

    class PulseOrbWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._phase = 0
            self._tone = "idle"
            self.setMinimumSize(72, 72)
            self.setMaximumSize(72, 72)

        def sizeHint(self) -> QSize:
            return QSize(72, 72)

        def set_tone(self, tone: str) -> None:
            self._tone = tone
            self.update()

        def tick(self) -> None:
            self._phase = (self._phase + 7) % 360
            self.update()

        def paintEvent(self, _event) -> None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect().adjusted(8, 8, -8, -8)
            if self._tone == "active":
                main = QColor("#ffb547")
                alt = QColor("#4be3ff")
            elif self._tone == "paused":
                main = QColor("#a7b2c7")
                alt = QColor("#ffb547")
            else:
                main = QColor("#4b5870")
                alt = QColor("#75839c")

            painter.setPen(QPen(QColor("#111723"), 2))
            painter.setBrush(QColor("#070a10"))
            painter.drawEllipse(rect)

            painter.setPen(QPen(main, 3))
            painter.drawArc(rect, self._phase * 16, 210 * 16)
            painter.setPen(QPen(alt, 2))
            painter.drawArc(rect.adjusted(8, 8, -8, -8), (self._phase + 120) * 16, 260 * 16)
            painter.setPen(QPen(QColor(main.red(), main.green(), main.blue(), 120), 1))
            center_x = self.width() // 2
            center_y = self.height() // 2
            for offset in (0, 45, 105, 168):
                painter.save()
                painter.translate(center_x, center_y)
                painter.rotate(offset + self._phase / 7)
                painter.drawLine(0, -24, 0, 24)
                painter.restore()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(main)
            painter.drawEllipse(self.width() // 2 - 5, self.height() // 2 - 5, 10, 10)
            painter.end()

    return PulseOrbWidget()


_FLOATING_STYLE = """
QWidget {
    color: #eef4ff;
    font-family: "Segoe UI";
    font-size: 12px;
}
QLabel#floatingTitle {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}
QLabel#floatingStatus {
    color: #ffbf63;
    font-size: 12px;
}
QLabel#floatingMetrics {
    color: #9fb1c8;
    font-size: 11px;
}
QPushButton#floatingButton {
    background: #151d2b;
    color: #dce8f7;
    border: 1px solid #2d3b52;
    border-radius: 6px;
    padding: 5px 8px;
}
QPushButton#floatingButton:hover {
    border-color: #ffb547;
    color: #ffffff;
}
QPushButton#floatingButton:disabled {
    color: #566377;
    border-color: #202838;
}
"""
