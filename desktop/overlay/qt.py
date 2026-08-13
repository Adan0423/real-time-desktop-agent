import sys

from desktop.overlay.geometry import OverlayRect

_QAPP_INSTANCE = None


def get_or_create_qapp():
    global _QAPP_INSTANCE
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        if _QAPP_INSTANCE is None:
            _QAPP_INSTANCE = QApplication(sys.argv if sys.argv else [""])
        app = _QAPP_INSTANCE
    return app


class GreenCaptureOverlay:
    def __init__(self, *, border_width: int = 4) -> None:
        get_or_create_qapp()
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor

        self.Qt = Qt
        self.QColor = QColor
        self._border_width = border_width
        self._rect: OverlayRect | None = None
        self.widget = _OverlayWidget(border_width=border_width)
        self.widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.widget.hide()

    def show_rect(self, rect: OverlayRect | None) -> None:
        if rect is None or not rect.valid:
            self.hide()
            return
        expanded = rect.expanded(self._border_width)
        self._rect = expanded
        self.widget.setGeometry(expanded.left, expanded.top, expanded.width, expanded.height)
        self.widget.show()
        self.widget.raise_()
        self.widget.update()

    def hide(self) -> None:
        self._rect = None
        self.widget.hide()


class _OverlayWidget:
    def __init__(self, *, border_width: int) -> None:
        get_or_create_qapp()
        from PySide6.QtWidgets import QWidget

        class OverlayWidget(QWidget):
            def __init__(self, width: int) -> None:
                super().__init__()
                self._border_width = width

            def paintEvent(self, _event) -> None:
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QColor, QPainter, QPen

                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                pen = QPen(QColor(0, 255, 102, 230))
                pen.setWidth(self._border_width)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                inset = self._border_width // 2
                painter.drawRect(
                    inset,
                    inset,
                    max(0, self.width() - self._border_width),
                    max(0, self.height() - self._border_width),
                )
                painter.end()

        self._impl = OverlayWidget(border_width)

    def __getattr__(self, name: str):
        return getattr(self._impl, name)
