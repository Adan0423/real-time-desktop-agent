from __future__ import annotations

"""Compatibility exports for desktop UI panels."""

from desktop.ui.ai_panel import AiPanel
from desktop.ui.runtime_panel import ActionBar, RuntimePanel
from desktop.ui.sidebar import ControlSidebar
from desktop.ui.settings_panel import SettingsPanel
from desktop.ui.target_panel import TargetPanel, TargetSelection

__all__ = [
    "ActionBar",
    "AiPanel",
    "ControlSidebar",
    "RuntimePanel",
    "SettingsPanel",
    "TargetPanel",
    "TargetSelection",
]
