from __future__ import annotations

import os
from rtda.ai.client import AI_PROVIDERS, AIClientConfig, default_model, env_var_for_provider

from desktop.ui.widgets import make_label


class AiPanel:
    """Manual provider prompt panel used only by the local desktop app."""

    def __init__(self) -> None:
        from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget

        self.provider = QComboBox()
        self.provider.addItems(list(AI_PROVIDERS))
        
        self.model = QLineEdit(default_model("groq"))
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        # Select RTDA_AI_PROVIDER or first provider with configured API key in .env
        env_pref = os.environ.get("RTDA_AI_PROVIDER", "groq")
        if os.environ.get(env_var_for_provider(env_pref)):  # type: ignore[arg-type]
            first_configured = env_pref
        else:
            first_configured = next((p for p in AI_PROVIDERS if os.environ.get(env_var_for_provider(p))), "groq")
        
        idx = self.provider.findText(first_configured)
        if idx >= 0:
            self.provider.setCurrentIndex(idx)
            self.model.setText(default_model(first_configured))

        self._sync_token_from_env(self.provider.currentText())
        self.provider.currentTextChanged.connect(self.sync_model)

        self.prompt = QTextEdit()
        self.prompt.setMinimumHeight(82)
        self.prompt.setMaximumHeight(150)
        self.prompt.setPlaceholderText("💡 Escribe tu consulta sobre el estado en vivo del escritorio...")
        self.ask_button = QPushButton("✨ Consultar IA")
        self.output = QTextEdit()
        self.output.setObjectName("aiOutput")
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(120)
        self.output.setPlaceholderText("💬 Respuesta IA")
        self.output.setText("🤖 IA: esperando prompt")

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(7)
        for row, (label, widget) in enumerate(
            (
                ("🤖 Proveedor", self.provider),
                ("⚡ Modelo", self.model),
                ("🔑 Token API", self.token),
            )
        ):
            grid.addWidget(make_label(label, "fieldLabel"), row, 0)
            grid.addWidget(widget, row, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(9)
        layout.addLayout(grid)
        layout.addWidget(self.status_label)
        layout.addWidget(self.prompt)
        layout.addWidget(self.ask_button)
        layout.addWidget(self.output, 1)

        self.widget = QWidget()
        self.widget.setLayout(layout)

    def sync_model(self, provider: str) -> None:
        self.model.setText(default_model(provider))
        self._sync_token_from_env(provider)

    def request_config(self) -> AIClientConfig:
        provider = self.provider.currentText()
        token = self.token.text().strip() or None
        model = self.model.text().strip() or None
        timeout_s = 90.0 if provider == "tokenrouter" else 30.0
        return AIClientConfig(provider=provider, api_key=token, model=model, timeout_s=timeout_s)

    def prompt_text(self) -> str:
        return self.prompt.toPlainText().strip()

    def set_busy(self, busy: bool) -> None:
        self.ask_button.setEnabled(not busy)
        if busy:
            self.output.setText("⌛ IA: consultando proveedor en tiempo real...")

    def _sync_token_from_env(self, provider: str) -> None:
        env_var = env_var_for_provider(provider)
        env_val = os.environ.get(env_var, "").strip()
        if env_val:
            self.token.setText(env_val)
            self.token.setPlaceholderText(f"✓ Configurado vía .env ({env_var})")
            self.status_label.setText(f"🟢 API Key detectada en .env ({env_var})")
            self.status_label.setStyleSheet("color: #39d98a; font-size: 11px; font-weight: 600;")
        else:
            self.token.clear()
            self.token.setPlaceholderText(f"Escribe tu token o agrégalo a .env ({env_var})")
            self.status_label.setText(f"⚪ Opcional si agregas {env_var} a tu .env")
            self.status_label.setStyleSheet("color: #ffb24a; font-size: 11px; font-weight: 500;")

