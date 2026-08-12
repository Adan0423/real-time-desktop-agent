from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_openai_plugin_manifest_points_to_mcp_config() -> None:
    manifest_path = ROOT / "plugins" / "real-time-desktop-agent" / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["name"] == "real-time-desktop-agent"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert manifest["interface"]["displayName"] == "Real-Time Desktop Agent"


def test_openai_plugin_mcp_config_uses_rtda_server() -> None:
    config_path = ROOT / "plugins" / "real-time-desktop-agent" / ".mcp.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    server = config["real-time-desktop-agent"]

    # Accept both "python" (generic) and absolute paths like C:\Python314\python.exe
    # The .mcp.json may use an absolute path so Claude Desktop finds the correct interpreter.
    assert "python" in server["command"].lower()
    assert server["args"] == ["-m", "rtda.mcp.server", "--transport", "stdio"]


def test_repo_marketplace_points_to_plugin_folder() -> None:
    marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin = marketplace["plugins"][0]

    assert plugin["name"] == "real-time-desktop-agent"
    assert plugin["source"]["path"] == "./plugins/real-time-desktop-agent"
    assert plugin["policy"]["installation"] == "AVAILABLE"
