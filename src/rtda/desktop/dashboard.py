from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from typing import Any

from rtda.ai.client import AIClient, AIClientConfig, AIClientError, default_model
from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region
from rtda.complement import RTDAComplementRuntime
from rtda.desktop.floating import RTDAFloatingControl
from rtda.overlay.geometry import capture_rect_from_config
from rtda.overlay.qt import GreenCaptureOverlay


class CaptureDashboard:
    def __init__(
        self,
        config: CaptureConfig | None = None,
        *,
        enable_perception_tools: bool = False,
        show_capture_overlay: bool = True,
        show_floating_control: bool = True,
    ) -> None:
        try:
            from PySide6.QtCore import Qt, QTimer
            from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
            from PySide6.QtWidgets import (
                QCheckBox,
                QComboBox,
                QFrame,
                QGridLayout,
                QHBoxLayout,
                QLabel,
                QLineEdit,
                QPushButton,
                QSizePolicy,
                QSpinBox,
                QTextEdit,
                QVBoxLayout,
                QWidget,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Missing optional dependency 'PySide6'. "
                "Install with: python -m pip install -e .[gui]"
            ) from exc

        self.Qt = Qt
        self.QFrame = QFrame
        self.QGridLayout = QGridLayout
        self.QHBoxLayout = QHBoxLayout
        self.QImage = QImage
        self.QLabel = QLabel
        self.QPainter = QPainter
        self.QPen = QPen
        self.QPixmap = QPixmap
        self.QPushButton = QPushButton
        self.QSizePolicy = QSizePolicy
        self.QTimer = QTimer
        self.QVBoxLayout = QVBoxLayout
        self.QWidget = QWidget

        self._config = config or CaptureConfig()
        self._enable_perception_tools = enable_perception_tools
        self._show_floating_control = show_floating_control
        self._runtime = RTDAComplementRuntime(self._config)
        self._overlay = GreenCaptureOverlay()
        self._last_overlay_update = 0.0
        self._shutdown_started = False
        self._ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rtda-ai")
        self._ai_future: Future[str] | None = None
        self._change_processor: Any | None = None
        self._uia_inspector: Any | None = None
        self._latest_change: Any | None = None
        self._reset_perception_tools()

        class DashboardWindow(QWidget):
            def __init__(self, dashboard: "CaptureDashboard") -> None:
                super().__init__()
                self._dashboard = dashboard

            def closeEvent(self, event) -> None:
                self._dashboard._handle_close_event(event)

        self.widget = DashboardWindow(self)
        self.widget.setObjectName("rtdaRoot")
        self.widget.setWindowTitle("RTDA Desktop Control Surface")
        self.widget.resize(1240, 780)

        self.monitor_combo = QComboBox()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["dxgi", "wgc"])
        self.backend_combo.setCurrentText(self._config.backend)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(self._config.target_fps)
        self.window_title = QLineEdit()
        self.window_title.setPlaceholderText("Titulo de ventana para WGC")
        self.region_enabled = QCheckBox("Region")
        self.overlay_enabled = QCheckBox("Marco verde")
        self.overlay_enabled.setChecked(show_capture_overlay)
        self.change_detection_enabled = QCheckBox("Detectar cambios")
        self.change_detection_enabled.setChecked(False)
        self.left_spin = self._coord_spin()
        self.top_spin = self._coord_spin()
        self.right_spin = self._coord_spin(3840)
        self.bottom_spin = self._coord_spin(2160)

        self.start_button = QPushButton("Iniciar")
        self.pause_button = QPushButton("Pausar")
        self.stop_button = QPushButton("Detener")
        self.uia_button = QPushButton("Inspeccionar UIA")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.uia_button.setEnabled(self._enable_perception_tools)

        self.extension_state = QLabel("Extension local lista")
        self.extension_state.setObjectName("stateChip")
        self.fps_value = self._metric_value("0.0")
        self.resolution_value = self._metric_value("-")
        self.latency_value = self._metric_value("-")
        self.drop_value = self._metric_value("0")
        self.frames_value = self._metric_value("0")
        self.errors_value = self._metric_value("0")

        self.uia_label = QLabel("UIA: sin inspeccion")
        self.uia_label.setObjectName("mutedText")
        self.uia_label.setWordWrap(True)

        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["openai", "anthropic"])
        self.ai_model = QLineEdit(default_model("openai"))
        self.ai_token = QLineEdit()
        self.ai_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_prompt = QTextEdit()
        self.ai_prompt.setMinimumHeight(92)
        self.ai_prompt.setPlaceholderText("Pregunta al proveedor IA usando el contexto del complemento RTDA.")
        self.ai_button = QPushButton("Consultar IA")
        self.ai_output = QLabel("IA: esperando prompt")
        self.ai_output.setObjectName("mutedText")
        self.ai_output.setWordWrap(True)

        self.preview_label = QLabel("Sin frame")
        self.preview_label.setObjectName("previewSurface")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(780, 520)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._floating = RTDAFloatingControl(
            on_open=self._show_main_window,
            on_start=self.start,
            on_pause=self.pause_or_resume,
            on_stop=self.stop,
            on_quit=self.quit,
        )

        self._build_layout()
        self._apply_theme()

        self.timer = QTimer()
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._update_preview)
        self.ai_timer = QTimer()
        self.ai_timer.setInterval(100)
        self.ai_timer.timeout.connect(self._poll_ai_result)

        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause_or_resume)
        self.stop_button.clicked.connect(self.stop)
        self.uia_button.clicked.connect(self.inspect_uia)
        self.overlay_enabled.stateChanged.connect(self._refresh_overlay)
        self.ai_provider.currentTextChanged.connect(self._sync_ai_model)
        self.ai_button.clicked.connect(self.ask_ai)
        self.widget.destroyed.connect(self._shutdown)

        self._load_monitors()
        self._update_runtime_status()

    def show(self) -> None:
        self.widget.show()
        if self._show_floating_control:
            self._floating.show()

    def quit(self) -> None:
        self.stop()
        self._shutdown()
        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()

    def start(self) -> None:
        self.stop()
        region = None
        if self.region_enabled.isChecked():
            region = Region(
                self.left_spin.value(),
                self.top_spin.value(),
                self.right_spin.value(),
                self.bottom_spin.value(),
            )
        window_title = self.window_title.text().strip() or None
        backend = self.backend_combo.currentText()
        if window_title:
            backend = "wgc"
            self.backend_combo.setCurrentText("wgc")
        config = replace(
            self._config,
            backend=backend,
            target_fps=self.fps_spin.value(),
            monitor_index=max(0, self.monitor_combo.currentIndex()),
            region=region,
            window_title=window_title,
        )
        self._runtime.start_capture(config)
        self._reset_perception_tools()
        self.timer.start()
        self._refresh_overlay()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.pause_button.setText("Pausar")
        self._update_runtime_status()

    def stop(self) -> None:
        self.timer.stop()
        self._runtime.stop_capture()
        self._overlay.hide()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("Pausar")
        self.preview_label.clear()
        self.preview_label.setText("Sin frame")
        self._update_runtime_status()

    def pause_or_resume(self) -> None:
        if not self._runtime.running:
            return
        if self._runtime.paused:
            self._runtime.resume_capture()
            self.pause_button.setText("Pausar")
            self.timer.start()
        else:
            self._runtime.pause_capture()
            self.pause_button.setText("Reanudar")
        self._update_runtime_status()

    def inspect_uia(self) -> None:
        if not self._enable_perception_tools:
            return
        if self._uia_inspector is None:
            self._reset_perception_tools()
        if self._uia_inspector is None:
            return
        window_title = self.window_title.text().strip() or None
        snapshot = self._uia_inspector.snapshot(window_title=window_title)
        if self._change_processor is not None:
            self._change_processor.metrics.record_uia_snapshot(
                timestamp=time.perf_counter(),
                uia_latency_ms=snapshot.latency_ms,
                element_count=snapshot.element_count,
            )
        error_text = f", errores: {len(snapshot.errors)}" if snapshot.errors else ""
        target = f" ({window_title})" if window_title else ""
        self.uia_label.setText(
            f"UIA{target}: {snapshot.element_count} elementos, "
            f"{snapshot.latency_ms:.1f} ms{error_text}"
        )

    def ask_ai(self) -> None:
        if self._ai_future is not None and not self._ai_future.done():
            return
        prompt = self.ai_prompt.toPlainText().strip()
        if not prompt:
            self.ai_output.setText("IA: escribe un prompt primero")
            return
        provider = self.ai_provider.currentText()
        token = self.ai_token.text().strip() or None
        model = self.ai_model.text().strip() or None
        config = AIClientConfig(provider=provider, api_key=token, model=model)
        system = self._ai_system_prompt()
        self.ai_button.setEnabled(False)
        self.ai_output.setText("IA: consultando proveedor")
        self._ai_future = self._ai_executor.submit(self._ask_ai_worker, config, prompt, system)
        self.ai_timer.start()

    def _build_layout(self) -> None:
        left = self.QVBoxLayout()
        left.setContentsMargins(18, 18, 18, 18)
        left.setSpacing(14)
        left.addWidget(self._header_panel())
        left.addWidget(self._target_panel())
        left.addWidget(self._runtime_panel())
        left.addWidget(self._ai_panel(), 1)

        sidebar = self.QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setLayout(left)
        sidebar.setMinimumWidth(360)
        sidebar.setMaximumWidth(390)

        preview_layout = self.QVBoxLayout()
        preview_layout.setContentsMargins(20, 18, 20, 20)
        preview_layout.setSpacing(14)
        preview_layout.addWidget(self._preview_header())
        preview_layout.addWidget(self.preview_label, 1)

        preview = self.QFrame()
        preview.setObjectName("previewPanel")
        preview.setLayout(preview_layout)

        root = self.QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(sidebar)
        root.addWidget(preview, 1)
        self.widget.setLayout(root)

    def _header_panel(self):
        title = self.QLabel("RTDA Control Surface")
        title.setObjectName("appTitle")
        subtitle = self.QLabel("Consola local que consume el complemento IA")
        subtitle.setObjectName("mutedText")
        subtitle.setWordWrap(True)

        layout = self.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.extension_state)

        panel = self.QFrame()
        panel.setObjectName("heroPanel")
        panel.setLayout(layout)
        return panel

    def _target_panel(self):
        grid = self.QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(9)
        for row, (label, widget) in enumerate(
            (
                ("Monitor", self.monitor_combo),
                ("Backend", self.backend_combo),
                ("FPS", self.fps_spin),
                ("Ventana", self.window_title),
            )
        ):
            grid.addWidget(self._field_label(label), row, 0)
            grid.addWidget(widget, row, 1)

        toggles = self.QHBoxLayout()
        toggles.setContentsMargins(0, 0, 0, 0)
        toggles.setSpacing(14)
        toggles.addWidget(self.region_enabled)
        toggles.addWidget(self.overlay_enabled)
        if self._enable_perception_tools:
            toggles.addWidget(self.change_detection_enabled)
        toggles.addStretch(1)
        grid.addLayout(toggles, 4, 0, 1, 2)

        region = self.QGridLayout()
        region.setHorizontalSpacing(8)
        region.setVerticalSpacing(8)
        for idx, (label, widget) in enumerate(
            (
                ("L", self.left_spin),
                ("T", self.top_spin),
                ("R", self.right_spin),
                ("B", self.bottom_spin),
            )
        ):
            region.addWidget(self._field_label(label), idx // 2, (idx % 2) * 2)
            region.addWidget(widget, idx // 2, (idx % 2) * 2 + 1)
        grid.addLayout(region, 5, 0, 1, 2)

        return self._section("Objetivo de captura", grid)

    def _runtime_panel(self):
        actions = self.QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        actions.addWidget(self.start_button)
        actions.addWidget(self.pause_button)
        actions.addWidget(self.stop_button)
        if self._enable_perception_tools:
            actions.addWidget(self.uia_button)

        metrics = self.QGridLayout()
        metrics.setHorizontalSpacing(8)
        metrics.setVerticalSpacing(8)
        for idx, card in enumerate(
            (
                self._metric_card("FPS", self.fps_value),
                self._metric_card("Resolucion", self.resolution_value),
                self._metric_card("Latencia", self.latency_value),
                self._metric_card("Drops", self.drop_value),
                self._metric_card("Frames", self.frames_value),
                self._metric_card("Errores", self.errors_value),
            )
        ):
            metrics.addWidget(card, idx // 2, idx % 2)

        layout = self.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(actions)
        layout.addLayout(metrics)
        if self._enable_perception_tools:
            layout.addWidget(self.uia_label)
        return self._section("Runtime del complemento", layout)

    def _ai_panel(self):
        grid = self.QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(9)
        for row, (label, widget) in enumerate(
            (
                ("Proveedor", self.ai_provider),
                ("Modelo", self.ai_model),
                ("Token", self.ai_token),
            )
        ):
            grid.addWidget(self._field_label(label), row, 0)
            grid.addWidget(widget, row, 1)

        layout = self.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addLayout(grid)
        layout.addWidget(self.ai_prompt)
        layout.addWidget(self.ai_button)
        layout.addWidget(self.ai_output)
        return self._section("Prueba IA", layout)

    def _preview_header(self):
        title = self.QLabel("Vista capturada")
        title.setObjectName("panelTitle")
        subtitle = self.QLabel("La app no es el motor: visualiza y controla el complemento local RTDA.")
        subtitle.setObjectName("mutedText")

        layout = self.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        panel = self.QFrame()
        panel.setLayout(layout)
        return panel

    def _section(self, title: str, content_layout):
        label = self.QLabel(title)
        label.setObjectName("sectionTitle")
        layout = self.QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(label)
        layout.addLayout(content_layout)
        panel = self.QFrame()
        panel.setObjectName("sectionPanel")
        panel.setLayout(layout)
        return panel

    def _metric_card(self, label: str, value_widget):
        label_widget = self.QLabel(label)
        label_widget.setObjectName("metricLabel")
        layout = self.QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        panel = self.QFrame()
        panel.setObjectName("metricCard")
        panel.setLayout(layout)
        return panel

    def _metric_value(self, text: str):
        label = self.QLabel(text)
        label.setObjectName("metricValue")
        return label

    def _field_label(self, text: str):
        label = self.QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _load_monitors(self) -> None:
        self.monitor_combo.clear()
        monitors = self._runtime.list_monitors()
        if not monitors:
            self.monitor_combo.addItem("0: monitor principal")
            return
        for monitor in monitors:
            self.monitor_combo.addItem(monitor.label)

    def _update_preview(self) -> None:
        self._refresh_overlay(throttle_s=0.5)
        frame = self._runtime.latest_frame()
        stats = self._runtime.metrics()
        change_enabled = (
            self._enable_perception_tools
            and self.change_detection_enabled.isChecked()
            and self._change_processor is not None
        )
        if change_enabled:
            result = self._change_processor.process_buffer(self._runtime.buffer)
            self._latest_change = result or self._latest_change
        self._update_runtime_status()
        if frame is None:
            return

        data = frame.data
        if data.shape[2] == 4:
            image_format = self.QImage.Format.Format_BGRA8888
        else:
            image_format = self.QImage.Format.Format_RGB888
        bytes_per_line = data.strides[0]
        image = self.QImage(data.data, frame.width, frame.height, bytes_per_line, image_format).copy()
        pixmap = self.QPixmap.fromImage(image)
        if change_enabled and self._latest_change is not None:
            pixmap = self._draw_change_regions(pixmap, self._latest_change)
        scaled = pixmap.scaled(
            self.preview_label.size(),
            self.Qt.AspectRatioMode.KeepAspectRatio,
            self.Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _refresh_overlay(self, *_args, throttle_s: float = 0.0) -> None:
        if not self.overlay_enabled.isChecked() or not self._runtime.running:
            self._overlay.hide()
            return
        now = time.perf_counter()
        if throttle_s and now - self._last_overlay_update < throttle_s:
            return
        self._last_overlay_update = now
        rect = capture_rect_from_config(self._runtime.config, self._runtime.list_monitors())
        self._overlay.show_rect(rect)

    def _update_runtime_status(self) -> None:
        stats = self._runtime.metrics()
        resolution = "-"
        if stats.latest_width and stats.latest_height:
            resolution = f"{stats.latest_width}x{stats.latest_height}"
        latency = "-" if stats.capture_latency_ms is None else f"{stats.capture_latency_ms:.2f} ms"
        self.fps_value.setText(f"{stats.capture_fps:.1f}")
        self.resolution_value.setText(resolution)
        self.latency_value.setText(latency)
        self.drop_value.setText(str(stats.buffer_dropped_frames))
        self.frames_value.setText(str(stats.frames_captured))
        self.errors_value.setText(str(stats.backend_errors))
        if self._runtime.running and self._runtime.paused:
            state = "Extension pausada"
            self.extension_state.setProperty("tone", "paused")
        elif self._runtime.running:
            state = "Extension activa"
            self.extension_state.setProperty("tone", "active")
        else:
            state = "Extension local lista"
            self.extension_state.setProperty("tone", "idle")
        self.extension_state.setText(state)
        self.extension_state.style().unpolish(self.extension_state)
        self.extension_state.style().polish(self.extension_state)
        self._floating.set_status(
            running=self._runtime.running,
            paused=self._runtime.paused,
            fps=stats.capture_fps,
            resolution=resolution,
            latency_ms=stats.capture_latency_ms,
            dropped=stats.buffer_dropped_frames,
        )

    def _sync_ai_model(self, provider: str) -> None:
        if provider in ("openai", "anthropic"):
            self.ai_model.setText(default_model(provider))

    def _poll_ai_result(self) -> None:
        if self._ai_future is None or not self._ai_future.done():
            return
        self.ai_timer.stop()
        try:
            output = self._ai_future.result()
        except AIClientError as exc:
            output = f"IA error: {exc}"
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            output = f"IA error: {type(exc).__name__}: {exc}"
        self.ai_output.setText(output)
        self.ai_button.setEnabled(True)
        self._ai_future = None

    def _ai_system_prompt(self) -> str:
        stats = self._runtime.metrics()
        frame = self._runtime.latest_frame()
        resolution = "unknown"
        if stats.latest_width and stats.latest_height:
            resolution = f"{stats.latest_width}x{stats.latest_height}"
        frame_text = "no latest frame" if frame is None else f"latest frame #{frame.sequence}"
        return (
            "You are using RTDA through its local AI complement runtime. "
            "Use capture metrics as context, but do not claim visual details "
            "that are not present in the user prompt. "
            f"Capture backend={self._runtime.config.backend}, resolution={resolution}, "
            f"fps={stats.capture_fps:.2f}, latency_ms={stats.capture_latency_ms}, {frame_text}."
        )

    def _show_main_window(self) -> None:
        self.widget.showNormal()
        self.widget.raise_()
        self.widget.activateWindow()

    def _handle_close_event(self, event) -> None:
        if self._show_floating_control:
            self.widget.hide()
            event.ignore()
            return
        self._shutdown()
        event.accept()

    def _shutdown(self, *_args) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True
        for timer in (self.timer, self.ai_timer):
            try:
                timer.stop()
            except RuntimeError:
                pass
        try:
            self._runtime.stop_capture()
        except RuntimeError:
            pass
        try:
            self._overlay.hide()
            self._floating.shutdown()
        except RuntimeError:
            pass
        self._ai_executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _ask_ai_worker(config: AIClientConfig, prompt: str, system: str) -> str:
        response = AIClient(config).complete(prompt, system=system)
        return response.output_text

    @staticmethod
    def _coord_spin(default: int = 0):
        from PySide6.QtWidgets import QSpinBox

        spin = QSpinBox()
        spin.setRange(0, 16384)
        spin.setValue(default)
        return spin

    def _reset_perception_tools(self) -> None:
        self._latest_change = None
        self._change_processor = None
        self._uia_inspector = None
        if not self._enable_perception_tools:
            return

        from rtda.perception.change_detector import FrameChangeProcessor
        from rtda.perception.opencv_detector import OpenCVChangeDetector
        from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector

        self._change_processor = FrameChangeProcessor(OpenCVChangeDetector())
        self._uia_inspector = WindowsUIAutomationInspector(UIAConfig(max_depth=3, max_elements=120))

    def _draw_change_regions(self, pixmap, result: Any):
        if not result.regions:
            return pixmap
        overlay = pixmap.copy()
        painter = self.QPainter(overlay)
        pen = self.QPen(self.Qt.GlobalColor.red)
        pen.setWidth(2)
        painter.setPen(pen)
        for region in result.regions:
            bbox = region.bbox
            painter.drawRect(bbox.left, bbox.top, bbox.width, bbox.height)
        painter.end()
        return overlay

    def _apply_theme(self) -> None:
        self.widget.setStyleSheet(_DASHBOARD_STYLE)


_DASHBOARD_STYLE = """
QWidget#rtdaRoot {
    background: #080b10;
    color: #edf5ff;
    font-family: "Segoe UI";
    font-size: 12px;
}
QFrame#sidebar {
    background: #0b1018;
    border-right: 1px solid #1d2a3a;
}
QFrame#previewPanel {
    background: #05070b;
}
QFrame#heroPanel {
    background: #101723;
    border: 1px solid #26364c;
    border-radius: 8px;
    padding: 14px;
}
QFrame#sectionPanel {
    background: #0f1621;
    border: 1px solid #253247;
    border-radius: 8px;
}
QFrame#metricCard {
    background: #111a27;
    border: 1px solid #26374e;
    border-radius: 7px;
}
QLabel#appTitle {
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
}
QLabel#sectionTitle,
QLabel#panelTitle {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}
QLabel#fieldLabel,
QLabel#metricLabel,
QLabel#mutedText {
    color: #91a0b6;
}
QLabel#metricValue {
    color: #ffbd5d;
    font-size: 18px;
    font-weight: 800;
}
QLabel#stateChip {
    background: #172131;
    color: #aebbd0;
    border: 1px solid #2b3b52;
    border-radius: 6px;
    padding: 6px 9px;
}
QLabel#stateChip[tone="active"] {
    color: #4be3ff;
    border-color: #2baac2;
}
QLabel#stateChip[tone="paused"] {
    color: #ffbd5d;
    border-color: #b77828;
}
QLabel#previewSurface {
    background: #030507;
    color: #c9d6e6;
    border: 1px solid #26364c;
    border-radius: 8px;
}
QPushButton {
    background: #162033;
    color: #edf5ff;
    border: 1px solid #30435f;
    border-radius: 6px;
    min-height: 28px;
    padding: 6px 10px;
}
QPushButton:hover {
    border-color: #ffb547;
    background: #1d2a40;
}
QPushButton:pressed {
    background: #243754;
}
QPushButton:disabled {
    color: #5d6b7e;
    background: #111823;
    border-color: #1d2838;
}
QComboBox,
QLineEdit,
QSpinBox,
QTextEdit {
    background: #0a0f17;
    color: #eef5ff;
    border: 1px solid #2b3b52;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #2baac2;
}
QTextEdit {
    min-height: 82px;
}
QComboBox:focus,
QLineEdit:focus,
QSpinBox:focus,
QTextEdit:focus {
    border-color: #4be3ff;
}
QCheckBox {
    color: #d8e4f3;
    spacing: 7px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #40526b;
    background: #0a0f17;
}
QCheckBox::indicator:checked {
    background: #ffb547;
    border-color: #ffce79;
}
"""
