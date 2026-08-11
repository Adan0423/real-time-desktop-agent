"""Desktop-only UI components that consume the RTDA complement runtime."""

__all__ = ["CaptureDashboard", "RTDAFloatingControl"]


def __getattr__(name: str):
    if name == "CaptureDashboard":
        from rtda.desktop.dashboard import CaptureDashboard

        return CaptureDashboard
    if name == "RTDAFloatingControl":
        from rtda.desktop.floating import RTDAFloatingControl

        return RTDAFloatingControl
    raise AttributeError(name)
