from __future__ import annotations

import customtkinter as ctk

from desktop.ui.components.metric_tile import MetricTile


class MetricsPanel(ctk.CTkFrame):
    """Panel tab for live telemetry metrics."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure((0, 1), weight=1)

        self.tiles: dict[str, MetricTile] = {}
        metric_configs = [
            ("fps", "⚡ FPS"),
            ("resolution", "📐 Resolución"),
            ("latency", "⏱️ Latencia"),
            ("drops", "⚠️ Drops"),
            ("frames", "🎞️ Frames"),
            ("errors", "❌ Errores"),
        ]

        for idx, (key, title) in enumerate(metric_configs):
            tile = MetricTile(self, title=title)
            tile.grid(row=idx // 2, column=idx % 2, padx=4, pady=4, sticky="ew")
            self.tiles[key] = tile

    def update_metrics(
        self,
        *,
        fps: float,
        resolution: str,
        latency_ms: float | None,
        drops: int,
        frames: int,
        errors: int,
    ) -> None:
        self.tiles["fps"].set_value(f"{fps:.1f}")
        self.tiles["resolution"].set_value(resolution)
        self.tiles["latency"].set_value(f"{latency_ms:.1f} ms" if latency_ms else "-")
        self.tiles["drops"].set_value(str(drops))
        self.tiles["frames"].set_value(str(frames))
        self.tiles["errors"].set_value(str(errors))
