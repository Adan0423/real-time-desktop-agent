/*
 * Real-Time Desktop Agent (RTDA) - Native C Win32 Helper
 * Compile Target: win32_helper.dll
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dwmapi.h>
#include <stdio.h>

#define DWMWA_USE_IMMERSIVE_DARK_MODE 20
#define DWMWA_WINDOW_CORNER_PREFERENCE 33
#define DWMWA_SYSTEMBACKDROP_TYPE 38

// Get high-precision system time in milliseconds using QueryPerformanceCounter
__declspec(dllexport) double native_get_high_res_time_ms(void) {
    LARGE_INTEGER freq, counter;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&counter);
    return ((double)counter.QuadPart * 1000.0) / (double)freq.QuadPart;
}

// Native C Win32: Apply Windows 11 Dark Mode and Rounded Corners
__declspec(dllexport) int native_apply_win11_theme(HWND hwnd, int dark_mode, int rounded_corners) {
    if (!hwnd) return 0;

    int mode = dark_mode ? 1 : 0;
    DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, &mode, sizeof(mode));

    if (rounded_corners) {
        int corner_pref = 2; // DWMWCP_ROUND
        DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, &corner_pref, sizeof(corner_pref));
    }
    return 1;
}

// Native C Win32: Apply Windows 11 Mica Backdrop Effect
__declspec(dllexport) int native_enable_mica(HWND hwnd, int backdrop_type) {
    if (!hwnd) return 0;
    int type = backdrop_type; // 2 = Mica, 3 = Acrylic
    HRESULT hr = DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, &type, sizeof(type));
    return SUCCEEDED(hr) ? 1 : 0;
}

// Native C Win32: Fetch Active Window Title
__declspec(dllexport) int native_get_foreground_title(wchar_t* buffer, int max_chars) {
    HWND hwnd = GetForegroundWindow();
    if (!hwnd) return 0;
    return GetWindowTextW(hwnd, buffer, max_chars);
}
