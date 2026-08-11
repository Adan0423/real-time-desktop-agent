from __future__ import annotations

from dataclasses import dataclass

from rtda.ai.client import AIClientConfig, default_model
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo
from rtda.capture.region import Region

from desktop.ui.widgets import MetricTile, SectionPanel, StatusPill, coord_spin, make_label


@dataclass(frozen=True, slots=True)
class TargetSelection:
    backend: str
    target_fps: int
    monitor_index: int
    window_title: str | None
    region: Region | None
    show_border: bool


class ControlSidebar:
    """Compact left rail for local desktop testing of the RTDA complement."""

    def __init__(
        self,
        *,
        config: CaptureConfig,
        enable_perception_tools: bool,
        show_capture_overlay: bool = True,
    ) -> None:
        from PySide6.QtWidgets import QFrame, QTabWidget, QVBoxLayout

        self.status = StatusPill("Extension local lista")
        self.target = TargetPanel(
            config=config,
            enable_perception_tools=enable_perception_tools,
            show_capture_overlay=show_capture_overlay,
        )
        self.runtime = RuntimePanel(enable_perception_tools=enable_perception_tools)
        self.ai = AiPanel()

        title = make_label("RTDA Desktop", "appTitle")
        subtitle = make_label("Control local del complemento IA", "mutedText")
        tabs = QTabWidget()
        tabs.setObjectName("modeTabs")
        tabs.addTab(self._capture_tab(), "Captura")
        tabs.addTab(self.ai.widget, "IA")

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.status.widget)
        layout.addWidget(tabs, 1)

        self.widget = QFrame()
        self.widget.setObjectName("sidebar")
        self.widget.setMinimumWidth(308)
        self.widget.setMaximumWidth(330)
        self.widget.setLayout(layout)

    def set_monitors(self, monitors: list[MonitorInfo]) -> None:
        self.target.set_monitors(monitors)

    def set_status(self, *, running: bool, paused: bool) -> None:
        if running and paused:
            self.status.set("Extension pausada", "paused")
            return
        if running:
            self.status.set("Extension activa", "active")
            return
        self.status.set("Extension local lista", "idle")

    def _capture_tab(self):
        from PySide6.QtWidgets import QWidget, QVBoxLayout

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.target.widget)
        layout.addWidget(self.runtime.widget)
        layout.addStretch(1)

        tab = QWidget()
        tab.setLayout(layout)
        return tab


