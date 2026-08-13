from __future__ import annotations

import customtkinter as ctk


class CapturePanel(ctk.CTkFrame):
    """Panel tab for Monitor selection and Capture FPS configuration."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            self,
            text="📷 Configuración de Captura",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC",
        )
        lbl.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self, text="Monitor Objetivo:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.opt_monitor = ctk.CTkOptionMenu(
            self,
            values=["Monitor 0 (Principal)"],
            fg_color="#1E293B",
            button_color="#0F172A",
        )
        self.opt_monitor.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(self, text="Tasa de Frames (FPS):", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.opt_fps = ctk.CTkOptionMenu(
            self,
            values=["60 FPS (Baja Latencia)", "30 FPS", "15 FPS"],
            fg_color="#1E293B",
            button_color="#0F172A",
        )
        self.opt_fps.pack(fill="x", pady=(2, 10))

    def set_monitors(self, monitors) -> None:
        if monitors:
            items = [f"Monitor {m.index} ({m.width}x{m.height})" for m in monitors]
            self.opt_monitor.configure(values=items)
            self.opt_monitor.set(items[0])
