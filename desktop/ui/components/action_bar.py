from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk


class ActionBar(ctk.CTkFrame):
    """Reusable 2x2 Action Bar component for Start, Pause, Stop, UIA buttons."""

    def __init__(
        self,
        master,
        *,
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_uia: Callable[[], None],
        enable_perception_tools: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color="#020617",
            corner_radius=12,
            border_color="#1E293B",
            border_width=1,
            **kwargs,
        )
        self.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(
            self,
            text="▶ Iniciar",
            command=on_start,
            fg_color="#065F46",
            hover_color="#047857",
            text_color="#ECFDF5",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
        )
        self.btn_start.grid(row=0, column=0, padx=3, pady=3, sticky="ew")

        self.btn_pause = ctk.CTkButton(
            self,
            text="⏸ Pausar",
            command=on_pause,
            state="disabled",
            fg_color="#78350F",
            hover_color="#92400E",
            text_color="#FFFBEB",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
        )
        self.btn_pause.grid(row=0, column=1, padx=3, pady=3, sticky="ew")

        self.btn_stop = ctk.CTkButton(
            self,
            text="⏹ Detener",
            command=on_stop,
            state="disabled",
            fg_color="#7F1D1D",
            hover_color="#991B1B",
            text_color="#FEF2F2",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
        )
        self.btn_stop.grid(row=1, column=0, padx=3, pady=3, sticky="ew")

        self.btn_uia = ctk.CTkButton(
            self,
            text="🔍 UIA",
            command=on_uia,
            state="normal" if enable_perception_tools else "disabled",
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#F0F9FF",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
        )
        self.btn_uia.grid(row=1, column=1, padx=3, pady=3, sticky="ew")

    def set_running_state(self, *, running: bool, paused: bool) -> None:
        if running and paused:
            self.btn_start.configure(state="disabled")
            self.btn_pause.configure(state="normal", text="▶ Reanudar")
            self.btn_stop.configure(state="normal")
        elif running:
            self.btn_start.configure(state="disabled")
            self.btn_pause.configure(state="normal", text="⏸ Pausar")
            self.btn_stop.configure(state="normal")
        else:
            self.btn_start.configure(state="normal")
            self.btn_pause.configure(state="disabled", text="⏸ Pausar")
            self.btn_stop.configure(state="disabled")
