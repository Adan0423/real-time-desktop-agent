from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from rtda.ai.client import AIClient, AIClientConfig
from rtda.capture.interface import CaptureStats
from rtda.capture.frame import Frame


class AIRequestRunner:
    """Runs provider calls away from the Qt event loop."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rtda-ai")
        self._future: Future[str] | None = None

    @property
    def busy(self) -> bool:
        return self._future is not None and not self._future.done()

    def submit(self, config: AIClientConfig, prompt: str, system: str) -> None:
        self._future = self._executor.submit(_complete, config, prompt, system)

    def pop_result(self) -> str | None:
        if self._future is None or not self._future.done():
            return None
        future = self._future
        self._future = None
        return future.result()

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


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
    frame_text = "no latest frame" if frame is None else f"latest frame #{frame.sequence}"
    return (
        "You are using RTDA through its local AI complement runtime. "
        "Use capture metrics as context, but do not claim visual details "
        "that are not present in the user prompt. "
        f"Capture backend={backend}, resolution={resolution}, "
        f"fps={stats.capture_fps:.2f}, latency_ms={stats.capture_latency_ms}, {frame_text}."
    )


def _complete(config: AIClientConfig, prompt: str, system: str) -> str:
    response = AIClient(config).complete(prompt, system=system)
    return response.output_text
