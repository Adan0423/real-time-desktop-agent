from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Any

from rtda.actions.engine import ActionEngine
from rtda.agent.executor import AgentExecutor
from rtda.agent.observer import AgentObserver
from rtda.agent.planner import RuleBasedPlanner
from rtda.capture.diagnostics import monitors_to_dict, run_capture_diagnostic
from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region
from rtda.complement import RTDAComplementConfig, RTDAComplementRuntime
from rtda.models.actions import ActionCommand, ActionType
from rtda.session.desktop_session import DesktopSession
from rtda.models.state import UIState
from rtda.perception.uia import summarize_uia_elements
from rtda.safety.action_guard import ActionGuard
from rtda.safety.confirmation import ConfirmationManager
from rtda.safety.policy import ActionPolicy


def health() -> dict[str, Any]:
    return {"name": "real-time-desktop-agent", "status": "ok", "phases": [1, 2, 3, 4, 5, 6, 7, 8]}


# ── Original tools (unchanged) ──────────────────────────────────────────────

def inspect_uia(window_title: str | None = None, max_depth: int = 3, max_elements: int = 120) -> dict[str, Any]:
    runtime = RTDAComplementRuntime(RTDAComplementConfig(uia_max_depth=max_depth, uia_max_elements=max_elements))
    snapshot = runtime.inspect_ui(window_title=window_title)
    return {
        "element_count": snapshot.element_count,
        "latency_ms": snapshot.latency_ms,
        "truncated": snapshot.truncated,
        "errors": list(snapshot.errors),
        "elements": summarize_uia_elements(snapshot.elements),
    }


def plan_goal(goal: str) -> dict[str, Any]:
    plan = RuleBasedPlanner().plan(UIState(), goal)
    return {
        "goal": plan.goal,
        "rationale": plan.rationale,
        "actions": [action.model_dump(mode="json") for action in plan.actions],
    }


def classify_action(action: str, target: str | None = None, value: str | None = None) -> dict[str, Any]:
    command = ActionCommand(action=ActionType(action), target=target, value=value)
    guard = ActionGuard(policy=ActionPolicy(), confirmations=ConfirmationManager())
    allowed, risk, message = guard.allowed(command)
    return {"allowed": allowed, "risk": risk.value, "message": message}


def capture_monitors() -> dict[str, Any]:
    runtime = RTDAComplementRuntime(CaptureConfig())
    return {"monitors": monitors_to_dict(runtime.list_monitors())}


def capture_diagnostic(
    duration_s: float = 2.0,
    backend: str = "dxgi",
    target_fps: int = 30,
    max_buffer_size: int = 2,
    monitor_index: int = 0,
    window_title: str | None = None,
    region_left: int | None = None,
    region_top: int | None = None,
    region_right: int | None = None,
    region_bottom: int | None = None,
) -> dict[str, Any]:
    region = None
    if None not in (region_left, region_top, region_right, region_bottom):
        region = Region(
            int(region_left),
            int(region_top),
            int(region_right),
            int(region_bottom),
        )
    selected_backend = "wgc" if window_title else backend
    config = CaptureConfig(
        backend=selected_backend,
        target_fps=target_fps,
        max_buffer_size=max_buffer_size,
        monitor_index=monitor_index,
        region=region,
        window_title=window_title,
    )
    runtime = RTDAComplementRuntime(RTDAComplementConfig(capture=config, enable_border=False))
    result = run_capture_diagnostic(runtime, config=config, duration_s=duration_s)
    return result.to_dict()


def dry_run_action(action: str, target: str | None = None, value: str | None = None) -> dict[str, Any]:
    command = ActionCommand(action=ActionType(action), target=target, value=value)
    runtime = RTDAComplementRuntime(RTDAComplementConfig(dry_run_actions=True))
    result = runtime.execute_action(command)
    return result.model_dump(mode="json")


# ── Global Persistent Desktop Session ──────────────────────────────────────
GLOBAL_SESSION = DesktopSession()
GLOBAL_SESSION.start()


def session_status() -> dict[str, Any]:
    """Return status and metadata of the active persistent desktop session."""
    return GLOBAL_SESSION.get_summary()


def get_focused_window() -> dict[str, Any]:
    """Return the title and basic info about the current foreground window."""
    state = GLOBAL_SESSION.observe()
    return {
        "focused_window": state.focused_window,
        "application": state.application,
        "element_count": len(state.elements),
        "uia_latency_ms": state.uia_snapshot.latency_ms if state.uia_snapshot else None,
    }


