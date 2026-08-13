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
from desktop.ui.theme import apply_theme_settings


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

        self.title("🌟 RTDA Desktop Control Surface")
        self.geometry("1160x700")
        self.minsize(1020, 620)
        self.configure(fg_color="#080C14")

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

        self._floating = RTDAFloatingControl(
            on_open=self.restore_window,
            on_start=self.start_capture,
            on_pause=self.pause_or_resume,
            on_stop=self.stop_capture,
            on_quit=self.quit_app,
        )
        if self._show_floating_control:
            self._floating.show()

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

        # ── SIDEBAR FRAME ──
        self.sidebar = ctk.CTkFrame(self, width=340, corner_radius=16, fg_color="#0F172A", border_color="#1E293B", border_width=1)
        self.sidebar.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=12, pady=(14, 6), sticky="ew")
        
        lbl_title = ctk.CTkLabel(header_frame, text="🌟 RTDA", font=ctk.CTkFont(size=22, weight="bold"), text_color="#10B981")
        lbl_title.pack(anchor="w")
        lbl_subtitle = ctk.CTkLabel(header_frame, text="🔌 Desktop AgentOS v3.0", font=ctk.CTkFont(size=11), text_color="#94A3B8")
        lbl_subtitle.pack(anchor="w")

        # Status Pill Component
        self.status_pill = StatusPill(self.sidebar)
        self.status_pill.grid(row=1, column=0, padx=12, pady=4, sticky="ew")

        # Tab Selector
        self.tab_selector = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["Captura", "Métricas", "MCP", "IA", "Config"],
            command=self._show_tab,
            selected_color="#10B981",
            unselected_color="#1E293B",
            selected_hover_color="#059669",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
        )
        self.tab_selector.set("IA")
        self.tab_selector.grid(row=2, column=0, padx=12, pady=8, sticky="ew")

        # Tab Views Container
        self.tab_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tab_container.grid(row=3, column=0, padx=12, pady=4, sticky="nsew")
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

        self._show_tab("IA")

        # Action Bar Component
        self.action_bar = ActionBar(
            self.sidebar,
            on_start=self.start_capture,
            on_pause=self.pause_or_resume,
            on_stop=self.stop_capture,
            on_uia=self.inspect_uia,
            enable_perception_tools=self._enable_perception_tools,
        )
        self.action_bar.grid(row=4, column=0, padx=12, pady=12, sticky="ew")

        # ── PREVIEW FRAME ──
        self.main_frame = ctk.CTkFrame(self, corner_radius=16, fg_color="#090D16", border_color="#1E293B", border_width=1)
        self.main_frame.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        preview_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        preview_header.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        
        lbl_preview_title = ctk.CTkLabel(preview_header, text="🖼️ Vista de Pantalla en Tiempo Real", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        lbl_preview_title.pack(side="left")

        self.preview_stats_label = ctk.CTkLabel(preview_header, text="Listo | dxgi | 0.0 FPS", font=ctk.CTkFont(size=11), text_color="#38BDF8")
        self.preview_stats_label.pack(side="right")

        self.preview_surface = ctk.CTkLabel(
            self.main_frame,
            text="🎬 Presiona '▶ Iniciar' (F5) para previsualizar el escritorio en vivo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#64748B",
            fg_color="#020617",
            corner_radius=12,
        )
        self.preview_surface.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

    def _show_tab(self, name: str) -> None:
        for p in (self.panel_capture, self.panel_metrics, self.panel_mcp, self.panel_ai, self.panel_settings):
            p.grid_forget()

        mapping = {
            "Captura": self.panel_capture,
            "Métricas": self.panel_metrics,
            "MCP": self.panel_mcp,
            "IA": self.panel_ai,
            "Config": self.panel_settings,
        }
        if name in mapping:
            mapping[name].grid(row=0, column=0, sticky="nsew")

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
        self.preview_surface.configure(image="", text="🎬 Presiona '▶ Iniciar' (F5) para previsualizar el escritorio en vivo")
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
        system_prompt = f"RTDA AgentOS Live Context. FPS: {stats.capture_fps:.1f}, Frames: {stats.frames_captured}."

        self.panel_ai.set_busy(True)
        self.panel_ai.set_output("🧠 Procesando respuesta de IA...")
        self._ai_runner.submit(cfg, prompt_text, system_prompt, frame)

    def _refresh_overlay(self) -> None:
        self._bridge.refresh_overlay(self.panel_settings.chk_overlay.get() == 1)

    def _toggle_floating(self) -> None:
        if self.panel_settings.chk_floating.get() == 1:
            self._floating.show()
        else:
            self._floating.hide()

    def restore_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self) -> None:
        self._bridge.shutdown()
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

    def _update_loop(self) -> None:
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

            self.preview_stats_label.configure(text=f"{stats.capture_fps:.1f} FPS | {res_str} | dxgi")

            if frame is not None and hasattr(frame, "data"):
                try:
                    img = Image.fromarray(frame.data[..., :3])
                    w = max(400, self.preview_surface.winfo_width())
                    h = max(300, self.preview_surface.winfo_height())
                    img.thumbnail((w, h), Image.Resampling.NEAREST)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                    self.preview_surface.configure(image=ctk_img, text="")
                except Exception:
                    pass

        if self._ai_runner.has_result():
            res = self._ai_runner.take_result()
            self.panel_ai.set_busy(False)
            if res.error:
                self.panel_ai.set_output(f"❌ Error IA: {res.error}")
            else:
                self.panel_ai.set_output(f"🤖 {res.text}")

        self.after(33, self._update_loop)


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
