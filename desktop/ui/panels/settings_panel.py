from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk


class SettingsPanel(ctk.CTkFrame):
    """Panel tab for system settings (overlay, floating control, change detection)."""

    def __init__(
        self,
        master,
        *,
        on_toggle_overlay: Callable[[], None] | None = None,
        on_toggle_floating: Callable[[], None] | None = None,
        show_capture_overlay: bool = True,
        show_floating_control: bool = True,
        enable_perception_tools: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        lbl = ctk.CTkLabel(
            self,
            text="⚙️ Opciones del Sistema",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC",
        )
        lbl.pack(anchor="w", pady=(0, 6))

        self.chk_overlay = ctk.CTkCheckBox(
            self,
            text="Marco de Captura Verde (Overlay)",
            command=on_toggle_overlay,
        )
        if show_capture_overlay:
            self.chk_overlay.select()
        self.chk_overlay.pack(anchor="w", pady=6)

        self.chk_floating = ctk.CTkCheckBox(
            self,
            text="Widget Flotante (Always-on-Top)",
            command=on_toggle_floating,
        )
        if show_floating_control:
            self.chk_floating.select()
        self.chk_floating.pack(anchor="w", pady=6)

        self.chk_changes = ctk.CTkCheckBox(
            self,
            text="Detección de Cambios (OpenCV ROI)",
        )
        if enable_perception_tools:
            self.chk_changes.select()
        self.chk_changes.pack(anchor="w", pady=6)
