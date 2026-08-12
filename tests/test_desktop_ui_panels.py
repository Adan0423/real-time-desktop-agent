from __future__ import annotations

import os

import numpy as np
import pytest


def test_target_panel_returns_compact_capture_selection() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.panels import TargetPanel
    from rtda.capture.interface import CaptureConfig

    app = widgets.QApplication.instance() or widgets.QApplication([])
    panel = TargetPanel(config=CaptureConfig(target_fps=75))
    panel.set_monitors([])
    panel.region_enabled.setChecked(True)
    panel.left_spin.setValue(10)
    panel.top_spin.setValue(20)
    panel.right_spin.setValue(800)
    panel.bottom_spin.setValue(600)
    panel.window_title.setText("Calculator")

    selection = panel.selection()

    assert selection.backend == "wgc"
    assert selection.target_fps == 75
    assert selection.region is not None
    assert selection.region.to_tuple() == (10, 20, 800, 600)
    assert panel._region_container.isHidden() is False

    panel.widget.deleteLater()
    app.processEvents()


def test_ai_panel_syncs_provider_model() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.panels import AiPanel
    from rtda.ai.client import AI_PROVIDERS, default_model

    app = widgets.QApplication.instance() or widgets.QApplication([])
    panel = AiPanel()

    panel.sync_model("anthropic")

    assert panel.model.text().startswith("claude")
    assert panel.provider.count() == len(AI_PROVIDERS)

    panel.sync_model("openrouter")

    assert panel.model.text() == default_model("openrouter")

    panel.widget.deleteLater()
    app.processEvents()


def test_preview_panel_accepts_four_channel_frames() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.preview import PreviewPanel
    from rtda.capture.frame import Frame

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
    from rtda.capture.interface import CaptureConfig

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
    assert sidebar.page_buttons["settings"].isChecked() is True

    sidebar.widget.deleteLater()
    app.processEvents()
