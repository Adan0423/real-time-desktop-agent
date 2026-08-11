from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict

from rtda.capture.diagnostics import monitors_to_dict, run_capture_diagnostic
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
    parser.add_argument("--list-monitors", action="store_true")
    parser.add_argument("--capture-diagnostic", action="store_true")
    parser.add_argument("--diagnostic-pause", type=float, default=0.25)
    parser.add_argument(
        "--enable-perception-tools",
        action="store_true",
        help="Enable later-phase OpenCV/UIA controls in the GUI. Disabled by default for Phase 1.",
    )
    parser.add_argument(
        "--hide-overlay",
        action="store_true",
        help="Hide the green capture-target overlay in GUI mode.",
    )
    parser.add_argument(
        "--hide-floating",
        action="store_true",
        help="Hide the always-on-top RTDA background control in GUI mode.",
    )
    parser.add_argument("--detect-changes", action="store_true")
    parser.add_argument("--inspect-uia", action="store_true")
    parser.add_argument("--uia-window-title", default=None)
    parser.add_argument("--uia-max-depth", type=int, default=4)
    parser.add_argument("--uia-max-elements", type=int, default=300)
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


def run_headless(
    config: CaptureConfig,
    duration: float,
    *,
    detect_changes: bool = False,
    inspect_uia: bool = False,
    uia_window_title: str | None = None,
    uia_max_depth: int = 4,
    uia_max_elements: int = 300,
) -> int:
    capture = WindowsCaptureEngine(config)
    processor = None
    if detect_changes:
        from rtda.perception.change_detector import FrameChangeProcessor
        from rtda.perception.opencv_detector import OpenCVChangeDetector

        processor = FrameChangeProcessor(OpenCVChangeDetector())

    uia_inspector = None
    summarize_uia_elements = None
    if inspect_uia:
        from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector, summarize_uia_elements

        uia_inspector = WindowsUIAutomationInspector(
            UIAConfig(max_depth=uia_max_depth, max_elements=uia_max_elements)
        )
    latest_result = None
    latest_uia = None
    try:
        if duration > 0:
            capture.start()
        deadline = time.perf_counter() + duration
        interval_s = 1.0 / config.target_fps
        while time.perf_counter() < deadline:
            if processor is not None:
                result = processor.process_buffer(capture.buffer)
                latest_result = result or latest_result
            time.sleep(interval_s)
        if uia_inspector is not None:
            latest_uia = uia_inspector.snapshot(window_title=uia_window_title)
            if processor is not None:
                processor.metrics.record_uia_snapshot(
                    timestamp=time.perf_counter(),
                    uia_latency_ms=latest_uia.latency_ms,
                    element_count=latest_uia.element_count,
                )
        payload = {"capture": asdict(capture.metrics())}
        if processor is not None:
            payload["perception"] = asdict(processor.metrics.snapshot())
            if latest_result is not None:
                payload["latest_change"] = {
                    "changed": latest_result.changed,
                    "regions": latest_result.region_count,
                    "changed_ratio": latest_result.changed_ratio,
                    "latency_ms": latest_result.latency_ms,
                }
        if latest_uia is not None:
            payload["uia"] = {
                "element_count": latest_uia.element_count,
                "latency_ms": latest_uia.latency_ms,
                "truncated": latest_uia.truncated,
                "errors": latest_uia.errors,
                "elements": summarize_uia_elements(latest_uia.elements) if summarize_uia_elements else [],
            }
        print(json.dumps(payload, indent=2, sort_keys=True))
    finally:
        capture.stop()
    return 0


def run_gui(
    config: CaptureConfig,
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

    from rtda.app.dashboard import CaptureDashboard

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(not show_floating_control)
    dashboard = CaptureDashboard(
        config,
        enable_perception_tools=enable_perception_tools,
        show_capture_overlay=show_capture_overlay,
        show_floating_control=show_floating_control,
    )
    dashboard.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = _config_from_args(args)
    if args.list_monitors:
        capture = WindowsCaptureEngine(config)
        print(json.dumps({"monitors": monitors_to_dict(capture.list_monitors())}, indent=2, sort_keys=True))
        return 0
    if args.capture_diagnostic:
        capture = WindowsCaptureEngine(config)
        result = run_capture_diagnostic(
            capture,
            config=config,
            duration_s=args.duration,
            pause_s=args.diagnostic_pause,
        )
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0 if result.passed else 1
    if args.headless:
        return run_headless(
            config,
            args.duration,
            detect_changes=args.detect_changes,
            inspect_uia=args.inspect_uia,
            uia_window_title=args.uia_window_title,
            uia_max_depth=args.uia_max_depth,
            uia_max_elements=args.uia_max_elements,
        )
    return run_gui(
        config,
        enable_perception_tools=args.enable_perception_tools,
        show_capture_overlay=not args.hide_overlay,
        show_floating_control=not args.hide_floating,
    )


if __name__ == "__main__":
    raise SystemExit(main())
