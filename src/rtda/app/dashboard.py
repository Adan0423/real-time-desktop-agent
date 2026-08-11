from __future__ import annotations

"""Backward-compatible import for the independent desktop dashboard.

The desktop UI lives in the repository-level `desktop` package. Keep this module
as a thin shim so older imports do not break while the architecture stays
clearly separated.
"""

from desktop.dashboard import CaptureDashboard

__all__ = ["CaptureDashboard"]
