from __future__ import annotations

import time
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Any

import numpy as np


@dataclass
class SharedMemoryFrameBuffer:
    """Zero-copy frame buffer using OS shared memory (multiprocessing.shared_memory).

    Allows zero-copy IPC transport of raw screen frames between capture and perception
    processes without base64 or PNG encoding overhead.
    """

    name: str = "rtda_frame_buffer_shm"
    size_bytes: int = 1920 * 1080 * 4  # 8.29 MB (supports 1080p BGRA)
    _shm: shared_memory.SharedMemory | None = None
    _is_owner: bool = False

    def create(self) -> None:
        """Create a new shared memory segment (owner process)."""
        try:
            self._shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.size_bytes)
            self._is_owner = True
        except FileExistsError:
            # Attach to existing if already created
            self._shm = shared_memory.SharedMemory(name=self.name, create=False)
            self._is_owner = False

    def attach(self) -> None:
        """Attach to an existing shared memory segment (consumer process)."""
        if self._shm is None:
            self._shm = shared_memory.SharedMemory(name=self.name, create=False)
            self._is_owner = False

    def write_frame(self, frame_data: np.ndarray) -> None:
        """Write raw numpy frame bytes into shared memory (zero-copy buffer copy)."""
        if self._shm is None:
            self.create()
        assert self._shm is not None

        raw_bytes = frame_data.tobytes()
        n = min(len(raw_bytes), self.size_bytes)
        self._shm.buf[:n] = raw_bytes[:n]

    def read_frame(self, width: int, height: int, channels: int = 4) -> np.ndarray:
        """Read raw frame numpy array directly from shared memory buffer."""
        if self._shm is None:
            self.attach()
        assert self._shm is not None

        expected_bytes = width * height * channels
        n = min(expected_bytes, self.size_bytes)

        buffer_slice = bytes(self._shm.buf[:n])
        arr = np.frombuffer(buffer_slice, dtype=np.uint8)
        return arr.reshape((height, width, channels))

    def close(self) -> None:
        """Close shared memory handle."""
        if self._shm is not None:
            self._shm.close()
            if self._is_owner:
                try:
                    self._shm.unlink()
                except Exception:
                    pass
            self._shm = None
