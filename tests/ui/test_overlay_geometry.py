from __future__ import annotations

from rtda.capture.interface import CaptureConfig, MonitorInfo
from rtda.capture.region import Region
from desktop.overlay.geometry import OverlayRect, capture_rect_from_config


def test_capture_rect_uses_monitor_bounds() -> None:
    monitors = [MonitorInfo(0, 1, 10, 20, 210, 120, True, "DISPLAY1")]

    rect = capture_rect_from_config(CaptureConfig(monitor_index=0), monitors)

    assert rect == OverlayRect(10, 20, 210, 120)


def test_capture_rect_offsets_region_by_monitor_origin() -> None:
    monitors = [MonitorInfo(0, 1, 100, 200, 500, 500, True, "DISPLAY1")]

    rect = capture_rect_from_config(
        CaptureConfig(monitor_index=0, region=Region(10, 20, 110, 120)),
        monitors,
    )

    assert rect == OverlayRect(110, 220, 210, 320)


def test_capture_rect_uses_window_resolver_for_window_capture() -> None:
    rect = capture_rect_from_config(
        CaptureConfig(backend="wgc", window_title="ChatGPT"),
        [],
        window_resolver=lambda title: OverlayRect(1, 2, 3, 4) if title == "ChatGPT" else None,
    )

    assert rect == OverlayRect(1, 2, 3, 4)
