from __future__ import annotations

"""Compatibility layer for the old `rtda.extension` import path."""

from rtda.complement.runtime import RTDAComplementConfig, RTDAComplementRuntime, RTDAObservation


class RTDAExtensionRuntime(RTDAComplementRuntime):
    """Backward-compatible alias for `RTDAComplementRuntime`."""


__all__ = ["RTDAComplementConfig", "RTDAComplementRuntime", "RTDAExtensionRuntime", "RTDAObservation"]
