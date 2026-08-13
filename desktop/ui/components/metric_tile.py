from __future__ import annotations

import customtkinter as ctk


class MetricTile(ctk.CTkFrame):
    """Reusable metric tile component for telemetry stats."""

    def __init__(self, master, title: str, initial_value: str = "-", **kwargs) -> None:
        super().__init__(
            master,
            fg_color="#020617",
            corner_radius=8,
            border_color="#1E293B",
            border_width=1,
            **kwargs,
        )
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8",
        )
        self.title_label.pack(anchor="w", padx=8, pady=(4, 0))

        self.value_label = ctk.CTkLabel(
            self,
            text=initial_value,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38BDF8",
        )
        self.value_label.pack(anchor="w", padx=8, pady=(0, 4))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)
