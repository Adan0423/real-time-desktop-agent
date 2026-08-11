from __future__ import annotations

import os

import pytest


def test_target_panel_returns_compact_capture_selection() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from desktop.ui.panels import TargetPanel
    from rtda.capture.interface import CaptureConfig

    app = widgets.QApplication.instance() or widgets.QApplication([])
    panel = TargetPanel(
        config=CaptureConfig(target_fps=75),
        enable_perception_tools=True,
        show_capture_overlay=False,
    )
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
    assert selection.show_border is False

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

    panel.widget.deleteLater()
    app.processEvents()
