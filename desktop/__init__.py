"""Desktop-only UI components that consume the RTDA complement runtime."""

import sys
from pathlib import Path

_ROOT_DIR = str(Path(__file__).resolve().parent.parent)
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

__all__ = ["CaptureDashboard", "RTDAFloatingControl"]



def __getattr__(name: str):
    if name == "CaptureDashboard":
        from desktop.dashboard import CaptureDashboard

        return CaptureDashboard
    if name == "RTDAFloatingControl":
        from desktop.floating import RTDAFloatingControl

        return RTDAFloatingControl
    raise AttributeError(name)
