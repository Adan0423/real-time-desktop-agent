from __future__ import annotations

import base64
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

from desktop.ai.client import AIClient, AIClientConfig
from rtda.capture.frame import Frame
from rtda.capture.interface import CaptureStats


@dataclass
class DesktopAiResult:
    text: str | None = None
    error: str | None = None


class AIRequestRunner:
    """Runs provider calls away from the main event loop."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rtda-ai")
        self._future: Future[str] | None = None

    @property
    def busy(self) -> bool:
        return self._future is not None and not self._future.done()

    def submit(self, config: AIClientConfig, prompt: str, system: str, frame: Frame | None) -> None:
        self._future = self._executor.submit(_complete, config, prompt, system, frame)

    def pop_result(self) -> str | None:
        if self._future is None or not self._future.done():
            return None
        future = self._future
        self._future = None
        return future.result()

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


class DesktopAiRunner:
    """Async AI runner wrapper for GUI integration."""

    def __init__(self) -> None:
        self._runner = AIRequestRunner()
        self._latest_result: DesktopAiResult | None = None

    @property
    def busy(self) -> bool:
        return self._runner.busy

    def submit(self, config: AIClientConfig, prompt: str, system: str, frame: Frame | None) -> None:
        self._latest_result = None
        self._runner.submit(config, prompt, system, frame)

    def has_result(self) -> bool:
        if self._latest_result is not None:
            return True
        try:
            res = self._runner.pop_result()
            if res is not None:
                self._latest_result = DesktopAiResult(text=res)
                return True
        except Exception as exc:
            self._latest_result = DesktopAiResult(error=str(exc))
            return True
        return False

    def take_result(self) -> DesktopAiResult:
        res = self._latest_result or DesktopAiResult(text="")
        self._latest_result = None
        return res

    def shutdown(self) -> None:
        self._runner.shutdown()


def build_ai_system_prompt(
    *,
    backend: str,
    stats: CaptureStats,
    frame: Frame | None,
) -> str:
    """Builds the compact runtime context passed to manual AI tests."""

    resolution = "unknown"
    if stats.latest_width and stats.latest_height:
        resolution = f"{stats.latest_width}x{stats.latest_height}"
    observation_text = "no live visual observation available" if frame is None else "live visual observation available"
    return (
        "You are connected to RTDA, a local real-time desktop observation and control runtime. "
        "Use the live desktop observation supplied for this request when it is present. "
        "It represents the current desktop state, not saved history. If no visual observation "
        "is available, use capture metrics as context and do not claim visual details. "
        f"Capture backend={backend}, resolution={resolution}, "
        f"fps={stats.capture_fps:.2f}, latency_ms={stats.capture_latency_ms}, {observation_text}."
    )


def frame_to_jpeg_data_url(frame: Frame, *, max_side: int = 1280, quality: int = 80) -> str:
    import cv2

    data = frame.data
    if data.ndim != 3 or data.shape[2] not in (3, 4):
        raise ValueError(f"unsupported frame shape for AI image: {data.shape}")
    if data.shape[2] == 4:
        image = cv2.cvtColor(data, cv2.COLOR_BGRA2BGR)
    else:
        image = data
    height, width = image.shape[:2]
    largest_side = max(width, height)
    if largest_side > max_side:
        scale = max_side / largest_side
        image = cv2.resize(
            image,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    success, encoded = cv2.imencode(
        ".jpg",
        image,
        [int(cv2.IMWRITE_JPEG_QUALITY), quality],
    )
    if not success:
        raise ValueError("could not encode RTDA frame for AI request")
    encoded_text = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded_text}"


def _complete(config: AIClientConfig, prompt: str, system: str, frame: Frame | None) -> str:
    image_data_url = frame_to_jpeg_data_url(frame) if frame is not None else None
    response = AIClient(config).complete(prompt, system=system, image_data_url=image_data_url)
    return response.output_text
