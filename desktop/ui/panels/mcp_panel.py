from __future__ import annotations

import customtkinter as ctk


class McpPanel(ctk.CTkFrame):
    """Panel tab for MCP Server status & registered tools."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        lbl = ctk.CTkLabel(
            self,
            text="🔌 Servidor MCP Integrado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC",
        )
        lbl.pack(anchor="w")

        self.mcp_box = ctk.CTkTextbox(
            self,
            height=180,
            fg_color="#020617",
            text_color="#34D399",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.mcp_box.pack(fill="both", expand=True, pady=6)
        self.mcp_box.insert(
            "1.0",
            "● Servidor MCP activo en puerto local\n"
            "● Herramientas registradas: 13 (observe_state, click, type, hotkey, screenshot, uia_snapshot)\n"
            "● Protocolo: Standard MCP 1.0 JSON-RPC 2.0",
        )
        self.mcp_box.configure(state="disabled")