def observe_state(
    window_title: str | None = None,
    max_elements: int = 30,
) -> dict[str, Any]:
    """Observe the current desktop state: active window, application, and UI elements.

    Args:
        window_title:  Optional title filter. If None, uses the foreground window.
        max_elements:  Maximum number of elements to return (default 30).

    Returns:
        A JSON-serialisable snapshot of the current UI state.
    """
    summary = GLOBAL_SESSION.observer.observe_summary(window_title=window_title)
    summary["elements"] = summary["elements"][:max_elements]
    summary["session_id"] = GLOBAL_SESSION.session_id
    return summary


def desktop_find(target: str) -> dict[str, Any]:
    """Data Channel tool: Search for UI elements matching target name/text without requesting images.

    Args:
        target: Text or control type to search for (case-insensitive).

    Returns:
        Matched elements with coordinates and confidence.
    """
    state = GLOBAL_SESSION.observe()
    matches = state.find_elements(target)
    return {
        "target": target,
        "matched_count": len(matches),
        "matches": [
            {
                "type": m.type,
                "text": m.text,
                "bbox": m.bbox.to_tuple() if m.bbox else None,
                "confidence": m.confidence,
                "source": m.source,
            }
            for m in matches[:15]
        ],
    }


def run_task(
    goal: str,
    max_steps: int = 10,
    expected_text: str | None = None,
    window_title: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute a multi-step desktop task using the full observe→plan→act→verify loop.

    Args:
        goal:          Natural-language instruction (e.g. ``"click OK"``).
        max_steps:     Safety cap on the number of action cycles (default 10).
        expected_text: If provided, task succeeds when this text appears in the UI.
        window_title:  Target window title. Defaults to the foreground window.
        dry_run:       If True (default), actions are simulated, not executed.
                       Set to False to perform real mouse/keyboard actions.

    Returns:
        Task result with success flag, steps taken, timing, and per-cycle details.
    """
    result = GLOBAL_SESSION.run_task(
        goal,
        max_steps=max_steps,
        expected_text=expected_text,
        dry_run=dry_run,
    )

    cycles_summary = []
    for cycle in result.cycles:
        cycles_summary.append({
            "plan_rationale": cycle.plan.rationale,
            "actions": [a.model_dump(mode="json") for a in cycle.plan.actions],
            "action_result": cycle.action_results[0].model_dump(mode="json") if cycle.action_results else None,
            "verification_success": cycle.verification.success if cycle.verification else None,
            "verification_message": cycle.verification.message if cycle.verification else None,
            "recovery_reason": cycle.recovery.reason if cycle.recovery else None,
        })

    return {
        "goal": result.goal,
        "success": result.success,
        "steps": result.steps,
        "stop_reason": result.stop_reason,
        "elapsed_ms": result.elapsed_ms,
        "telemetry": result.telemetry,
        "dry_run": dry_run,
        "session_id": GLOBAL_SESSION.session_id,
        "focused_window": result.final_state.focused_window,
        "application": result.final_state.application,
        "cycles": cycles_summary,
    }


def execute_action(
    action: str,
    target: str | None = None,
    value: str | None = None,
    keys: list[str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute a single desktop action with optional dry-run mode.

    Args:
        action:  Action type string (e.g. ``"click"``, ``"type"``, ``"hotkey"``).
        target:  Target element name or label.
        value:   Text to type or URL to navigate.
        keys:    Key list for hotkey actions (e.g. ``["ctrl", "s"]``).
        dry_run: If True (default), simulates without real mouse/keyboard events.

    Returns:
        ActionResult as JSON.
    """
    result = GLOBAL_SESSION.execute_action(
        action=action,
        target=target,
        value=value,
        keys=keys,
        dry_run=dry_run,
    )
    return result.model_dump(mode="json")


# ── Server assembly ──────────────────────────────────────────────────────────

def build_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("mcp>=1.27,<2 is required to run the RTDA MCP server") from exc

    mcp = FastMCP("RTDA", json_response=True)

    # Original tools
    mcp.tool()(health)
    mcp.tool()(inspect_uia)
    mcp.tool()(plan_goal)
    mcp.tool()(capture_monitors)
    mcp.tool()(capture_diagnostic)
    mcp.tool()(classify_action)
    mcp.tool()(dry_run_action)

    # Phase-7+ & Runtime v2 tools
    mcp.tool()(session_status)
    mcp.tool()(get_focused_window)
    mcp.tool()(observe_state)
    mcp.tool()(desktop_find)
    mcp.tool()(run_task)
    mcp.tool()(execute_action)

    return mcp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RTDA MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
    args = parser.parse_args(argv)
    server = build_mcp_server()
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

