from __future__ import annotations


class FloatingShell:
    """Draggable translucent shell for the compact floating controller."""

    def __init__(self) -> None:
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
                painter.setPen(QPen(QColor("#2c3847"), 1))
                painter.setBrush(QColor(9, 12, 16, 238))
                painter.drawRoundedRect(rect, 10, 10)
                painter.end()

        self.widget = FloatingWidget()


class StatusGlyph:
    """Small animated signal mark used as active/paused/idle feedback."""

    def __init__(self) -> None:
        from PySide6.QtCore import QSize, Qt
        from PySide6.QtGui import QColor, QPainter, QPen
        from PySide6.QtWidgets import QWidget

        class Glyph(QWidget):
            def __init__(self) -> None:
                super().__init__()
                self._phase = 0
                self._tone = "idle"
                self.setMinimumSize(42, 42)
                self.setMaximumSize(42, 42)

            def sizeHint(self) -> QSize:
                return QSize(42, 42)

            def set_tone(self, tone: str) -> None:
                self._tone = tone
                self.update()

            def tick(self) -> None:
                self._phase = (self._phase + 9) % 360
                self.update()

            def paintEvent(self, _event) -> None:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                main = QColor("#39d98a")
                if self._tone == "paused":
                    main = QColor("#ffb24a")
                elif self._tone == "idle":
                    main = QColor("#7b8798")

                rect = self.rect().adjusted(6, 6, -6, -6)
                painter.setPen(QPen(QColor("#1c2633"), 2))
                painter.setBrush(QColor("#06080b"))
                painter.drawRoundedRect(rect, 8, 8)
                painter.setPen(QPen(main, 3))
                painter.drawArc(rect.adjusted(5, 5, -5, -5), self._phase * 16, 240 * 16)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(main)
                painter.drawEllipse(17, 17, 8, 8)
                painter.end()

        self.widget = Glyph()


FLOATING_STYLE = """
QWidget {
    color: #eef4ff;
    font-family: "Segoe UI";
    font-size: 11px;
}
QLabel#floatingTitle {
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
}
QLabel#floatingStatus {
    color: #b8c4d6;
}
QLabel#floatingMetrics {
    color: #7fd7ff;
    font-size: 10px;
}
QPushButton#floatingButton {
    background: #151a23;
    color: #dce8f7;
    border: 1px solid #2d3b52;
    border-radius: 5px;
    padding: 4px 7px;
}
QPushButton#floatingButton:hover {
    border-color: #39d98a;
    color: #ffffff;
}
QPushButton#floatingButton:disabled {
    color: #566377;
    border-color: #202838;
}
"""
