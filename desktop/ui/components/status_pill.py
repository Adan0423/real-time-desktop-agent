from __future__ import annotations

import customtkinter as ctk


class StatusPill(ctk.CTkLabel):
    """Reusable status indicator badge component."""

    def __init__(self, master, text: str = "● Extension Local Lista", **kwargs) -> None:
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
            fg_color="#0F172A",
            corner_radius=10,
            height=28,
            **kwargs,
        )
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        if state == "active":
            self.configure(
                text="● Extension Activa",
                fg_color="#065F46",
                text_color="#34D399",
            )
        elif state == "paused":
            self.configure(
                text="● Extension Pausada",
                fg_color="#451A03",
                text_color="#FBBF24",
            )
        elif state == "error":
            self.configure(
                text="⚠️ Error de Runtime",
                fg_color="#450A0A",
                text_color="#F87171",
            )
        else:
            self.configure(
                text="● Extension Local Lista",
                fg_color="#0F172A",
                text_color="#94A3B8",
            )
