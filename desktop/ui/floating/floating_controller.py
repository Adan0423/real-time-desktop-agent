from __future__ import annotations

from collections.abc import Callable

from desktop.ui.floating.floating_widget import FloatingWidget


class RTDAFloatingControl:
    """Always-on-top compact dual-mode control surface for the RTDA runtime."""

    def __init__(
        self,
        *,
        on_open: Callable[[], None],
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_quit: Callable[[], None],
        on_screenshot: Callable[[], None] | None = None,
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        from desktop.overlay.qt import get_or_create_qapp

        get_or_create_qapp()

        self.widget = FloatingWidget(
            on_open=on_open,
            on_start=on_start,
            on_pause=on_pause,
            on_stop=on_stop,
            on_quit=on_quit,
            on_screenshot=on_screenshot,
            on_settings=on_settings,
        )
        self.widget.setWindowTitle("RTDA")

    @property
    def status(self):
        return self.widget.collapsed_status

    @property
    def metrics(self):
        return self.widget.exp_metrics

    @property
    def run_button(self):
        return self.widget.start_btn

    @property
    def pause_button(self):
        return self.widget.pause_btn

    @property
    def stop_button(self):
        return self.widget.stop_btn

    def show(self) -> None:
        self.widget.show()
        self.widget.raise_()
        try:
            from desktop.native import apply_windows_11_theme
            apply_windows_11_theme(int(self.widget.winId()), dark_mode=True, rounded_corners=True)
        except Exception:
            pass

    def hide(self) -> None:
        self.widget.hide()

    def shutdown(self) -> None:
        self.widget.hide()

    def set_status(
        self,
        *,
        running: bool,
        paused: bool,
        fps: float,
        resolution: str,
        latency_ms: float | None,
        dropped: int,
    ) -> None:
        self.widget.set_status(
            running=running,
            paused=paused,
            fps=fps,
            resolution=resolution,
            latency_ms=latency_ms,
            dropped=dropped,
        )
