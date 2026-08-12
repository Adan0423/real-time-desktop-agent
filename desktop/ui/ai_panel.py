from __future__ import annotations

from rtda.ai.client import AI_PROVIDERS, AIClientConfig, default_model, env_var_for_provider

from desktop.ui.widgets import make_label


class AiPanel:
    """Manual provider prompt panel used only by the local desktop app."""

    def __init__(self) -> None:
        from PySide6.QtWidgets import QComboBox, QGridLayout, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget

        self.provider = QComboBox()
        self.provider.addItems(list(AI_PROVIDERS))
        self.model = QLineEdit(default_model("openai"))
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self._sync_token_placeholder("openai")
        self.prompt = QTextEdit()
        self.prompt.setMinimumHeight(82)
        self.prompt.setMaximumHeight(150)
        self.prompt.setPlaceholderText("Pregunta sobre el estado vivo del escritorio en RTDA.")
        self.ask_button = QPushButton("Consultar IA")
        self.output = QTextEdit()
        self.output.setObjectName("aiOutput")
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(120)
        self.output.setPlaceholderText("Respuesta IA")
        self.output.setText("IA: esperando prompt")

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(7)
        for row, (label, widget) in enumerate(
            (
                ("Proveedor", self.provider),
                ("Modelo", self.model),
                ("Token", self.token),
            )
        ):
            grid.addWidget(make_label(label, "fieldLabel"), row, 0)
            grid.addWidget(widget, row, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(9)
        layout.addLayout(grid)
        layout.addWidget(self.prompt)
        layout.addWidget(self.ask_button)
        layout.addWidget(self.output, 1)

        self.widget = QWidget()
        self.widget.setLayout(layout)

    def sync_model(self, provider: str) -> None:
        self.model.setText(default_model(provider))
        self._sync_token_placeholder(provider)

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
            self.output.setText("IA: consultando proveedor")

    def _sync_token_placeholder(self, provider: str) -> None:
        self.token.setPlaceholderText(f"Opcional si existe {env_var_for_provider(provider)}")
