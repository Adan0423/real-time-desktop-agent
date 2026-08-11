from __future__ import annotations

from rtda.capture.interface import CaptureStats

from desktop.ui.widgets import MetricTile, SectionPanel, make_label


class RuntimePanel:
    """Runtime buttons and live metrics for the complement."""

    def __init__(self, *, enable_perception_tools: bool) -> None:
        from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout

        self.start_button = QPushButton("Iniciar")
        self.pause_button = QPushButton("Pausar")
        self.stop_button = QPushButton("Detener")
        self.uia_button = QPushButton("UIA")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.uia_button.setEnabled(enable_perception_tools)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(7)
        for button in (self.start_button, self.pause_button, self.stop_button):
            actions.addWidget(button)
        if enable_perception_tools:
            actions.addWidget(self.uia_button)

        self.metrics = {
            "fps": MetricTile("FPS", "0.0"),
            "resolution": MetricTile("Resolucion", "-"),
            "latency": MetricTile("Latencia", "-"),
            "drops": MetricTile("Drops", "0"),
            "frames": MetricTile("Frames", "0"),
            "errors": MetricTile("Errores", "0"),
        }
        metric_grid = QGridLayout()
        metric_grid.setHorizontalSpacing(6)
        metric_grid.setVerticalSpacing(6)
        for idx, metric in enumerate(self.metrics.values()):
            metric_grid.addWidget(metric.widget, idx // 2, idx % 2)

        self.uia_label = make_label("UIA: sin inspeccion", "mutedText")
        self.uia_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        layout.addLayout(actions)
        layout.addLayout(metric_grid)
        if enable_perception_tools:
            layout.addWidget(self.uia_label)

        self.widget = SectionPanel("Runtime", layout).widget

    def set_running_state(self, *, running: bool, paused: bool) -> None:
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.stop_button.setEnabled(running)
        self.pause_button.setText("Reanudar" if paused else "Pausar")

    def set_metrics(self, stats: CaptureStats) -> str:
        resolution = "-"
        if stats.latest_width and stats.latest_height:
            resolution = f"{stats.latest_width}x{stats.latest_height}"
        latency = "-" if stats.capture_latency_ms is None else f"{stats.capture_latency_ms:.2f} ms"
        self.metrics["fps"].set_text(f"{stats.capture_fps:.1f}")
        self.metrics["resolution"].set_text(resolution)
        self.metrics["latency"].set_text(latency)
        self.metrics["drops"].set_text(str(stats.buffer_dropped_frames))
        self.metrics["frames"].set_text(str(stats.frames_captured))
        self.metrics["errors"].set_text(str(stats.backend_errors))
        return resolution

    def set_uia_status(self, text: str) -> None:
        self.uia_label.setText(text)
