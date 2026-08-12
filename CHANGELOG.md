# 📜 Changelog — Real-Time Desktop Agent

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0-beta.1] - 2026-08-12

### 🚀 Added
- **`DesktopSession` Persistent Runtime**: Persistent session runtime maintaining background observation, input controllers, state store, and event bus alive across multiple tasks.
- **Native Win32 `SendInput` Backend**: Ultra-low latency (`< 15 ms`) native Windows mouse/keyboard execution via `user32.dll` `SendInput` API.
- **`ROIProcessor` Work Elimination**: Screen perception ROI cropping reducing OCR/CV workload by over 93% on unchanged frames.
- **Native WinEvents Listener (`SetWinEventHook`)**: Real-time native Windows event listener for foreground window switching (`EVENT_SYSTEM_FOREGROUND`) and dialog creation (`EVENT_OBJECT_SHOW`).
- **Zero-Copy IPC Frame Buffer**: Shared memory transport (`multiprocessing.shared_memory.SharedMemory`) for raw BGRA frame sharing between process boundaries.
- **FastAPI Service Gateway & WebSockets Event Stream**: Administrative REST endpoints (`/health`, `/metrics`, `/sessions`) and real-time bidirectional WebSocket event streams (`/events` and `/desktop`).
- **25-Case Automated Benchmark Suite**: Comprehensive benchmark framework (`tests/benchmark/`) testing Level 1 (Single Actions), Level 2 (Multi-Step), Level 3 (Multi-Window), and Level 4 (Complex Workflows) with 100% pass rate.
- **Fine-Grained Telemetry**: Phase-by-phase breakdown metrics (`observe_ms`, `plan_ms`, `act_ms`, `verify_ms`, `avg_cycle_ms`) in `AgentTaskResult`.

### 🔄 Changed
- Refactored `AgentExecutor.run_task()` to execute full multi-step `OBSERVE → PLAN → ACT → VERIFY → RECOVER` loops.
- Updated `RuleBasedPlanner` to handle multi-action compound goals and track completed action history.
- Upgraded `Verifier` to compare real UIA element diffs and active window focus changes.
- Reorganized `tests/` into clean domain directories (`unit/`, `capture/`, `perception/`, `ui/`, `benchmark/`).

### 📦 Packaging
- Generated standalone 1-click MCP extension bundle: `dist/real-time-desktop-agent-0.1.0.mcpb` (251.5 KB).
