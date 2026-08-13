from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.ui.floating.floating_styles import FLOATING_STYLE


class StatusDotWidget(QWidget):
    """Small status indicator dot for Ready/Running/Paused/Error states."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tone = "idle"
        self.setFixedSize(14, 14)

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color_map = {
            "idle": QColor("#29D98F"),
            "active": QColor("#26D7D0"),
            "paused": QColor("#F4C95D"),
            "error": QColor("#F35D7A"),
        }
        main_color = color_map.get(self._tone, QColor("#29D98F"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(main_color)
        painter.drawEllipse(3, 3, 8, 8)
        painter.end()


class FloatingWidget(QWidget):
    """Dual-mode (COLLAPSED / EXPANDED) frameless floating widget for RTDA."""

    def __init__(
        self,
        *,
        on_open: Callable[[], None],
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_quit: Callable[[], None],
        on_screenshot: Callable[[], None] | None = None,
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._on_open = on_open
        self._on_start = on_start
        self._on_pause = on_pause
        self._on_stop = on_stop
        self._on_quit = on_quit
        self._on_screenshot = on_screenshot
        self._on_settings = on_settings

        self._drag_origin: QPoint | None = None
        self._running = False
        self._paused = False
        self._mode = "COLLAPSED"
        self._auto_collapse = True
        self._always_on_top = True

        self._settings = QSettings("RTDA", "FloatingControl")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("floatingRoot")
        self.setStyleSheet(FLOATING_STYLE)

        self._init_ui()
        self._load_saved_settings()

        self._auto_collapse_timer = QTimer(self)
        self._auto_collapse_timer.setInterval(4000)
        self._auto_collapse_timer.setSingleShot(True)
        self._auto_collapse_timer.timeout.connect(self._handle_auto_collapse)

    def _init_ui(self) -> None:
        # --- COLLAPSED CARD ---
        self.collapsed_card = QFrame()
        self.collapsed_card.setObjectName("collapsedCard")
        self.collapsed_card.setFixedSize(145, 175)

        self.dot = StatusDotWidget()
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_logo()

        self.collapsed_title = QLabel("RTDA")
        self.collapsed_title.setObjectName("floatingTitle")
        self.collapsed_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.collapsed_status = QLabel("Listo")
        self.collapsed_status.setObjectName("floatingSubtitle")
        self.collapsed_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.collapsed_action_btn = QPushButton("▶ Iniciar")
        self.collapsed_action_btn.setObjectName("actionStartButton")
        self.collapsed_action_btn.clicked.connect(self._handle_primary_action)

        self.expand_btn = QPushButton("↔️ Expandir")
        self.expand_btn.setObjectName("toggleExpandButton")
        self.expand_btn.clicked.connect(self.toggle_mode)

        c_top = QHBoxLayout()
        c_top.setContentsMargins(8, 6, 8, 0)
        c_top.addStretch(1)
        c_top.addWidget(self.dot)

        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(10, 6, 10, 10)
        c_layout.setSpacing(4)
        c_layout.addLayout(c_top)
        c_layout.addWidget(self.logo_label)
        c_layout.addWidget(self.collapsed_title)
        c_layout.addWidget(self.collapsed_status)
        c_layout.addWidget(self.collapsed_action_btn)
        c_layout.addWidget(self.expand_btn)
        self.collapsed_card.setLayout(c_layout)

        # --- EXPANDED PANEL ---
        self.expanded_panel = QFrame()
        self.expanded_panel.setObjectName("expandedPanel")
        self.expanded_panel.setFixedSize(270, 175)

        self.exp_title = QLabel("RTDA Control")
        self.exp_title.setObjectName("floatingTitle")
        self.exp_status = QLabel("Listo ● local MCP")
        self.exp_status.setObjectName("floatingSubtitle")

        self.gear_btn = QPushButton("⚙")
        self.gear_btn.setObjectName("iconOnlyButton")
        self.gear_btn.setToolTip("Ajustes")
        if self._on_settings:
            self.gear_btn.clicked.connect(self._on_settings)

        self.close_panel_btn = QPushButton("✕")
        self.close_panel_btn.setObjectName("iconOnlyButton")
        self.close_panel_btn.setToolTip("Colapsar")
        self.close_panel_btn.clicked.connect(self.collapse)

        exp_top = QHBoxLayout()
        exp_top.setContentsMargins(0, 0, 0, 0)
        exp_title_box = QVBoxLayout()
        exp_title_box.setSpacing(1)
        exp_title_box.addWidget(self.exp_title)
        exp_title_box.addWidget(self.exp_status)
        exp_top.addLayout(exp_title_box)
        exp_top.addStretch(1)
        exp_top.addWidget(self.gear_btn)
        exp_top.addWidget(self.close_panel_btn)

        self.exp_metrics = QLabel("0.0 FPS  |  drop 0")
        self.exp_metrics.setObjectName("floatingMetrics")

        # Action grid (Start, Pause, Stop)
        self.start_btn = QPushButton("▶ Iniciar")
        self.start_btn.setObjectName("actionStartButton")
        self.start_btn.clicked.connect(self._on_start)

        self.pause_btn = QPushButton("⏸ Pausar")
        self.pause_btn.setObjectName("actionPauseButton")
        self.pause_btn.clicked.connect(self._on_pause)

        self.stop_btn = QPushButton("⏹ Detener")
        self.stop_btn.setObjectName("actionStopButton")
        self.stop_btn.clicked.connect(self._on_stop)

        grid_actions = QHBoxLayout()
        grid_actions.setContentsMargins(0, 0, 0, 0)
        grid_actions.setSpacing(4)
        grid_actions.addWidget(self.start_btn)
        grid_actions.addWidget(self.pause_btn)
        grid_actions.addWidget(self.stop_btn)

        # Utility grid (Screenshot, Settings)
        self.screenshot_btn = QPushButton("📷 Screenshot")
        self.screenshot_btn.setObjectName("utilityButton")
        if self._on_screenshot:
            self.screenshot_btn.clicked.connect(self._on_screenshot)
        else:
            self.screenshot_btn.clicked.connect(self._on_open)

        self.settings_btn = QPushButton("⚙ Ajustes")
        self.settings_btn.setObjectName("utilityButton")
        if self._on_settings:
            self.settings_btn.clicked.connect(self._on_settings)
        else:
            self.settings_btn.clicked.connect(self._on_open)

        grid_utils = QHBoxLayout()
        grid_utils.setContentsMargins(0, 0, 0, 0)
        grid_utils.setSpacing(4)
        grid_utils.addWidget(self.screenshot_btn)
        grid_utils.addWidget(self.settings_btn)

        self.exp_footer = QLabel("● Runtime Online")
        self.exp_footer.setObjectName("floatingSubtitle")

        exp_layout = QVBoxLayout()
        exp_layout.setContentsMargins(10, 10, 10, 10)
        exp_layout.setSpacing(6)
        exp_layout.addLayout(exp_top)
        exp_layout.addWidget(self.exp_metrics)
        exp_layout.addLayout(grid_actions)
        exp_layout.addLayout(grid_utils)
        exp_layout.addWidget(self.exp_footer)
        self.expanded_panel.setLayout(exp_layout)

        # --- ROOT LAYOUT ---
        self.root_layout = QHBoxLayout()
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(6)
        self.root_layout.addWidget(self.collapsed_card)
        self.root_layout.addWidget(self.expanded_panel)

        self.setLayout(self.root_layout)
        self.expanded_panel.hide()
        self.adjustSize()

    def _load_logo(self) -> None:
        icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("🌟")
            self.logo_label.setStyleSheet("font-size: 24px;")

    def _handle_primary_action(self) -> None:
        if self._running and self._paused:
            self._on_pause()
        elif self._running:
            self._on_pause()
        else:
            self._on_start()

    def set_status(
        self,
        *,
        running: bool,
        paused: bool,
        fps: float,
        resolution: str,
        latency_ms: float | None,
        dropped: int,
    ) -> None:
        self._running = running
        self._paused = paused

        if running and paused:
            label = "Pausado"
            tone = "paused"
            btn_text = "▶ Reanudar"
        elif running:
            label = "Activo"
            tone = "active"
            btn_text = "⏸ Pausar"
        else:
            label = "Listo"
            tone = "idle"
            btn_text = "▶ Iniciar"

        self.dot.set_tone(tone)
        self.collapsed_status.setText(label)
        self.collapsed_action_btn.setText(btn_text)

        self.start_btn.setEnabled(not running)
        self.pause_btn.setEnabled(running)
        self.stop_button = getattr(self, "stop_btn", None)
        if self.stop_button:
            self.stop_button.setEnabled(running)

        self.exp_status.setText(f"{label} ● local MCP")
        self.exp_metrics.setText(f"{fps:.1f} FPS  |  drop {dropped}")

    def toggle_mode(self) -> None:
        if self._mode == "COLLAPSED":
            self.expand()
        else:
            self.collapse()

    def expand(self) -> None:
        self._mode = "EXPANDED"
        self.expanded_panel.show()
        self.expand_btn.setText("◀ Ocultar")
        self.adjustSize()
        if self._auto_collapse:
            self._auto_collapse_timer.start()

    def collapse(self) -> None:
        self._mode = "COLLAPSED"
        self.expanded_panel.hide()
        self.expand_btn.setText("↔️ Expandir")
        self.adjustSize()
        self._auto_collapse_timer.stop()

    def _handle_auto_collapse(self) -> None:
        if self._mode == "EXPANDED" and not self.underMouse():
            self.collapse()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        if self._auto_collapse_timer.isActive():
            self._auto_collapse_timer.stop()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        if self._mode == "EXPANDED" and self._auto_collapse:
            self._auto_collapse_timer.start()

    # --- MOUSE DRAG & PERSISTENCE ---
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_origin is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_origin
            self.move(self._snap_to_screen_edges(new_pos))
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if self._drag_origin is not None:
            self._drag_origin = None
            self._save_position()
            event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_open()
            event.accept()

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        open_action = menu.addAction("🗔 Abrir RTDA")
        open_action.triggered.connect(self._on_open)
        menu.addSeparator()

        top_action = menu.addAction("📌 Siempre Visible")
        top_action.setCheckable(True)
        top_action.setChecked(self._always_on_top)
        top_action.triggered.connect(self._toggle_always_on_top)

        auto_col_action = menu.addAction("⏱️ Auto-Colapsar")
        auto_col_action.setCheckable(True)
        auto_col_action.setChecked(self._auto_collapse)
        auto_col_action.triggered.connect(self._toggle_auto_collapse)

        if self._on_settings:
            settings_action = menu.addAction("⚙️ Ajustes...")
            settings_action.triggered.connect(self._on_settings)

        hide_action = menu.addAction("👁️ Ocultar Widget")
        hide_action.triggered.connect(self.hide)

        menu.addSeparator()
        exit_action = menu.addAction("❌ Salir de RTDA")
        exit_action.triggered.connect(self._on_quit)

        menu.exec(event.globalPos())

    def _toggle_always_on_top(self, checked: bool) -> None:
        self._always_on_top = checked
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self._settings.setValue("always_on_top", checked)

    def _toggle_auto_collapse(self, checked: bool) -> None:
        self._auto_collapse = checked
        self._settings.setValue("auto_collapse", checked)

    def _snap_to_screen_edges(self, pos: QPoint) -> QPoint:
        screen = self.screen()
        if not screen:
            return pos
        available = screen.availableGeometry()
        threshold = 15

        x = pos.x()
        y = pos.y()

        if abs(x - available.left()) < threshold:
            x = available.left() + 5
        elif abs(x + self.width() - available.right()) < threshold:
            x = available.right() - self.width() - 5

        if abs(y - available.top()) < threshold:
            y = available.top() + 5
        elif abs(y + self.height() - available.bottom()) < threshold:
            y = available.bottom() - self.height() - 5

        return QPoint(x, y)

    def _save_position(self) -> None:
        pos = self.pos()
        self._settings.setValue("x", pos.x())
        self._settings.setValue("y", pos.y())

    def _load_saved_settings(self) -> None:
        x = self._settings.value("x", type=int)
        y = self._settings.value("y", type=int)
        if x and y:
            self.move(QPoint(x, y))
        else:
            self._move_to_default_position()

        self._always_on_top = self._settings.value("always_on_top", True, type=bool)
        self._auto_collapse = self._settings.value("auto_collapse", True, type=bool)

    def _move_to_default_position(self) -> None:
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            self.move(available.right() - 200, available.top() + 40)
