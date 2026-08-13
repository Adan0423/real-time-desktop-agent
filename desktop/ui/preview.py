from __future__ import annotations

from typing import Any


class PreviewPanel:
    """Realtime frame preview and compact capture summary."""

    def __init__(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

        self._qt = Qt
        title = QLabel("🖼️ Vista de Pantalla en Tiempo Real")
        title.setObjectName("panelTitle")
        self.summary = QLabel("⏸️ Captura Inactiva")
        self.summary.setObjectName("mutedText")
        self.surface = QLabel("🎥 Presiona '▶ Iniciar' (F5) para previsualizar el escritorio en vivo")
        self.surface.setObjectName("previewSurface")
        self.surface.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.surface.setMinimumSize(640, 440)
        self.surface.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.summary)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addWidget(self.surface, 1)

        self.widget = QFrame()
        self.widget.setObjectName("previewPanel")
        self.widget.setLayout(layout)

    def clear(self) -> None:
        self.surface.clear()
        self.surface.setText("🎥 Presiona '▶ Iniciar' (F5) para previsualizar el escritorio en vivo")
        self.summary.setText("⏸️ Captura Inactiva")


    def set_summary(self, *, running: bool, paused: bool, backend: str, resolution: str) -> None:
        if running and paused:
            state = "Pausado"
        elif running:
            state = "Activo"
        else:
            state = "Listo"
        self.summary.setText(f"{state} | {backend} | {resolution}")

    def set_frame(self, frame, *, change_result: Any | None = None) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QImage, QPainter, QPen, QPixmap

        data = frame.data
        image_format = _qimage_format_for_channels(data.shape[2], QImage)
        image = QImage(data.data, frame.width, frame.height, data.strides[0], image_format).copy()
        pixmap = QPixmap.fromImage(image)
        if change_result is not None:
            pixmap = _draw_change_regions(pixmap, change_result, QPainter, QPen, Qt)
        scaled = pixmap.scaled(
            self.surface.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.surface.setPixmap(scaled)


def _draw_change_regions(pixmap, result: Any, painter_cls, pen_cls, qt):
    if not getattr(result, "regions", None):
        return pixmap
    overlay = pixmap.copy()
    painter = painter_cls(overlay)
    pen = pen_cls(qt.GlobalColor.red)
    pen.setWidth(2)
    painter.setPen(pen)
    for region in result.regions:
        bbox = region.bbox
        painter.drawRect(bbox.left, bbox.top, bbox.width, bbox.height)
    painter.end()
    return overlay


def _qimage_format_for_channels(channel_count: int, qimage_cls):
    if channel_count == 4:
        bgra_format = getattr(qimage_cls.Format, "Format_BGRA8888", None)
        if bgra_format is not None:
            return bgra_format
        return qimage_cls.Format.Format_ARGB32
    return qimage_cls.Format.Format_RGB888