class TargetPanel:
    def __init__(
        self,
        *,
        config: CaptureConfig,
        enable_perception_tools: bool,
        show_capture_overlay: bool,
    ) -> None:
        from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLineEdit, QSpinBox

        self.monitor_combo = QComboBox()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["dxgi", "wgc"])
        self.backend_combo.setCurrentText(config.backend)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(config.target_fps)
        self.window_title = QLineEdit()
        self.window_title.setPlaceholderText("Titulo de ventana para WGC")
        self.region_enabled = QCheckBox("Region")
        self.overlay_enabled = QCheckBox("Marco verde")
        self.overlay_enabled.setChecked(show_capture_overlay)
        self.change_detection_enabled = QCheckBox("Cambios")
        self.change_detection_enabled.setChecked(False)
        self.left_spin = coord_spin(config.region.left if config.region else 0)
        self.top_spin = coord_spin(config.region.top if config.region else 0)
        self.right_spin = coord_spin(config.region.right if config.region else 3840)
        self.bottom_spin = coord_spin(config.region.bottom if config.region else 2160)
        self.region_enabled.setChecked(config.region is not None)
        self.region_enabled.toggled.connect(self._set_region_controls_enabled)

        fields = QGridLayout()
        fields.setHorizontalSpacing(8)
        fields.setVerticalSpacing(7)
        for row, (label, widget) in enumerate(
            (
                ("Monitor", self.monitor_combo),
                ("Backend", self.backend_combo),
                ("FPS", self.fps_spin),
                ("Ventana", self.window_title),
            )
        ):
            fields.addWidget(make_label(label, "fieldLabel"), row, 0)
            fields.addWidget(widget, row, 1)

        toggles = QHBoxLayout()
        toggles.setContentsMargins(0, 0, 0, 0)
        toggles.setSpacing(10)
        toggles.addWidget(self.region_enabled)
        toggles.addWidget(self.overlay_enabled)
        if enable_perception_tools:
            toggles.addWidget(self.change_detection_enabled)
        toggles.addStretch(1)
        fields.addLayout(toggles, 4, 0, 1, 2)

        region = QGridLayout()
        region.setHorizontalSpacing(6)
        region.setVerticalSpacing(6)
        for idx, (label, widget) in enumerate(
            (
                ("L", self.left_spin),
                ("T", self.top_spin),
                ("R", self.right_spin),
                ("B", self.bottom_spin),
            )
        ):
            region.addWidget(make_label(label, "fieldLabel"), idx // 2, (idx % 2) * 2)
            region.addWidget(widget, idx // 2, (idx % 2) * 2 + 1)
        fields.addLayout(region, 5, 0, 1, 2)

        self.widget = SectionPanel("Objetivo", fields).widget
        self._set_region_controls_enabled(self.region_enabled.isChecked())

    def set_monitors(self, monitors: list[MonitorInfo]) -> None:
        self.monitor_combo.clear()
        if not monitors:
            self.monitor_combo.addItem("0: monitor principal")
            return
        for monitor in monitors:
            self.monitor_combo.addItem(monitor.label)

    def selection(self) -> TargetSelection:
        region = None
        if self.region_enabled.isChecked():
            region = Region(
                self.left_spin.value(),
                self.top_spin.value(),
                self.right_spin.value(),
                self.bottom_spin.value(),
            )
        window_title = self.window_title.text().strip() or None
        backend = "wgc" if window_title else self.backend_combo.currentText()
        if window_title:
            self.backend_combo.setCurrentText("wgc")
        return TargetSelection(
            backend=backend,
            target_fps=self.fps_spin.value(),
            monitor_index=max(0, self.monitor_combo.currentIndex()),
            window_title=window_title,
            region=region,
            show_border=self.overlay_enabled.isChecked(),
        )

    def _set_region_controls_enabled(self, enabled: bool) -> None:
        for widget in (self.left_spin, self.top_spin, self.right_spin, self.bottom_spin):
            widget.setEnabled(enabled)


class RuntimePanel:
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


class AiPanel:
    def __init__(self) -> None:
        from PySide6.QtWidgets import QComboBox, QGridLayout, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget

        self.provider = QComboBox()
        self.provider.addItems(["openai", "anthropic"])
        self.model = QLineEdit(default_model("openai"))
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.prompt = QTextEdit()
        self.prompt.setMinimumHeight(82)
        self.prompt.setPlaceholderText("Pregunta usando el contexto capturado por RTDA.")
        self.ask_button = QPushButton("Consultar IA")
        self.output = make_label("IA: esperando prompt", "mutedText")
        self.output.setWordWrap(True)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(7)
        for row, (label, widget) in enumerate(
            (
                ("Proveedor", self.provider),
                ("Modelo", self.model),
                ("Token", self.token),
            )
        ):
            grid.addWidget(make_label(label, "fieldLabel"), row, 0)
            grid.addWidget(widget, row, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(9)
        layout.addLayout(grid)
        layout.addWidget(self.prompt)
        layout.addWidget(self.ask_button)
        layout.addWidget(self.output, 1)

        self.widget = QWidget()
        self.widget.setLayout(layout)

    def sync_model(self, provider: str) -> None:
        if provider in ("openai", "anthropic"):
            self.model.setText(default_model(provider))

    def request_config(self) -> AIClientConfig:
        token = self.token.text().strip() or None
        model = self.model.text().strip() or None
        return AIClientConfig(provider=self.provider.currentText(), api_key=token, model=model)

    def prompt_text(self) -> str:
        return self.prompt.toPlainText().strip()

    def set_busy(self, busy: bool) -> None:
        self.ask_button.setEnabled(not busy)
        self.output.setText("IA: consultando proveedor" if busy else self.output.text())
