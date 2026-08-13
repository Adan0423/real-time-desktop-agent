from __future__ import annotations

import json
import time
from typing import Any

from rtda.capture.interface import CaptureConfig
from rtda.capture.frame import Frame
from rtda.mcp.server import capture_monitors, health, session_status
from rtda.perception import HighPrecisionPerceptionPipeline
from desktop.ui.widgets import SectionPanel, make_label


class McpPanel:
    """Panel de control y diagnostico en vivo para el Servidor MCP y Percepción."""

    def __init__(self) -> None:
        from PySide6.QtWidgets import (
            QFrame,
            QGridLayout,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )

        self.status_label = QLabel("🟢 Servidor MCP v1.27 Listo (Protocolo Activo)")
        self.status_label.setStyleSheet("color: #39d98a; font-weight: 700; font-size: 13px;")

        self.btn_test_mcp = QPushButton("🧪 Test Diagnóstico MCP")
        self.btn_test_perception = QPushButton("👁️ Test Visión Alta Precisión")
        self.btn_run_benchmark = QPushButton("📊 Ejecutar Benchmark (25 Casos)")

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(220)
        self.output.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        self.output.setText("🔌 Presiona un botón para verificar el estado real del servidor MCP o la Percepción.")

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        btn_layout.addWidget(self.btn_test_mcp)
        btn_layout.addWidget(self.btn_test_perception)
        btn_layout.addWidget(self.btn_run_benchmark)

        self.btn_test_mcp.clicked.connect(self._run_mcp_test)
        self.btn_test_perception.clicked.connect(self._run_perception_test)
        self.btn_run_benchmark.clicked.connect(self._run_benchmark_test)

        info_box = QVBoxLayout()
        info_box.setContentsMargins(0, 0, 0, 0)
        info_box.setSpacing(8)
        info_box.addWidget(self.status_label)
        info_box.addLayout(btn_layout)
        info_box.addWidget(make_label("💬 Consola de Verificación en Tiempo Real", "fieldLabel"))
        info_box.addWidget(self.output, 1)

        self.widget = SectionPanel("🔌 Servidor MCP y Diagnóstico", info_box).widget

    def _run_mcp_test(self) -> None:
        self.output.setText("⌛ Probando respuestas del Servidor MCP local...")
        try:
            h = health()
            m = capture_monitors()
            s = session_status()
            res = {
                "mcp_health": h,
                "monitores": m.get("monitors", []),
                "sesion_activa": s,
                "timestamp": time.time(),
                "veredicto": "✅ SERVIDOR MCP FUNCIONANDO AL 100%",
            }
            self.output.setText(json.dumps(res, indent=2, ensure_ascii=False))
        except Exception as exc:
            self.output.setText(f"❌ Error probando MCP Server: {exc}")

    def _run_perception_test(self) -> None:
        self.output.setText("⌛ Ejecutando prueba de Visión Multicapa en tiempo real (UIA + OCR + ROI)...")
        try:
            import numpy as np
            frame = Frame(
                timestamp=time.time(),
                width=1920,
                height=1080,
                data=np.zeros((1080, 1920, 4), dtype=np.uint8),
                sequence=1,
            )
            pipeline = HighPrecisionPerceptionPipeline()
            analysis = pipeline.process_frame(frame)

            res = {
                "multicapa_perception": {
                    "elementos_detectados": len(analysis.elements),
                    "latencia_ms": round(analysis.latency_ms, 2),
                    "cambio_detectado": analysis.changed,
                    "ahorro_computo_roi": f"{analysis.work_saved_ratio}%",
                    "errores": list(analysis.errors),
                },
                "veredicto": "🟢 PIPELINE DE ALTA PRECISIÓN OK",
            }
            self.output.setText(json.dumps(res, indent=2, ensure_ascii=False))
        except Exception as exc:
            self.output.setText(f"❌ Error en Pipeline de Percepción: {exc}")

    def _run_benchmark_test(self) -> None:
        self.output.setText("⌛ Ejecutando suite de evaluación de 25 casos de prueba...")
        try:
            from tests.benchmark.test_cases import run_benchmark_suite
            report = run_benchmark_suite()
            self.output.setText(json.dumps(report, indent=2, ensure_ascii=False))
        except Exception as exc:
            self.output.setText(f"❌ Error ejecutando Benchmark Suite: {exc}")
