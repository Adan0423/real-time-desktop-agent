from __future__ import annotations

import os
from collections.abc import Callable

import customtkinter as ctk

from desktop.ai.client import AI_PROVIDERS, default_model, env_var_for_provider


class AiPanel(ctk.CTkFrame):
    """Panel tab for AI Provider prompt submission & chat completions."""

    def __init__(self, master, *, on_ask: Callable[[], None], **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_ask = on_ask

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="🤖 Proveedor IA:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.opt_provider = ctk.CTkOptionMenu(
            self,
            values=list(AI_PROVIDERS),
            command=self._on_provider_changed,
            fg_color="#1E293B",
            button_color="#0F172A",
            height=30,
        )
        self.opt_provider.set("groq")
        self.opt_provider.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(self, text="⚡ Modelo:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.entry_model = ctk.CTkEntry(self, height=30, fg_color="#020617", border_color="#1E293B")
        self.entry_model.insert(0, default_model("groq"))
        self.entry_model.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(self, text="🔑 Token API / Clave:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.entry_token = ctk.CTkEntry(self, height=30, show="•", fg_color="#020617", border_color="#1E293B")
        self.entry_token.pack(fill="x", pady=(2, 4))

        self.lbl_env_status = ctk.CTkLabel(self, text="● API Key detectada en .env", font=ctk.CTkFont(size=10, weight="bold"), text_color="#34D399")
        self.lbl_env_status.pack(anchor="w", pady=(0, 6))
        self._sync_token("groq")

        self.txt_prompt = ctk.CTkTextbox(self, height=75, fg_color="#020617", border_color="#1E293B", border_width=1)
        self.txt_prompt.pack(fill="x", pady=(0, 6))
        self.txt_prompt.insert("1.0", "💡 Consulta en vivo sobre el escritorio...")

        self.btn_ask = ctk.CTkButton(
            self,
            text="✨ Consultar IA",
            command=self._on_ask,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#ECFDF5",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
        )
        self.btn_ask.pack(fill="x", pady=(0, 6))

        self.txt_output = ctk.CTkTextbox(self, height=90, fg_color="#020617", text_color="#38BDF8", font=ctk.CTkFont(size=11))
        self.txt_output.pack(fill="both", expand=True)
        self.txt_output.insert("1.0", "🤖 IA: esperando prompt")
        self.txt_output.configure(state="disabled")

    def _on_provider_changed(self, provider: str) -> None:
        self.entry_model.delete(0, "end")
        self.entry_model.insert(0, default_model(provider))
        self._sync_token(provider)

    def _sync_token(self, provider: str) -> None:
        env_var = env_var_for_provider(provider)
        key_val = os.environ.get(env_var, "")
        self.entry_token.delete(0, "end")
        if key_val:
            self.entry_token.insert(0, key_val)
            self.lbl_env_status.configure(text=f"● API Key detectada en .env ({env_var})", text_color="#34D399")
        else:
            self.lbl_env_status.configure(text=f"⚠️ Sin clave en .env ({env_var})", text_color="#F59E0B")

    def set_output(self, text: str) -> None:
        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", text)
        self.txt_output.configure(state="disabled")

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.btn_ask.configure(state="disabled", text="⏳ Consultando...")
        else:
            self.btn_ask.configure(state="normal", text="✨ Consultar IA")
