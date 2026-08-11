from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from typing import Any

from rtda.ai.client import AIClient, AIClientConfig, AIClientError, default_model
from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region
from rtda.capture.windows_capture import WindowsCaptureEngine
from rtda.overlay.geometry import capture_rect_from_config
from rtda.overlay.qt import GreenCaptureOverlay


class CaptureDashboard:
    def __init__(
        self,
        config: CaptureConfig | None = None,
        *,
        enable_perception_tools: bool = False,
        show_capture_overlay: bool = True,
    ) -> None:
        try:
            from PySide6.QtCore import Qt, QTimer
            from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
            from PySide6.QtWidgets import (
                QCheckBox,
                QComboBox,
                QFormLayout,
                QHBoxLayout,
                QLabel,
                QLineEdit,
                QPushButton,
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
        self.QImage = QImage
        self.QPainter = QPainter
        self.QPen = QPen
        self.QPixmap = QPixmap
        self.QTimer = QTimer
        self.QTextEdit = QTextEdit
        self.QWidget = QWidget

        self._config = config or CaptureConfig()
        self._enable_perception_tools = enable_perception_tools
        self._capture = WindowsCaptureEngine(self._config)
        self._overlay = GreenCaptureOverlay()
        self._last_overlay_update = 0.0
        self._ai_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rtda-ai")
        self._ai_future: Future[str] | None = None
        self._change_processor: Any | None = None
        self._uia_inspector: Any | None = None
        self._latest_change: Any | None = None
        self._reset_perception_tools()

        self.widget = QWidget()
        self.widget.setWindowTitle("RTDA Capture Engine")
        self.widget.resize(1120, 760)

        self.monitor_combo = QComboBox()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["dxgi", "wgc"])
        self.backend_combo.setCurrentText(self._config.backend)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(self._config.target_fps)
        self.window_title = QLineEdit()
        self.window_title.setPlaceholderText("Window title for WGC")
        self.region_enabled = QCheckBox()
        self.overlay_enabled = QCheckBox()
        self.overlay_enabled.setChecked(show_capture_overlay)
        self.change_detection_enabled = QCheckBox()
        self.change_detection_enabled.setChecked(False)
        self.left_spin = self._coord_spin()
        self.top_spin = self._coord_spin()
        self.right_spin = self._coord_spin(3840)
        self.bottom_spin = self._coord_spin(2160)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.uia_button = QPushButton("Inspect UIA")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.uia_button.setEnabled(self._enable_perception_tools)

        self.metrics_label = QLabel("Capture FPS: 0.0\nResolution: -\nLatency: -\nDropped: 0")
        self.uia_label = QLabel("UIA: not inspected")
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["openai", "anthropic"])
        self.ai_model = QLineEdit(default_model("openai"))
        self.ai_token = QLineEdit()
        self.ai_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_prompt = QTextEdit()
        self.ai_prompt.setMinimumHeight(90)
        self.ai_button = QPushButton("Ask AI")
        self.ai_output = QLabel("AI: idle")
        self.ai_output.setWordWrap(True)
        self.preview_label = QLabel("No frame")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(800, 520)
        self.preview_label.setStyleSheet("background:#111; color:#ddd; border:1px solid #333;")

        form = QFormLayout()
        form.addRow("Monitor", self.monitor_combo)
        form.addRow("Backend", self.backend_combo)
        form.addRow("Target FPS", self.fps_spin)
        form.addRow("Window", self.window_title)
        form.addRow("Use region", self.region_enabled)
        form.addRow("Green border", self.overlay_enabled)
        if self._enable_perception_tools:
            form.addRow("Change detect", self.change_detection_enabled)
        form.addRow("Left", self.left_spin)
        form.addRow("Top", self.top_spin)
        form.addRow("Right", self.right_spin)
        form.addRow("Bottom", self.bottom_spin)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.stop_button)
        if self._enable_perception_tools:
            buttons.addWidget(self.uia_button)

        side = QVBoxLayout()
        side.addLayout(form)
        side.addLayout(buttons)
        side.addWidget(self.metrics_label)
        if self._enable_perception_tools:
            side.addWidget(self.uia_label)
        ai_form = QFormLayout()
        ai_form.addRow("AI provider", self.ai_provider)
        ai_form.addRow("AI model", self.ai_model)
        ai_form.addRow("AI token", self.ai_token)
        ai_form.addRow("AI prompt", self.ai_prompt)
        ai_form.addRow(self.ai_button)
        side.addLayout(ai_form)
        side.addWidget(self.ai_output)
        side.addStretch(1)

        root = QHBoxLayout()
        root.addLayout(side, 0)
        root.addWidget(self.preview_label, 1)
        self.widget.setLayout(root)

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

    def show(self) -> None:
        self.widget.show()

    def _shutdown(self, *_args) -> None:
        self._overlay.hide()
        self._ai_executor.shutdown(wait=False, cancel_futures=True)

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
        self._capture = WindowsCaptureEngine(config)
        self._reset_perception_tools()
        self._capture.start()
        self.timer.start()
        self._refresh_overlay()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)

    def stop(self) -> None:
        self.timer.stop()
        self._capture.stop()
        self._overlay.hide()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("Pause")

    def pause_or_resume(self) -> None:
        if self.pause_button.text() == "Pause":
            self._capture.pause()
            self.pause_button.setText("Resume")
        else:
            self._capture.resume()
            self.pause_button.setText("Pause")

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
        error_text = f", errors: {len(snapshot.errors)}" if snapshot.errors else ""
        target = f" ({window_title})" if window_title else ""
        self.uia_label.setText(
            f"UIA{target}: {snapshot.element_count} elements, "
            f"{snapshot.latency_ms:.1f} ms{error_text}"
        )

    def ask_ai(self) -> None:
        if self._ai_future is not None and not self._ai_future.done():
            return
        prompt = self.ai_prompt.toPlainText().strip()
        if not prompt:
            self.ai_output.setText("AI: empty prompt")
            return
        provider = self.ai_provider.currentText()
        token = self.ai_token.text().strip() or None
        model = self.ai_model.text().strip() or None
        config = AIClientConfig(provider=provider, api_key=token, model=model)
        system = self._ai_system_prompt()
        self.ai_button.setEnabled(False)
        self.ai_output.setText("AI: working")
        self._ai_future = self._ai_executor.submit(self._ask_ai_worker, config, prompt, system)
        self.ai_timer.start()

    def _load_monitors(self) -> None:
        self.monitor_combo.clear()
        monitors = self._capture.list_monitors()
        if not monitors:
            self.monitor_combo.addItem("0: primary monitor")
            return
        for monitor in monitors:
            self.monitor_combo.addItem(monitor.label)

    def _update_preview(self) -> None:
        self._refresh_overlay(throttle_s=0.5)
        frame = self._capture.latest_frame()
        stats = self._capture.metrics()
        change_enabled = (
            self._enable_perception_tools
            and self.change_detection_enabled.isChecked()
            and self._change_processor is not None
        )
        if change_enabled:
            result = self._change_processor.process_buffer(self._capture.buffer)
            self._latest_change = result or self._latest_change
        resolution = "-"
        if stats.latest_width and stats.latest_height:
            resolution = f"{stats.latest_width}x{stats.latest_height}"
        latency = "-" if stats.capture_latency_ms is None else f"{stats.capture_latency_ms:.2f} ms"
        metric_lines = [
            f"Capture FPS: {stats.capture_fps:.1f}",
            f"Resolution: {resolution}",
            f"Latency: {latency}",
            f"Dropped: {stats.buffer_dropped_frames}",
            f"Missed est.: {stats.estimated_missed_frames}",
            f"Frames: {stats.frames_captured}",
            f"Errors: {stats.backend_errors}",
        ]
        if self._enable_perception_tools and self._change_processor is not None:
            processing_stats = self._change_processor.metrics.snapshot()
            metric_lines.extend(
                [
                    f"Processing FPS: {processing_stats.processing_fps:.1f}",
                    f"OpenCV Latency: {self._format_ms(processing_stats.opencv_latency_ms)}",
                    f"Changed regions: {processing_stats.latest_changed_regions}",
                    f"Changed ratio: {processing_stats.latest_changed_ratio:.4f}",
                ]
            )
        self.metrics_label.setText(
            "\n".join(metric_lines)
        )
        if frame is None:
            return
        data = frame.data
        if data.shape[2] == 4:
            image_format = self.QImage.Format.Format_BGRA8888
            bytes_per_line = data.strides[0]
            image = self.QImage(data.data, frame.width, frame.height, bytes_per_line, image_format).copy()
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
        if not self.overlay_enabled.isChecked():
            self._overlay.hide()
            return
        now = time.perf_counter()
        if throttle_s and now - self._last_overlay_update < throttle_s:
            return
        self._last_overlay_update = now
        rect = capture_rect_from_config(self._capture.config, self._capture.list_monitors())
        self._overlay.show_rect(rect)

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
            output = f"AI error: {exc}"
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            output = f"AI error: {type(exc).__name__}: {exc}"
        self.ai_output.setText(output)
        self.ai_button.setEnabled(True)
        self._ai_future = None

    def _ai_system_prompt(self) -> str:
        stats = self._capture.metrics()
        frame = self._capture.latest_frame()
        resolution = "unknown"
        if stats.latest_width and stats.latest_height:
            resolution = f"{stats.latest_width}x{stats.latest_height}"
        frame_text = "no latest frame" if frame is None else f"latest frame #{frame.sequence}"
        return (
            "You are RTDA standalone test assistant. "
            "Use the capture metrics as context, but do not claim visual details "
            "that are not present in the prompt. "
            f"Capture backend={self._capture.config.backend}, resolution={resolution}, "
            f"fps={stats.capture_fps:.2f}, latency_ms={stats.capture_latency_ms}, {frame_text}."
        )

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

    @staticmethod
    def _format_ms(value: float | None) -> str:
        return "-" if value is None else f"{value:.2f} ms"

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
