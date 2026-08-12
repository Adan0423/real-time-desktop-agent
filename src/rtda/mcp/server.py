from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Any

from rtda.agent.planner import RuleBasedPlanner
from rtda.capture.diagnostics import monitors_to_dict, run_capture_diagnostic
from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region
from rtda.complement import RTDAComplementConfig, RTDAComplementRuntime
from rtda.models.actions import ActionCommand, ActionType
from rtda.models.state import UIState
from rtda.perception.uia import summarize_uia_elements
from rtda.safety.action_guard import ActionGuard
from rtda.safety.confirmation import ConfirmationManager
from rtda.safety.policy import ActionPolicy


def health() -> dict[str, Any]:
    return {"name": "real-time-desktop-agent", "status": "ok", "phases": [1, 2, 3, 4, 5, 6, 7, 8]}


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


def build_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("mcp>=1.27,<2 is required to run the RTDA MCP server") from exc

    mcp = FastMCP("RTDA", json_response=True)
    mcp.tool()(health)
    mcp.tool()(inspect_uia)
    mcp.tool()(plan_goal)
    mcp.tool()(capture_monitors)
    mcp.tool()(capture_diagnostic)
    mcp.tool()(classify_action)
    mcp.tool()(dry_run_action)
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
