from __future__ import annotations

from desktop.ai.client import AIClientError
from rtda.capture.interface import CaptureConfig

from desktop.ai_bridge import AIRequestRunner, build_ai_system_prompt
from desktop.floating import RTDAFloatingControl
from desktop.runtime_bridge import DesktopRuntimeBridge
from desktop.theme import DASHBOARD_STYLE
from desktop.ui import ControlSidebar, PreviewPanel


class CaptureDashboard:
    """Desktop-only control surface that consumes the RTDA complement runtime."""

    def __init__(
        self,
        config: CaptureConfig | None = None,
        *,
        enable_perception_tools: bool = False,
        show_capture_overlay: bool = True,
        show_floating_control: bool = True,
    ) -> None:
        try:
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QHBoxLayout, QWidget
        except ImportError as exc:
            raise RuntimeError(
                "Missing optional dependency 'PySide6'. "
                "Install with: python -m pip install -e .[gui]"
            ) from exc

        self._config = config or CaptureConfig()
        self._show_floating_control = show_floating_control
        self._shutdown_started = False
        self._bridge = DesktopRuntimeBridge(self._config, enable_perception_tools=enable_perception_tools)
        self._runtime = self._bridge.runtime
        self._ai_runner = AIRequestRunner()

        class DashboardWindow(QWidget):
            def __init__(self, dashboard: "CaptureDashboard") -> None:
                super().__init__()
                self._dashboard = dashboard

            def closeEvent(self, event) -> None:
                self._dashboard._handle_close_event(event)

        from pathlib import Path
        from PySide6.QtGui import QIcon

        self.widget = DashboardWindow(self)
        self.widget.setObjectName("rtdaRoot")
        self.widget.setWindowTitle("🌟 RTDA Desktop Control Surface")
        self.widget.resize(1060, 660)

        icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
        if icon_path.exists():
            self.widget.setWindowIcon(QIcon(str(icon_path)))

        self.sidebar = ControlSidebar(
            config=self._config,
            enable_perception_tools=enable_perception_tools,
            show_capture_overlay=show_capture_overlay,
            show_floating_control=show_floating_control,
        )
        self.preview = PreviewPanel()
        self.preview_label = self.preview.surface
        self._enable_perception_tools = enable_perception_tools

        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.sidebar.widget)
        root.addWidget(self.preview.widget, 1)
        self.widget.setLayout(root)
        self.widget.setStyleSheet(DASHBOARD_STYLE)

        self._floating = RTDAFloatingControl(
            on_open=self._show_main_window,
            on_start=self.start,
            on_pause=self.pause_or_resume,
            on_stop=self.stop,
            on_quit=self.quit,
        )

        self.timer = QTimer()
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._update_preview)
        self.ai_timer = QTimer()
        self.ai_timer.setInterval(100)
        self.ai_timer.timeout.connect(self._poll_ai_result)

        self._connect_signals()
        self._setup_shortcuts()
        self._load_monitors()
        self._update_runtime_status()

    def _setup_shortcuts(self) -> None:
        from PySide6.QtGui import QKeySequence, QShortcut

        QShortcut(QKeySequence("F5"), self.widget, self.start)

        QShortcut(QKeySequence("Shift+F5"), self.widget, self.stop)
        QShortcut(QKeySequence("Ctrl+1"), self.widget, lambda: self.sidebar.set_page(0))
        QShortcut(QKeySequence("Ctrl+2"), self.widget, lambda: self.sidebar.set_page(1))
        QShortcut(QKeySequence("Ctrl+3"), self.widget, lambda: self.sidebar.set_page(2))
        QShortcut(QKeySequence("Ctrl+4"), self.widget, lambda: self.sidebar.set_page(3))
        QShortcut(QKeySequence("Ctrl+5"), self.widget, lambda: self.sidebar.set_page(4))


    def show(self) -> None:
        self.widget.show()
        try:
            from desktop.native import apply_windows_11_theme, enable_mica_effect
            hwnd = int(self.widget.winId())
            apply_windows_11_theme(hwnd, dark_mode=True, rounded_corners=True)
            enable_mica_effect(hwnd)
        except Exception:
            pass

        if self._show_floating_control:
            self._floating.show()


    def quit(self) -> None:
        self.stop()
        self._shutdown()
        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()

    def start(self) -> None:
        self.stop()
        selected = self.sidebar.target.selection()
        self._bridge.start(
            base_config=self._config,
            backend=selected.backend,
            target_fps=selected.target_fps,
            monitor_index=selected.monitor_index,
            window_title=selected.window_title,
            region=selected.region,
            show_border=self.sidebar.settings.show_border(),
        )
        self._config = self._bridge.config
        self.timer.start()
        self._update_runtime_status()

    def stop(self) -> None:
        self.timer.stop()
        self._bridge.stop()
        self.preview.clear()
        self._update_runtime_status()

    def pause_or_resume(self) -> None:
        self._bridge.pause_or_resume()
        if self._bridge.running and not self._bridge.paused:
            self.timer.start()
        self._update_runtime_status()

    def inspect_uia(self) -> None:
        window_title = self.sidebar.target.window_title.text().strip() or None
        status = self._bridge.inspect_uia(window_title=window_title)
        if status:
            self.sidebar.runtime.set_uia_status(status)

    def ask_ai(self) -> None:
        if self._ai_runner.busy:
            return
        prompt = self.sidebar.ai.prompt_text()
        if not prompt:
            self.sidebar.ai.output.setText("IA: escribe un prompt primero")
            return
        stats = self._bridge.metrics()
        frame = self._bridge.latest_frame()
        system = build_ai_system_prompt(
            backend=self._bridge.config.backend,
            stats=stats,
            frame=frame,
        )
        self.sidebar.ai.set_busy(True)
        self._ai_runner.submit(self.sidebar.ai.request_config(), prompt, system, frame)
        self.ai_timer.start()

    def open_settings(self) -> None:
        from desktop.ui.settings_dialog import SettingsDialog

        dialog = SettingsDialog(
            self.widget,
            enable_perception_tools=self._enable_perception_tools,
            show_capture_overlay=self.sidebar.settings.show_border(),
            show_floating_control=self.sidebar.settings.floating_enabled.isChecked(),
        )

        # Sync checkboxes from active settings
        dialog.panel.border_enabled.setChecked(self.sidebar.settings.border_enabled.isChecked())
        dialog.panel.floating_enabled.setChecked(self.sidebar.settings.floating_enabled.isChecked())
        if self._enable_perception_tools:
            dialog.panel.detect_changes_cb.setChecked(self.sidebar.settings.detect_changes_cb.isChecked())

        # Connect signals
        dialog.panel.border_enabled.stateChanged.connect(self.sidebar.settings.border_enabled.setChecked)
        dialog.panel.floating_enabled.stateChanged.connect(self.sidebar.settings.floating_enabled.setChecked)
        if self._enable_perception_tools:
            dialog.panel.detect_changes_cb.stateChanged.connect(self.sidebar.settings.detect_changes_cb.setChecked)

        dialog.exec()

    def _connect_signals(self) -> None:
        self.sidebar.actions.start_button.clicked.connect(self.start)
        self.sidebar.actions.pause_button.clicked.connect(self.pause_or_resume)
        self.sidebar.actions.stop_button.clicked.connect(self.stop)
        self.sidebar.actions.uia_button.clicked.connect(self.inspect_uia)
        self.sidebar.settings_button.clicked.connect(self.open_settings)
        self.sidebar.settings.border_enabled.stateChanged.connect(self._refresh_overlay)
        self.sidebar.settings.floating_enabled.stateChanged.connect(self._set_floating_visible)
        self.sidebar.ai.provider.currentTextChanged.connect(self.sidebar.ai.sync_model)
        self.sidebar.ai.ask_button.clicked.connect(self.ask_ai)
        self.widget.destroyed.connect(self._shutdown)

    def _load_monitors(self) -> None:
        self.sidebar.set_monitors(self._bridge.list_monitors())

    def _update_preview(self) -> None:
        self._refresh_overlay(throttle_s=0.5)
        change_enabled = (
            self._enable_perception_tools
            and self.sidebar.settings.detect_changes()
        )
        change = self._bridge.process_change_detection(change_enabled)
        self._update_runtime_status()
        frame = self._bridge.latest_frame()
        if frame is not None:
            self.preview.set_frame(frame, change_result=change if change_enabled else None)

    def _refresh_overlay(self, *_args, throttle_s: float = 0.0) -> None:
        self._bridge.refresh_overlay(self.sidebar.settings.show_border(), throttle_s=throttle_s)

    def _update_runtime_status(self) -> None:
        stats = self._bridge.metrics()
        resolution = self.sidebar.runtime.set_metrics(stats)
        self.sidebar.actions.set_running_state(running=self._bridge.running, paused=self._bridge.paused)
        self.sidebar.set_status(running=self._bridge.running, paused=self._bridge.paused)
        self.preview.set_summary(
            running=self._bridge.running,
            paused=self._bridge.paused,
            backend=self._bridge.config.backend,
            resolution=resolution,
        )
        self._floating.set_status(
            running=self._bridge.running,
            paused=self._bridge.paused,
            fps=stats.capture_fps,
            resolution=resolution,
            latency_ms=stats.capture_latency_ms,
            dropped=stats.buffer_dropped_frames,
        )

    def _set_floating_visible(self, *_args) -> None:
        if self.sidebar.settings.floating_enabled.isChecked():
            self._floating.show()
            return
        self._floating.hide()

    def _poll_ai_result(self) -> None:
        if self._ai_runner.busy:
            return
        self.ai_timer.stop()
        try:
            output = self._ai_runner.pop_result()
        except AIClientError as exc:
            output = f"IA error: {exc}"
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            output = f"IA error: {type(exc).__name__}: {exc}"
        if output is not None:
            self.sidebar.ai.output.setText(output)
        self.sidebar.ai.set_busy(False)

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
            self._bridge.shutdown()
        except RuntimeError:
            pass
        try:
            self._floating.shutdown()
        except RuntimeError:
            pass
        self._ai_runner.shutdown()
