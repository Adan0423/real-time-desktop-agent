from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import numpy as np
import pytest

from desktop.ai_bridge import build_ai_system_prompt, frame_to_jpeg_data_url
from desktop.ai.client import AI_PROVIDERS, AIClient, AIClientConfig, AIClientError, default_model
from desktop.overlay.geometry import OverlayRect, capture_rect_from_config
from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo
from rtda.complement import runtime as runtime_module
from rtda.complement import RTDAComplementConfig, RTDAComplementRuntime
from rtda.extension import RTDAExtensionRuntime
from rtda.models.actions import ActionStatus
from rtda.models.perception import BoundingBox
from rtda.performance.metrics import CaptureMetrics, ProcessingMetrics

ROOT = Path(__file__).resolve().parents[1]


# ── AI Client & Bridge Tests ────────────────────────────────────────────────

def test_openai_client_posts_responses_payload(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append((url, headers, payload, timeout_s))
        return {"output_text": "ok"}

    response = AIClient(
        AIClientConfig(provider="openai", api_key="secret", model="gpt-test"),
        transport=transport,
    ).complete("hello", system="system")

    url, headers, payload, timeout_s = calls[0]
    assert response.output_text == "ok"
    assert url == "https://api.openai.com/v1/responses"
    assert headers["Authorization"] == "Bearer secret"
    assert payload["model"] == "gpt-test"
    assert payload["input"] == "hello"


def test_ai_client_uses_custom_base_url_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_BASE_URL", "http://localhost:8080/v1")
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append((url, headers, payload, timeout_s))
        return {"choices": [{"message": {"content": "ok"}}]}

    response = AIClient(
        AIClientConfig(provider="groq", api_key="secret"),
        transport=transport,
    ).complete("test prompt")

    url, _, _, _ = calls[0]
    assert url == "http://localhost:8080/v1/chat/completions"
    assert response.output_text == "ok"


def test_dynamic_custom_openai_compatible_provider(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test")
    calls = []

    def transport(url, headers, payload, timeout_s):
        calls.append((url, headers, payload, timeout_s))
        return {"choices": [{"message": {"content": "deepseek response"}}]}

    response = AIClient(
        AIClientConfig(provider="deepseek"),
        transport=transport,
    ).complete("hello deepseek")

    url, headers, _, _ = calls[0]
    assert url == "https://api.deepseek.com/v1/chat/completions"
    assert headers["Authorization"] == "Bearer sk-deepseek-test"
    assert response.output_text == "deepseek response"


def test_frame_to_jpeg_data_url_encodes_frame_in_memory() -> None:
    data = np.zeros((4, 6, 4), dtype=np.uint8)
    data[..., 0] = 255
    data[..., 3] = 255
    frame = Frame(timestamp=1.0, width=6, height=4, data=data, sequence=1)

    data_url = frame_to_jpeg_data_url(frame, max_side=4, quality=70)
    prefix, encoded = data_url.split(",", 1)

    assert prefix == "data:image/jpeg;base64"
    assert base64.b64decode(encoded).startswith(b"\xff\xd8")


def test_system_prompt_describes_live_state_without_history() -> None:
    prompt = build_ai_system_prompt(
        backend="dxgi",
        stats=CaptureStats(
            capture_fps=20.0,
            capture_latency_ms=4.0,
            frames_captured=10,
            buffer_dropped_frames=0,
            estimated_missed_frames=0,
            backend_errors=0,
            uptime_s=1.0,
            latest_width=1920,
            latest_height=1080,
        ),
        frame=None,
    )

    assert "real-time desktop observation and control runtime" in prompt
    assert "not saved history" in prompt
    assert "no live visual observation available" in prompt


# ── Desktop UI Panels & Widgets Tests ───────────────────────────────────────

def test_target_panel_returns_compact_capture_selection() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.panels import TargetPanel

    app = widgets.QApplication.instance() or widgets.QApplication([])
    panel = TargetPanel(config=CaptureConfig(target_fps=75))
    panel.set_monitors([])
    panel.region_enabled.setChecked(True)
    panel.left_spin.setValue(10)
    panel.top_spin.setValue(20)
    panel.right_spin.setValue(800)
    panel.bottom_spin.setValue(600)

    selection = panel.selection()

    assert selection.target_fps == 75
    assert selection.region is not None
    assert selection.region.to_tuple() == (10, 20, 800, 600)

    panel.widget.deleteLater()
    app.processEvents()


def test_ai_panel_syncs_provider_model() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.panels import AiPanel

    app = widgets.QApplication.instance() or widgets.QApplication([])
    panel = AiPanel()

    panel.sync_model("anthropic")
    assert panel.model.text().startswith("claude")
    assert panel.provider.count() == len(AI_PROVIDERS)

    panel.sync_model("openrouter")
    assert panel.model.text() == default_model("openrouter")

    panel.sync_model("tokenrouter")
    assert panel.model.text() == default_model("tokenrouter")
    assert "TOKENROUTER_API_KEY" in panel.token.placeholderText()

    panel.provider.setCurrentText("tokenrouter")
    assert panel.request_config().timeout_s == 90.0

    panel.widget.deleteLater()
    app.processEvents()


def test_preview_panel_accepts_four_channel_frames() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.preview import PreviewPanel

    app = widgets.QApplication.instance() or widgets.QApplication([])
    panel = PreviewPanel()
    data = np.zeros((2, 3, 4), dtype=np.uint8)
    data[..., 3] = 255
    frame = Frame(timestamp=0.0, width=3, height=2, data=data)

    panel.set_frame(frame)
    assert panel.surface.pixmap() is not None

    panel.widget.deleteLater()
    app.processEvents()


def test_sidebar_uses_pages_instead_of_single_dense_column() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.sidebar import ControlSidebar

    app = widgets.QApplication.instance() or widgets.QApplication([])
    sidebar = ControlSidebar(
        config=CaptureConfig(),
        enable_perception_tools=True,
        show_capture_overlay=True,
        show_floating_control=True,
    )

    assert sidebar.pages.count() == 4
    sidebar.set_page(3)
    assert sidebar.pages.currentIndex() == 3
    assert sidebar.page_buttons["ai"].isChecked() is True
    assert sidebar.settings_button is not None

    sidebar.widget.deleteLater()
    app.processEvents()


def test_floating_control_status_and_visibility() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.floating import RTDAFloatingControl

    app = widgets.QApplication.instance() or widgets.QApplication([])
    events: list[str] = []
    control = RTDAFloatingControl(
        on_open=lambda: events.append("open"),
        on_start=lambda: events.append("start"),
        on_pause=lambda: events.append("pause"),
        on_stop=lambda: events.append("stop"),
        on_quit=lambda: events.append("quit"),
    )

    control.set_status(
        running=True,
        paused=False,
        fps=59.8,
        resolution="1920x1080",
        latency_ms=4.2,
        dropped=1,
    )

    assert any(word in control.status.text() for word in ("Active", "Activo"))
    assert "59.8 FPS" in control.metrics.text()
    assert control.run_button.isEnabled() is False
    assert control.pause_button.isEnabled() is True
    assert control.stop_button.isEnabled() is True

    control.show()
    app.processEvents()
    control.widget.deleteLater()


# ── Overlay Geometry Tests ──────────────────────────────────────────────────

def test_capture_rect_uses_monitor_bounds() -> None:
    monitors = [MonitorInfo(0, 1, 10, 20, 210, 120, True, "DISPLAY1")]
    rect = capture_rect_from_config(CaptureConfig(monitor_index=0), monitors)

    assert rect == OverlayRect(10, 20, 210, 120)


def test_capture_rect_uses_window_resolver_for_window_capture() -> None:
    rect = capture_rect_from_config(
        CaptureConfig(backend="wgc", window_title="ChatGPT"),
        [],
        window_resolver=lambda title: OverlayRect(1, 2, 3, 4) if title == "ChatGPT" else None,
    )

    assert rect == OverlayRect(1, 2, 3, 4)


# ── Performance Metrics Tests ───────────────────────────────────────────────

def test_metrics_records_fps_and_drops() -> None:
    metrics = CaptureMetrics(target_fps=10, window_s=10)
    metrics.reset()
    metrics.record_frame(timestamp=1.0, latency_ms=2.0, width=100, height=50)
    metrics.record_frame(timestamp=1.1, latency_ms=3.0, width=100, height=50, buffer_dropped=1)
    snapshot = metrics.snapshot()

    assert snapshot.capture_fps > 0
    assert snapshot.capture_latency_ms == 3.0
    assert snapshot.frames_captured == 2
    assert snapshot.buffer_dropped_frames == 1


def test_processing_metrics_records_change_detection() -> None:
    metrics = ProcessingMetrics(window_s=10)
    metrics.reset()

    metrics.record_change_detection(
        timestamp=1.0,
        opencv_latency_ms=4.5,
        changed=True,
        region_count=2,
        changed_ratio=0.1,
    )
    metrics.record_change_detection(
        timestamp=1.1,
        opencv_latency_ms=4.5,
        changed=True,
        region_count=2,
        changed_ratio=0.1,
    )
    snapshot = metrics.snapshot()

    assert snapshot.processing_fps > 0
    assert snapshot.opencv_latency_ms == 4.5
    assert snapshot.frames_processed == 2


# ── Extension Runtime & Plugin Metadata Tests ───────────────────────────────

class FakeCaptureEngine:
    instances: list["FakeCaptureEngine"] = []

    def __init__(self, config: CaptureConfig | None = None) -> None:
        self.config = config or CaptureConfig()
        self.buffer = FrameBuffer(max_size=self.config.max_buffer_size)
        self.started = False
        self.stopped = False
        self.paused = False
        self.latest = Frame(
            timestamp=10.0,
            source_timestamp=9.995,
            width=32,
            height=32,
            data=np.zeros((32, 32, 4), dtype=np.uint8),
            sequence=1,
        )
        self.buffer.push(self.latest)
        FakeCaptureEngine.instances.append(self)

    def list_monitors(self) -> list[MonitorInfo]:
        return [
            MonitorInfo(
                index=0,
                handle=100,
                left=0,
                top=0,
                right=1920,
                bottom=1080,
                primary=True,
                device_name="DISPLAY1",
            )
        ]

    def start(self) -> None:
        self.started = True
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True
        self.started = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def latest_frame(self) -> Frame | None:
        return self.latest

    def metrics(self) -> CaptureStats:
        return CaptureStats(
            capture_fps=60.0 if self.started else 0.0,
            capture_latency_ms=5.0,
            frames_captured=1,
            buffer_dropped_frames=0,
            estimated_missed_frames=0,
            backend_errors=0,
            uptime_s=1.0,
            latest_width=2,
            latest_height=2,
        )


def test_complement_runtime_wraps_capture_lifecycle(monkeypatch) -> None:
    FakeCaptureEngine.instances = []
    monkeypatch.setattr(runtime_module, "WindowsCaptureEngine", FakeCaptureEngine)

    runtime = runtime_module.RTDAComplementRuntime(CaptureConfig(target_fps=30))
    runtime.start_capture(CaptureConfig(target_fps=60, max_buffer_size=4))

    assert runtime.running is True
    assert FakeCaptureEngine.instances[-1].started is True
    assert runtime.metrics().capture_fps == 60.0

    runtime.stop_capture()
    assert runtime.running is False


def test_extension_runtime_import_path_remains_compatible() -> None:
    assert issubclass(RTDAExtensionRuntime, RTDAComplementRuntime)


def test_openai_plugin_manifest_points_to_mcp_config() -> None:
    manifest_path = ROOT / "plugins" / "real-time-desktop-agent" / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["name"] == "real-time-desktop-agent"
    assert manifest["mcpServers"] == "./.mcp.json"


def test_openai_plugin_mcp_config_uses_rtda_server() -> None:
    config_path = ROOT / "plugins" / "real-time-desktop-agent" / ".mcp.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    server = config["real-time-desktop-agent"]

    assert any(cmd in server["command"].lower() for cmd in ("python", "uv"))
    assert "rtda.mcp.server" in server["args"]
