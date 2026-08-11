from __future__ import annotations

import os

import pytest


def test_floating_control_status_and_visibility() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")

    from rtda.desktop.floating import RTDAFloatingControl

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

    assert "Active" in control.status.text()
    assert "59.8 FPS" in control.metrics.text()
    assert control.run_button.isEnabled() is False
    assert control.pause_button.isEnabled() is True
    assert control.stop_button.isEnabled() is True

    control.show()
    app.processEvents()
    assert control.widget.isVisible() is True

    control.hide()
    app.processEvents()
    assert control.widget.isVisible() is False

    control.timer.stop()
    control.widget.deleteLater()
    app.processEvents()
