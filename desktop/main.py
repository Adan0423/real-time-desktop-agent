from __future__ import annotations

import argparse
import sys

from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTDA Desktop Control Surface")
    parser.add_argument("--backend", choices=["dxgi", "wgc"], default="dxgi")
    parser.add_argument("--target-fps", type=int, default=60)
    parser.add_argument("--monitor-index", type=int, default=0)
    parser.add_argument("--window-title", default=None)
    parser.add_argument("--region", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument(
        "--enable-perception-tools",
        action="store_true",
        help="Enable later-phase OpenCV/UIA controls in the desktop app.",
    )
    parser.add_argument(
        "--hide-overlay",
        action="store_true",
        help="Hide the green capture-target overlay.",
    )
    parser.add_argument(
        "--hide-floating",
        action="store_true",
        help="Hide the always-on-top RTDA desktop control.",
    )
    return parser


def config_from_args(args: argparse.Namespace) -> CaptureConfig:
    region = Region(*args.region) if args.region else None
    backend = "wgc" if args.window_title else args.backend
    return CaptureConfig(
        backend=backend,
        target_fps=args.target_fps,
        monitor_index=args.monitor_index,
        region=region,
        window_title=args.window_title,
    )


def run_gui(
    config: CaptureConfig | None = None,
    *,
    enable_perception_tools: bool = False,
    show_capture_overlay: bool = True,
    show_floating_control: bool = True,
) -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "Missing optional dependency 'PySide6'. "
            "Install with: python -m pip install -e .[gui]"
        ) from exc

    from desktop.dashboard import CaptureDashboard

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(not show_floating_control)
    dashboard = CaptureDashboard(
        config or CaptureConfig(),
        enable_perception_tools=enable_perception_tools,
        show_capture_overlay=show_capture_overlay,
        show_floating_control=show_floating_control,
    )
    dashboard.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)
    return run_gui(
        config,
        enable_perception_tools=args.enable_perception_tools,
        show_capture_overlay=not args.hide_overlay,
        show_floating_control=not args.hide_floating,
    )


if __name__ == "__main__":
    raise SystemExit(main())
