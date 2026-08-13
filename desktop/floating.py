from __future__ import annotations

from collections.abc import Callable

from desktop.ui.floating_widgets import FLOATING_STYLE, FloatingShell, StatusGlyph


class RTDAFloatingControl:
    """Always-on-top compact control for the RTDA complement runtime."""

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

        shell = FloatingShell()
        self.widget = shell.widget
        self.widget.setWindowTitle("RTDA")
        self.widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.widget.resize(330, 86)

        self.glyph = StatusGlyph()
        self.orb = self.glyph.widget
        self.title = QLabel("RTDA Extension")
        self.title.setObjectName("floatingTitle")
        self.status = QLabel("Idle - local MCP")
        self.status.setObjectName("floatingStatus")
        self.metrics = QLabel("0.0 FPS | - | drop 0")
        self.metrics.setObjectName("floatingMetrics")

        self.open_button = _button("🗔", on_open)
        self.run_button = _button("▶", on_start)
        self.pause_button = _button("⏸", on_pause)
        self.stop_button = _button("⏹", on_stop)
        self.quit_button = _button("❌", on_quit)

        copy = QVBoxLayout()
        copy.setContentsMargins(0, 0, 0, 0)
        copy.setSpacing(1)
        copy.addWidget(self.title)
        copy.addWidget(self.status)
        copy.addWidget(self.metrics)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(5)
        for button in (
            self.open_button,
            self.run_button,
            self.pause_button,
            self.stop_button,
            self.quit_button,
        ):
            buttons.addWidget(button)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(6)
        right.addLayout(copy)
        right.addLayout(buttons)

        root = QHBoxLayout()
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)
        root.addWidget(self.glyph.widget)
        root.addLayout(right, 1)
        self.widget.setLayout(root)
        self.widget.setStyleSheet(FLOATING_STYLE)

        self.timer = QTimer()
        self.timer.setInterval(70)
        self.timer.timeout.connect(self.glyph.widget.tick)
        self.timer.start()
        self.set_status(running=False, paused=False, fps=0.0, resolution="-", latency_ms=None, dropped=0)

    def show(self) -> None:
        if not self._positioned:
            self._move_to_default_position()
        self.widget.show()
        self.widget.raise_()

    def hide(self) -> None:
        self.widget.hide()

    def shutdown(self) -> None:
        self.timer.stop()
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
            label = "Pausado"
            tone = "paused"
        elif running:
            label = "Activo"
            tone = "active"
        else:
            label = "Listo"
            tone = "idle"
        latency = "-" if latency_ms is None else f"{latency_ms:.1f} ms"
        self.status.setText(f"{label} - local MCP")
        self.metrics.setText(f"{fps:.1f} FPS | {resolution} | {latency} | drop {dropped}")
        self.pause_button.setText("▶" if paused else "⏸")
        self.pause_button.setEnabled(running)
        self.stop_button.setEnabled(running)
        self.run_button.setEnabled(not running)
        self.glyph.widget.set_tone(tone)


    def _move_to_default_position(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen is None:
            self._positioned = True
            return
        available = screen.availableGeometry()
        self.widget.move(available.right() - self.widget.width() - 22, available.top() + 22)
        self._positioned = True


def _button(text: str, callback: Callable[[], None]):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton

    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setObjectName("floatingButton")
    button.clicked.connect(callback)
    return button
