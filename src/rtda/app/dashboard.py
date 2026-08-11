from __future__ import annotations

"""Backward-compatible import for the desktop dashboard.

The desktop UI lives in `rtda.desktop`. Keep this module as a thin shim so
older imports do not break while the architecture stays clearly separated.
"""

from rtda.desktop.dashboard import CaptureDashboard

__all__ = ["CaptureDashboard"]
