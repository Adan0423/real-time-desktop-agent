from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict

from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region
from rtda.capture.windows_capture import WindowsCaptureEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTDA Capture Engine")
    parser.add_argument("--backend", choices=["dxgi", "wgc"], default="dxgi")
    parser.add_argument("--target-fps", type=int, default=60)
    parser.add_argument("--monitor-index", type=int, default=0)
    parser.add_argument("--window-title", default=None)
    parser.add_argument("--region", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--duration", type=float, default=5.0)
    return parser


def _config_from_args(args: argparse.Namespace) -> CaptureConfig:
    region = Region(*args.region) if args.region else None
    backend = "wgc" if args.window_title else args.backend
    return CaptureConfig(
        backend=backend,
        target_fps=args.target_fps,
        monitor_index=args.monitor_index,
        region=region,
        window_title=args.window_title,
    )


def run_headless(config: CaptureConfig, duration: float) -> int:
    capture = WindowsCaptureEngine(config)
    try:
        capture.start()
        time.sleep(duration)
        print(json.dumps(asdict(capture.metrics()), indent=2, sort_keys=True))
    finally:
        capture.stop()
    return 0


def run_gui(config: CaptureConfig) -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "Missing optional dependency 'PySide6'. "
            "Install with: python -m pip install -e .[gui]"
        ) from exc

    from rtda.app.dashboard import CaptureDashboard

    app = QApplication(sys.argv)
    dashboard = CaptureDashboard(config)
    dashboard.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = _config_from_args(args)
    if args.headless:
        return run_headless(config, args.duration)
    return run_gui(config)


if __name__ == "__main__":
    raise SystemExit(main())
