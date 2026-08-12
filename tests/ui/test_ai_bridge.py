from __future__ import annotations

import base64

import numpy as np

from desktop.ai_bridge import build_ai_system_prompt, frame_to_jpeg_data_url
from rtda.capture.frame import Frame
from rtda.capture.interface import CaptureStats


def test_frame_to_jpeg_data_url_encodes_frame_in_memory() -> None:
    data = np.zeros((4, 6, 4), dtype=np.uint8)
    data[..., 0] = 255
    data[..., 3] = 255
    frame = Frame(timestamp=1.0, width=6, height=4, data=data, sequence=1)

    data_url = frame_to_jpeg_data_url(frame, max_side=4, quality=70)

    prefix, encoded = data_url.split(",", 1)
    assert prefix == "data:image/jpeg;base64"
    assert base64.b64decode(encoded).startswith(b"\xff\xd8")


def test_system_prompt_describes_live_state_without_history() -> None:
    prompt = build_ai_system_prompt(
        backend="dxgi",
        stats=CaptureStats(
            capture_fps=20.0,
            capture_latency_ms=4.0,
            frames_captured=10,
            buffer_dropped_frames=0,
            estimated_missed_frames=0,
            backend_errors=0,
            uptime_s=1.0,
            latest_width=1920,
            latest_height=1080,
        ),
        frame=None,
    )

    assert "real-time desktop observation and control runtime" in prompt
    assert "not saved history" in prompt
    assert "no live visual observation available" in prompt
