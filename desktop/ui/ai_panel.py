from __future__ import annotations

from rtda.ai.client import AI_PROVIDERS, AIClientConfig, default_model

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
        self.prompt = QTextEdit()
        self.prompt.setMinimumHeight(82)
        self.prompt.setPlaceholderText("Pregunta usando el contexto capturado por RTDA.")
        self.ask_button = QPushButton("Consultar IA")
        self.output = make_label("IA: esperando prompt", "mutedText")
        self.output.setWordWrap(True)

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

    def request_config(self) -> AIClientConfig:
        token = self.token.text().strip() or None
        model = self.model.text().strip() or None
        return AIClientConfig(provider=self.provider.currentText(), api_key=token, model=model)

    def prompt_text(self) -> str:
        return self.prompt.toPlainText().strip()

    def set_busy(self, busy: bool) -> None:
        self.ask_button.setEnabled(not busy)
        if busy:
            self.output.setText("IA: consultando proveedor")
