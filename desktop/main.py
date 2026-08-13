from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)


def load_dotenv_if_present() -> None:
    """Load key-value pairs from .env if present in root or working directory."""
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and v and k not in os.environ:
                        os.environ[k] = v
                break
            except Exception:
                pass


load_dotenv_if_present()

from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RTDA Desktop Control Surface")
    parser.add_argument("--backend", choices=["dxgi", "wgc"], default="dxgi")
    parser.add_argument("--target-fps", type=int, default=60)
    parser.add_argument("--max-buffer-size", type=int, default=2)
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
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the Web Dashboard Control Surface from desktop/web in your browser.",
    )
    return parser



def config_from_args(args: argparse.Namespace) -> CaptureConfig:
    region = Region(*args.region) if args.region else None
    backend = "wgc" if args.window_title else args.backend
    return CaptureConfig(
        backend=backend,
        target_fps=args.target_fps,
        max_buffer_size=args.max_buffer_size,
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
    # Prevent Windows Qt DPI awareness conflict warning
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.window.warning=false")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    # Set explicit AppUserModelID so Windows Taskbar displays the app icon
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Adan0423.RTDA.DesktopAgent.v3")
        except Exception:
            pass

    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "Missing optional dependency 'PySide6'. "
            "Install with: python -m pip install -e .[gui]"
        ) from exc

    from desktop.dashboard import CaptureDashboard

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(not show_floating_control)

    icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    dashboard = CaptureDashboard(
        config or CaptureConfig(),
        enable_perception_tools=enable_perception_tools,
        show_capture_overlay=show_capture_overlay,
        show_floating_control=show_floating_control,
    )
    dashboard.show()
    return app.exec()


def run_web_ui() -> int:
    import webbrowser
    from pathlib import Path
    try:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        from rtda.service.gateway import create_service_app
    except ImportError as exc:
        raise RuntimeError("FastAPI y uvicorn son necesarios para el modo web. Instálalos con: uv pip install fastapi uvicorn") from exc

    app = create_service_app()
    web_dir = Path(__file__).parent / "web"
    if web_dir.exists():
        app.mount("/app", StaticFiles(directory=str(web_dir), html=True), name="web_app")

    url = "http://localhost:8000/app/"
    print(f"🌐 Iniciando Servidor Web RTDA en {url} ...")
    webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=8000)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.web:
        return run_web_ui()
    config = config_from_args(args)
    return run_gui(
        config,
        enable_perception_tools=args.enable_perception_tools,
        show_capture_overlay=not args.hide_overlay,
        show_floating_control=not args.hide_floating,
    )


if __name__ == "__main__":
    raise SystemExit(main())

