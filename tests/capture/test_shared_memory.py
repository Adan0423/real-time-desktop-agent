from __future__ import annotations

import numpy as np
from rtda.capture.shared_memory import SharedMemoryFrameBuffer


def test_shared_memory_frame_buffer_write_read() -> None:
    shm_buf = SharedMemoryFrameBuffer(name="test_rtda_shm_buffer", size_bytes=100 * 100 * 4)

    try:
        shm_buf.create()

        # Create dummy 100x100 BGRA frame
        original_data = np.full((100, 100, 4), fill_value=128, dtype=np.uint8)
        original_data[10, 10] = [255, 0, 0, 255]

        # Write to shared memory
        shm_buf.write_frame(original_data)

        # Read from shared memory
        read_data = shm_buf.read_frame(width=100, height=100, channels=4)

        assert read_data.shape == (100, 100, 4)
        assert np.array_equal(read_data[10, 10], [255, 0, 0, 255])
        assert np.array_equal(read_data[0, 0], [128, 128, 128, 128])
    finally:
        shm_buf.close()
