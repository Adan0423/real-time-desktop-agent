from __future__ import annotations

import customtkinter as ctk

# Color Palette (Slate Dark + Emerald Accent)
THEME_PALETTE = {
    "background_app": "#080C14",
    "background_card": "#0F172A",
    "background_main": "#090D16",
    "background_input": "#020617",
    "border": "#1E293B",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "accent_emerald": "#10B981",
    "accent_emerald_hover": "#059669",
    "accent_emerald_dark": "#065F46",
    "accent_cyan": "#38BDF8",
    "accent_amber": "#F59E0B",
    "accent_amber_dark": "#78350F",
    "accent_red": "#EF4444",
    "accent_red_dark": "#7F1D1D",
    "accent_blue": "#0284C7",
    "accent_blue_hover": "#0369A1",
}


def apply_theme_settings() -> None:
    """Initialize CustomTkinter global appearance settings."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
