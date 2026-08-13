from __future__ import annotations

import os
import time
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from rtda.capture.interface import CaptureConfig
from desktop.ai_bridge import DesktopAiRunner
from desktop.ai.client import AIClientConfig
from desktop.floating import RTDAFloatingControl
from desktop.runtime_bridge import DesktopRuntimeBridge
from desktop.ui.components import ActionBar, StatusPill
from desktop.ui.panels import AiPanel, CapturePanel, McpPanel, MetricsPanel, SettingsPanel
from desktop.ui.theme import apply_theme_settings, THEME_PALETTE as T


class CollapsiblePreview(ctk.CTkFrame):
    """Preview frame with a collapse/expand toggle button (▲/▼)."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=T["background_main"],
            corner_radius=14,
            border_color=T["border"],
            border_width=1,
            **kwargs,
        )
        self._expanded = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── HEADER BAR ──
        header = ctk.CTkFrame(self, fg_color="transparent", height=38)
        header.grid(row=0, column=0, padx=14, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        self.lbl_title = ctk.CTkLabel(
            header,
            text="\U0001f5bc\ufe0f  Vista de Pantalla en Tiempo Real",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=T["text_primary"],
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.lbl_stats = ctk.CTkLabel(
            header,
            text="Listo  |  dxgi  |  0.0 FPS",
            font=ctk.CTkFont(size=11),
            text_color=T["accent_cyan"],
        )
        self.lbl_stats.grid(row=0, column=1, sticky="e")

        self.btn_toggle = ctk.CTkButton(
            header,
            text="\u25b2",
            width=30,
            height=26,
            corner_radius=8,
            fg_color=T["background_card"],
            hover_color="#1D3050",
            text_color=T["accent_cyan"],
            border_color=T["border"],
            border_width=1,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle,
        )
        self.btn_toggle.grid(row=0, column=2, padx=(10, 0))

        # ── PREVIEW SURFACE ──
        self.surface = ctk.CTkLabel(
            self,
            text="\U0001f3ac  Presiona  \u25b6 Iniciar  (F5)  para previsualizar el escritorio en vivo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4B5E7A",
            fg_color=T["background_input"],
            corner_radius=10,
        )
        self.surface.grid(row=1, column=0, padx=14, pady=(6, 14), sticky="nsew")

    # ── public helpers ──

    def update_stats(self, text: str) -> None:
        self.lbl_stats.configure(text=text)

    def update_image(self, ctk_img) -> None:
        self.surface.configure(image=ctk_img, text="")

    def clear_image(self) -> None:
        self.surface.configure(
            image="",
            text="\U0001f3ac  Presiona  \u25b6 Iniciar  (F5)  para previsualizar el escritorio en vivo",
        )

    # ── collapse / expand ──

    def _toggle(self) -> None:
        if self._expanded:
            self.surface.grid_remove()
            self.btn_toggle.configure(text="\u25bc")
            self._expanded = False
        else:
            self.surface.grid()
            self.btn_toggle.configure(text="\u25b2")
            self._expanded = True


class RTDADesktopApp(ctk.CTk):
    """Clean, modular, scalable CustomTkinter Desktop Application for RTDA."""

    def __init__(
        self,
        config: CaptureConfig | None = None,
        *,
        enable_perception_tools: bool = False,
        show_capture_overlay: bool = True,
        show_floating_control: bool = True,
    ) -> None:
        apply_theme_settings()
        super().__init__()

        self.title("\U0001f31f RTDA Desktop Control Surface")
        self.geometry("1200x740")
        self.minsize(1040, 640)
        self.configure(fg_color=T["background_app"])

        self._base_config = config or CaptureConfig()
        self._enable_perception_tools = enable_perception_tools
        self._show_capture_overlay = show_capture_overlay
        self._show_floating_control = show_floating_control

        self._bridge = DesktopRuntimeBridge(
            self._base_config,
            enable_perception_tools=self._enable_perception_tools,
        )
        self._ai_runner = DesktopAiRunner()

        self._setup_window_icon()
        self._build_ui()

        self._floating = None
        if self._show_floating_control:
            try:
                self._floating = RTDAFloatingControl(
                    on_open=self.restore_window,
                    on_start=self.start_capture,
                    on_pause=self.pause_or_resume,
                    on_stop=self.stop_capture,
                    on_quit=self.quit_app,
                )
                self._floating.show()
            except Exception:
                self._floating = None

        self._load_monitors()
        self._update_loop()

    def _setup_window_icon(self) -> None:
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(True, photo)
            except Exception:
                pass

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ══════════════════════════════════
        #   SIDEBAR
        # ══════════════════════════════════
        self.sidebar = ctk.CTkFrame(
            self, width=355, corner_radius=16,
            fg_color=T["background_card"],
            border_color=T["border"], border_width=1,
        )
        self.sidebar.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # ── Header: logo badge + title ──
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        logo_badge = ctk.CTkFrame(
            header_frame, width=38, height=38, corner_radius=10,
            fg_color=T["accent_emerald_dark"],
            border_color=T["accent_emerald"], border_width=1,
        )
        logo_badge.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="w")
        logo_badge.grid_propagate(False)
        ctk.CTkLabel(logo_badge, text="\U0001f31f", font=ctk.CTkFont(size=18)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(
            header_frame, text="RTDA Agent OS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=T["accent_emerald"],
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            header_frame, text="Desktop Control Surface  v3.0",
            font=ctk.CTkFont(size=10),
            text_color=T["text_secondary"],
        ).grid(row=1, column=1, sticky="w")

        # ── Status Pill ──
        self.status_pill = StatusPill(self.sidebar)
        self.status_pill.grid(row=1, column=0, padx=12, pady=(4, 4), sticky="ew")

        # ── Icon + Text Tab Selector ──
        self.tab_selector = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["📷 Captura", "📊 Métricas", "🔌 MCP", "🤖 IA", "⚙️ Config"],
            command=self._show_tab,
            selected_color=T["accent_emerald"],
            unselected_color="#17253D",
            selected_hover_color=T["accent_emerald_hover"],
            fg_color="#0D1B2E",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=10,
        )
        self.tab_selector.set("🤖 IA")
        self.tab_selector.grid(row=2, column=0, padx=12, pady=(6, 4), sticky="ew")

        # ── Tab Container ──
        self.tab_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tab_container.grid(row=3, column=0, padx=12, pady=(4, 4), sticky="nsew")
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self.panel_capture = CapturePanel(self.tab_container)
        self.panel_metrics = MetricsPanel(self.tab_container)
        self.panel_mcp = McpPanel(self.tab_container)
        self.panel_ai = AiPanel(self.tab_container, on_ask=self.ask_ai)
        self.panel_settings = SettingsPanel(
            self.tab_container,
            on_toggle_overlay=self._refresh_overlay,
            on_toggle_floating=self._toggle_floating,
            show_capture_overlay=self._show_capture_overlay,
            show_floating_control=self._show_floating_control,
            enable_perception_tools=self._enable_perception_tools,
        )

        self._tab_map = {
            "📷 Captura": self.panel_capture,
            "📊 Métricas": self.panel_metrics,
            "🔌 MCP": self.panel_mcp,
            "🤖 IA": self.panel_ai,
            "⚙️ Config": self.panel_settings,
        }
        self._show_tab("🤖 IA")

        # ── Action Bar ──
        self.action_bar = ActionBar(
            self.sidebar,
            on_start=self.start_capture,
            on_pause=self.pause_or_resume,
            on_stop=self.stop_capture,
            on_uia=self.inspect_uia,
            enable_perception_tools=self._enable_perception_tools,
        )
        self.action_bar.grid(row=4, column=0, padx=12, pady=(4, 10), sticky="ew")

        # ══════════════════════════════════
        #   MAIN CONTENT
        # ══════════════════════════════════
        self.main_frame = ctk.CTkFrame(
            self, corner_radius=16,
            fg_color=T["background_main"],
            border_color=T["border"], border_width=1,
        )
        self.main_frame.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # ── Collapsible Preview ──
        self.preview = CollapsiblePreview(self.main_frame)
        self.preview.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

    def _show_tab(self, name: str) -> None:
        for p in self._tab_map.values():
            p.grid_forget()
        if name in self._tab_map:
            self._tab_map[name].grid(row=0, column=0, sticky="nsew")

    # ── RUNTIME CONTROLS ──
    def start_capture(self) -> None:
        self._bridge.start(
            base_config=self._base_config,
            backend="dxgi",
            target_fps=60,
            monitor_index=0,
            window_title=None,
            region=None,
            show_border=self.panel_settings.chk_overlay.get() == 1,
        )
        self._update_runtime_status()

    def stop_capture(self) -> None:
        self._bridge.stop()
        self.preview.clear_image()
        self._update_runtime_status()

    def pause_or_resume(self) -> None:
        self._bridge.pause_or_resume()
        self._update_runtime_status()

    def inspect_uia(self) -> None:
        res = self._bridge.inspect_uia(window_title=None)
        if res:
            self.panel_ai.set_output(f"🔍 {res}")

    def ask_ai(self) -> None:
        provider = self.panel_ai.opt_provider.get()
        model = self.panel_ai.entry_model.get()
        token = self.panel_ai.entry_token.get()
        prompt_text = self.panel_ai.txt_prompt.get("1.0", "end").strip()

        if not prompt_text:
            return

        cfg = AIClientConfig(provider=provider, api_key=token, model=model)
        frame = self._bridge.latest_frame()
        stats = self._bridge.metrics()
        from desktop.ai_bridge import build_ai_system_prompt

        system_prompt = build_ai_system_prompt(backend="dxgi", stats=stats, frame=frame)

        self.panel_ai.set_busy(True)
        self.panel_ai.set_output("🧠 Procesando respuesta de IA...")
        self._ai_runner.submit(cfg, prompt_text, system_prompt, frame)

    def _refresh_overlay(self) -> None:
        self._bridge.refresh_overlay(self.panel_settings.chk_overlay.get() == 1)

    def _toggle_floating(self) -> None:
        if self.panel_settings.chk_floating.get() == 1:
            if self._floating is None:
                try:
                    self._floating = RTDAFloatingControl(
                        on_open=self.restore_window,
                        on_start=self.start_capture,
                        on_pause=self.pause_or_resume,
                        on_stop=self.stop_capture,
                        on_quit=self.quit_app,
                    )
                except Exception:
                    pass
            if self._floating is not None:
                self._floating.show()
        else:
            if self._floating is not None:
                self._floating.hide()

    def restore_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self) -> None:
        self._bridge.shutdown()
        if self._floating is not None:
            self._floating.shutdown()
        self.destroy()

    def _update_runtime_status(self) -> None:
        running = self._bridge.running
        paused = self._bridge.paused

        if running and paused:
            self.status_pill.set_state("paused")
        elif running:
            self.status_pill.set_state("active")
        else:
            self.status_pill.set_state("idle")

        self.action_bar.set_running_state(running=running, paused=paused)

        stats = self._bridge.metrics()
        if self._floating is not None:
            self._floating.set_status(
                running=running,
                paused=paused,
                fps=stats.capture_fps,
                resolution=f"{stats.latest_width}x{stats.latest_height}" if stats.latest_width else "-",
                latency_ms=stats.capture_latency_ms,
                dropped=stats.buffer_dropped_frames,
            )

    def _load_monitors(self) -> None:
        monitors = self._bridge.list_monitors()
        self.panel_capture.set_monitors(monitors)

    def destroy(self) -> None:
        if hasattr(self, "_timer_id") and self._timer_id:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None
        super().destroy()

    def _update_loop(self) -> None:
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        if self._bridge.running:
            frame = self._bridge.latest_frame()
            stats = self._bridge.metrics()
            self._update_runtime_status()

            res_str = f"{stats.latest_width}x{stats.latest_height}" if stats.latest_width else "-"
            self.panel_metrics.update_metrics(
                fps=stats.capture_fps,
                resolution=res_str,
                latency_ms=stats.capture_latency_ms,
                drops=stats.buffer_dropped_frames,
                frames=stats.frames_captured,
                errors=stats.backend_errors,
            )

            self.preview.update_stats(f"{stats.capture_fps:.1f} FPS  |  {res_str}  |  dxgi")

            if frame is not None and hasattr(frame, "data"):
                try:
                    img = Image.fromarray(frame.data[..., :3])
                    w = max(400, self.preview.surface.winfo_width())
                    h = max(300, self.preview.surface.winfo_height())
                    img.thumbnail((w, h), Image.Resampling.NEAREST)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                    self.preview.update_image(ctk_img)
                except Exception:
                    pass

        if self._ai_runner.has_result():
            res = self._ai_runner.take_result()
            self.panel_ai.set_busy(False)
            if res.error:
                self.panel_ai.set_output(f"❌ Error IA: {res.error}")
            else:
                self.panel_ai.set_output(f"🤖 {res.text}")

        try:
            if self.winfo_exists():
                self._timer_id = self.after(33, self._update_loop)
        except Exception:
            pass


def run_gui(
    config: CaptureConfig | None = None,
    *,
    enable_perception_tools: bool = False,
    show_capture_overlay: bool = True,
    show_floating_control: bool = True,
) -> int:
    app = RTDADesktopApp(
        config=config,
        enable_perception_tools=enable_perception_tools,
        show_capture_overlay=show_capture_overlay,
        show_floating_control=show_floating_control,
    )
    app.mainloop()
    return 0
