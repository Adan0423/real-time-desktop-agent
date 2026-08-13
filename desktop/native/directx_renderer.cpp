/*
 * Real-Time Desktop Agent (RTDA) - Native C++ DirectX 11 ROI Frame Processor
 * Compile Target: win32_helper.dll
 */

#include <windows.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <cstdint>

extern "C" {

struct BoundingBoxC {
    int32_t left;
    int32_t top;
    int32_t right;
    int32_t bottom;
};

// High-speed native C++ region difference detector for frame buffers
__declspec(dllexport) int32_t native_compute_frame_diff(
    const uint8_t* frame_a,
    const uint8_t* frame_b,
    int32_t width,
    int32_t height,
    int32_t threshold,
    BoundingBoxC* out_bbox
) {
    if (!frame_a || !frame_b || !out_bbox) return 0;

    int32_t min_x = width, min_y = height, max_x = 0, max_y = 0;
    int32_t changed_pixels = 0;

    int32_t stride = 4; // BGRA 4 bytes per pixel
    int32_t total_pixels = width * height;

    for (int32_t i = 0; i < total_pixels; i += 4) {
        int32_t idx = i * stride;
        int32_t diff_b = abs((int32_t)frame_a[idx] - (int32_t)frame_b[idx]);
        int32_t diff_g = abs((int32_t)frame_a[idx + 1] - (int32_t)frame_b[idx + 1]);
        int32_t diff_r = abs((int32_t)frame_a[idx + 2] - (int32_t)frame_b[idx + 2]);

        if (diff_b + diff_g + diff_r > threshold) {
            int32_t x = i % width;
            int32_t y = i / width;

            if (x < min_x) min_x = x;
            if (x > max_x) max_x = x;
            if (y < min_y) min_y = y;
            if (y > max_y) max_y = y;
            changed_pixels++;
        }
    }

    if (changed_pixels > 0) {
        out_bbox->left = min_x;
        out_bbox->top = min_y;
        out_bbox->right = max_x;
        out_bbox->bottom = max_y;
        return 1;
    }
    return 0;
}

}
