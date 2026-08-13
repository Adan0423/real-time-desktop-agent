from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import customtkinter as ctk
from PIL import Image, ImageTk

from rtda.capture.interface import CaptureConfig, MonitorInfo
from rtda.capture.region import Region
from desktop.ai_bridge import DesktopAiRunner
from desktop.ai.client import AI_PROVIDERS, AIClientConfig, default_model, env_var_for_provider
from desktop.floating import RTDAFloatingControl
from desktop.runtime_bridge import DesktopRuntimeBridge

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CaptureDashboardCTK(ctk.CTk):
    """Modern CustomTkinter desktop control surface for RTDA AgentOS."""

    def __init__(
        self,
        config: CaptureConfig | None = None,
        *,
        enable_perception_tools: bool = False,
        show_capture_overlay: bool = True,
        show_floating_control: bool = True,
    ) -> None:
        super().__init__()

        self.title("🌟 RTDA Desktop Control Surface (CustomTkinter)")
        self.geometry("1160x700")
        self.minsize(1020, 620)
        self.configure(fg_color="#080C14")

        self._base_config = config or CaptureConfig()
        self._enable_perception_tools = enable_perception_tools
        self._show_capture_overlay = show_capture_overlay
        self._show_floating_control = show_floating_control
        self._monitors: list[MonitorInfo] = []

        self._bridge = DesktopRuntimeBridge(
            self._base_config,
            enable_perception_tools=self._enable_perception_tools,
        )
        self._ai_runner = DesktopAiRunner()
        self._ai_last_query = 0.0

        self._setup_window_icon()
        self._build_layout()

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
        icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                self.wm_iconphoto(True, photo)
            except Exception:
                pass

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── SIDEBAR FRAME ──
        self.sidebar = ctk.CTkFrame(self, width=340, corner_radius=16, fg_color="#0F172A", border_color="#1E293B", border_width=1)
        self.sidebar.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # 1. Header
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=12, pady=(14, 6), sticky="ew")
        
        self.app_title = ctk.CTkLabel(header_frame, text="🌟 RTDA", font=ctk.CTkFont(size=22, weight="bold"), text_color="#10B981")
        self.app_title.pack(anchor="w")
        self.app_subtitle = ctk.CTkLabel(header_frame, text="🔌 Desktop AgentOS v3.0", font=ctk.CTkFont(size=11), text_color="#94A3B8")
        self.app_subtitle.pack(anchor="w")

        # 2. Status Badge Pill
        self.status_pill = ctk.CTkLabel(
            self.sidebar,
            text="● Extension Local Lista",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#34D399",
            fg_color="#065F46",
            corner_radius=10,
            height=28,
        )
        self.status_pill.grid(row=1, column=0, padx=12, pady=4, sticky="ew")

        # 3. Tab Selector
        self.tab_selector = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["Captura", "Métricas", "MCP", "IA", "Config"],
            command=self._on_tab_changed,
            selected_color="#10B981",
            unselected_color="#1E293B",
            selected_hover_color="#059669",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
        )
        self.tab_selector.set("IA")
        self.tab_selector.grid(row=2, column=0, padx=12, pady=8, sticky="ew")

        # 4. Tab Views Stack Container
        self.tab_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tab_container.grid(row=3, column=0, padx=12, pady=4, sticky="nsew")
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self._build_captura_tab()
        self._build_metricas_tab()
        self._build_mcp_tab()
        self._build_ia_tab()
        self._build_config_tab()

        self._show_tab("IA")

        # 5. Bottom Action Bar Grid (2x2)
        action_frame = ctk.CTkFrame(self.sidebar, fg_color="#020617", corner_radius=12, border_color="#1E293B", border_width=1)
        action_frame.grid(row=4, column=0, padx=12, pady=12, sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(
            action_frame, text="▶ Iniciar", command=self.start_capture,
            fg_color="#065F46", hover_color="#047857", text_color="#ECFDF5", font=ctk.CTkFont(size=12, weight="bold"), height=34
        )
        self.btn_start.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.btn_pause = ctk.CTkButton(
            action_frame, text="⏸ Pausar", command=self.pause_or_resume, state="disabled",
            fg_color="#78350F", hover_color="#92400E", text_color="#FFFBEB", font=ctk.CTkFont(size=12, weight="bold"), height=34
        )
        self.btn_pause.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.btn_stop = ctk.CTkButton(
            action_frame, text="⏹ Detener", command=self.stop_capture, state="disabled",
            fg_color="#7F1D1D", hover_color="#991B1B", text_color="#FEF2F2", font=ctk.CTkFont(size=12, weight="bold"), height=34
        )
        self.btn_stop.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self.btn_uia = ctk.CTkButton(
            action_frame, text="🔍 UIA", command=self.inspect_uia, state="normal" if enable_perception_tools else "disabled",
            fg_color="#0284C7", hover_color="#0369A1", text_color="#F0F9FF", font=ctk.CTkFont(size=12, weight="bold"), height=34
        )
        self.btn_uia.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        # ── MAIN PREVIEW FRAME ──
        self.main_frame = ctk.CTkFrame(self, corner_radius=16, fg_color="#090D16", border_color="#1E293B", border_width=1)
        self.main_frame.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Preview Header Bar
        preview_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        preview_header.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="ew")
        
        lbl_preview_title = ctk.CTkLabel(preview_header, text="🖼️ Vista de Pantalla en Tiempo Real", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        lbl_preview_title.pack(side="left")

        self.preview_stats_label = ctk.CTkLabel(preview_header, text="Listo | dxgi | 0.0 FPS", font=ctk.CTkFont(size=11), text_color="#38BDF8")
        self.preview_stats_label.pack(side="right")

        # Video Preview Surface
        self.preview_surface = ctk.CTkLabel(
            self.main_frame,
            text="🎬 Presiona '▶ Iniciar' (F5) para previsualizar el escritorio en vivo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#64748B",
            fg_color="#020617",
            corner_radius=12,
        )
        self.preview_surface.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")

    # ── TAB BUILDERS ──
    def _build_captura_tab(self) -> None:
        self.tab_captura = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.tab_captura.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(self.tab_captura, text="📷 Configuración de Captura", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        lbl.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(self.tab_captura, text="Monitor Objetivo:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.opt_monitor = ctk.CTkOptionMenu(self.tab_captura, values=["Monitor 0 (Principal)"], fg_color="#1E293B", button_color="#0F172A")
        self.opt_monitor.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(self.tab_captura, text="Tasa de Frames (FPS):", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.opt_fps = ctk.CTkOptionMenu(self.tab_captura, values=["60 FPS (Baja Latencia)", "30 FPS", "15 FPS"], fg_color="#1E293B", button_color="#0F172A")
        self.opt_fps.pack(fill="x", pady=(2, 10))

    def _build_metricas_tab(self) -> None:
        self.tab_metricas = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.tab_metricas.grid_columnconfigure((0, 1), weight=1)

        self.metric_labels: dict[str, ctk.CTkLabel] = {}
        for idx, (key, title) in enumerate([
            ("fps", "⚡ FPS"),
            ("resolution", "📐 Resolución"),
            ("latency", "⏱️ Latencia"),
            ("drops", "⚠️ Drops"),
            ("frames", "🎞️ Frames"),
            ("errors", "❌ Errores"),
        ]):
            card = ctk.CTkFrame(self.tab_metricas, fg_color="#020617", corner_radius=8, border_color="#1E293B", border_width=1)
            card.grid(row=idx // 2, column=idx % 2, padx=4, pady=4, sticky="ew")
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10), text_color="#94A3B8").pack(anchor="w", padx=8, pady=(4, 0))
            val_lbl = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=15, weight="bold"), text_color="#38BDF8")
            val_lbl.pack(anchor="w", padx=8, pady=(0, 4))
            self.metric_labels[key] = val_lbl

    def _build_mcp_tab(self) -> None:
        self.tab_mcp = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        ctk.CTkLabel(self.tab_mcp, text="🔌 Servidor MCP Integrado", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC").pack(anchor="w")
        mcp_box = ctk.CTkTextbox(self.tab_mcp, height=180, fg_color="#020617", text_color="#34D399", font=ctk.CTkFont(family="Consolas", size=11))
        mcp_box.pack(fill="both", expand=True, pady=6)
        mcp_box.insert("1.0", "● Servidor MCP activo en puerto local\n● Herramientas registradas: 13 (observe_state, click, type, hotkey, screenshot, uia_snapshot)")
        mcp_box.configure(state="disabled")

    def _build_ia_tab(self) -> None:
        self.tab_ia = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.tab_ia.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.tab_ia, text="🤖 Proveedor IA:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.opt_provider = ctk.CTkOptionMenu(
            self.tab_ia,
            values=list(AI_PROVIDERS),
            command=self._on_provider_changed,
            fg_color="#1E293B",
            button_color="#0F172A",
            height=30,
        )
        self.opt_provider.set("groq")
        self.opt_provider.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(self.tab_ia, text="⚡ Modelo:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.entry_model = ctk.CTkEntry(self.tab_ia, height=30, fg_color="#020617", border_color="#1E293B")
        self.entry_model.insert(0, default_model("groq"))
        self.entry_model.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(self.tab_ia, text="🔑 Token API / Clave:", font=ctk.CTkFont(size=11), text_color="#94A3B8").pack(anchor="w")
        self.entry_token = ctk.CTkEntry(self.tab_ia, height=30, show="•", fg_color="#020617", border_color="#1E293B")
        self.entry_token.pack(fill="x", pady=(2, 4))
        self._sync_token("groq")

        self.lbl_env_status = ctk.CTkLabel(self.tab_ia, text="● API Key detectada en .env", font=ctk.CTkFont(size=10, weight="bold"), text_color="#34D399")
        self.lbl_env_status.pack(anchor="w", pady=(0, 6))

        self.txt_prompt = ctk.CTkTextbox(self.tab_ia, height=75, fg_color="#020617", border_color="#1E293B", border_width=1)
        self.txt_prompt.pack(fill="x", pady=(0, 6))
        self.txt_prompt.insert("1.0", "💡 Consulta en vivo sobre el escritorio...")

        self.btn_ask = ctk.CTkButton(
            self.tab_ia,
            text="✨ Consultar IA",
            command=self.ask_ai,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#ECFDF5",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
        )
        self.btn_ask.pack(fill="x", pady=(0, 6))

        self.txt_output = ctk.CTkTextbox(self.tab_ia, height=90, fg_color="#020617", text_color="#38BDF8", font=ctk.CTkFont(size=11))
        self.txt_output.pack(fill="both", expand=True)
        self.txt_output.insert("1.0", "🤖 IA: esperando prompt")
        self.txt_output.configure(state="disabled")

    def _build_config_tab(self) -> None:
        self.tab_config = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        ctk.CTkLabel(self.tab_config, text="⚙️ Opciones del Sistema", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC").pack(anchor="w", pady=(0, 6))

        self.chk_overlay = ctk.CTkCheckBox(self.tab_config, text="Marco de Captura Verde (Overlay)", command=self._refresh_overlay)
        if self._show_capture_overlay:
            self.chk_overlay.select()
        self.chk_overlay.pack(anchor="w", pady=6)

        self.chk_floating = ctk.CTkCheckBox(self.tab_config, text="Widget Flotante (Always-on-Top)", command=self._toggle_floating)
        if self._show_floating_control:
            self.chk_floating.select()
        self.chk_floating.pack(anchor="w", pady=6)

        self.chk_changes = ctk.CTkCheckBox(self.tab_config, text="Detección de Cambios (OpenCV ROI)")
        if self._enable_perception_tools:
            self.chk_changes.select()
        self.chk_changes.pack(anchor="w", pady=6)

    # ── TAB SWITCHING ──
    def _on_tab_changed(self, value: str) -> None:
        self._show_tab(value)

    def _show_tab(self, name: str) -> None:
        for tab in (self.tab_captura, self.tab_metricas, self.tab_mcp, self.tab_ia, self.tab_config):
            tab.grid_forget()

        mapping = {
            "Captura": self.tab_captura,
            "Métricas": self.tab_metricas,
            "MCP": self.tab_mcp,
            "IA": self.tab_ia,
            "Config": self.tab_config,
        }
        if name in mapping:
            mapping[name].grid(row=0, column=0, sticky="nsew")

    # ── PROVIDER HELPERS ──
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

    # ── EVENT HANDLERS & RUNTIME ──
    def start_capture(self) -> None:
        selected_monitor = 0
        self._bridge.start(
            base_config=self._base_config,
            backend="dxgi",
            target_fps=60,
            monitor_index=selected_monitor,
            window_title=None,
            region=None,
            show_border=self.chk_overlay.get() == 1,
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
            self.txt_output.configure(state="normal")
            self.txt_output.delete("1.0", "end")
            self.txt_output.insert("1.0", f"🔍 {res}")
            self.txt_output.configure(state="disabled")

    def ask_ai(self) -> None:
        provider = self.opt_provider.get()
        model = self.entry_model.get()
        token = self.entry_token.get()
        prompt_text = self.txt_prompt.get("1.0", "end").strip()

        if not prompt_text:
            return

        cfg = AIClientConfig(provider=provider, api_key=token, model=model)
        frame = self._bridge.latest_frame()
        stats = self._bridge.metrics()
        system_prompt = f"RTDA AgentOS Live Context. FPS: {stats.capture_fps:.1f}, Frames: {stats.frames_captured}."

        self.btn_ask.configure(state="disabled", text="⏳ Consultando...")
        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", "🧠 Procesando respuesta de IA...")
        self.txt_output.configure(state="disabled")

        self._ai_runner.submit(cfg, prompt_text, system_prompt, frame)
        self._ai_last_query = time.perf_counter()

    def _refresh_overlay(self) -> None:
        self._bridge.refresh_overlay(self.chk_overlay.get() == 1)

    def _toggle_floating(self) -> None:
        if self.chk_floating.get() == 1:
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
            self.status_pill.configure(text="● Extension Pausada", fg_color="#451A03", text_color="#FBBF24")
            self.btn_start.configure(state="disabled")
            self.btn_pause.configure(state="normal", text="▶ Reanudar")
            self.btn_stop.configure(state="normal")
        elif running:
            self.status_pill.configure(text="● Extension Activa", fg_color="#065F46", text_color="#34D399")
            self.btn_start.configure(state="disabled")
            self.btn_pause.configure(state="normal", text="⏸ Pausar")
            self.btn_stop.configure(state="normal")
        else:
            self.status_pill.configure(text="● Extension Local Lista", fg_color="#0F172A", text_color="#94A3B8")
            self.btn_start.configure(state="normal")
            self.btn_pause.configure(state="disabled", text="⏸ Pausar")
            self.btn_stop.configure(state="disabled")

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
        self._monitors = self._bridge.list_monitors()
        if self._monitors:
            items = [f"Monitor {m.index} ({m.width}x{m.height})" for m in self._monitors]
            self.opt_monitor.configure(values=items)
            self.opt_monitor.set(items[0])

    def _update_loop(self) -> None:
        if self._bridge.running:
            frame = self._bridge.latest_frame()
            stats = self._bridge.metrics()
            self._update_runtime_status()

            # Update Metrics tab
            self.metric_labels["fps"].configure(text=f"{stats.capture_fps:.1f}")
            self.metric_labels["resolution"].configure(text=f"{stats.latest_width}x{stats.latest_height}" if stats.latest_width else "-")
            self.metric_labels["latency"].configure(text=f"{stats.capture_latency_ms:.1f} ms" if stats.capture_latency_ms else "-")
            self.metric_labels["drops"].configure(text=str(stats.buffer_dropped_frames))
            self.metric_labels["frames"].configure(text=str(stats.frames_captured))
            self.metric_labels["errors"].configure(text=str(stats.backend_errors))

            self.preview_stats_label.configure(text=f"{stats.capture_fps:.1f} FPS | {stats.latest_width}x{stats.latest_height} | dxgi")

            # Render video frame if available
            if frame is not None and hasattr(frame, "data"):
                try:
                    img = Image.fromarray(frame.data[..., :3])
                    # Fit to preview label size
                    w = max(400, self.preview_surface.winfo_width())
                    h = max(300, self.preview_surface.winfo_height())
                    img.thumbnail((w, h), Image.Resampling.NEAREST)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
                    self.preview_surface.configure(image=ctk_img, text="")
                except Exception:
                    pass

        # Poll AI runner result if pending
        if self._ai_runner.has_result():
            res = self._ai_runner.take_result()
            self.btn_ask.configure(state="normal", text="✨ Consultar IA")
            self.txt_output.configure(state="normal")
            self.txt_output.delete("1.0", "end")
            if res.error:
                self.txt_output.insert("1.0", f"❌ Error IA: {res.error}")
            else:
                self.txt_output.insert("1.0", f"🤖 {res.text}")
            self.txt_output.configure(state="disabled")

        self.after(33, self._update_loop)


def run_ctk_gui(
    config: CaptureConfig | None = None,
    *,
    enable_perception_tools: bool = False,
    show_capture_overlay: bool = True,
    show_floating_control: bool = True,
) -> int:
    app = CaptureDashboardCTK(
        config=config,
        enable_perception_tools=enable_perception_tools,
        show_capture_overlay=show_capture_overlay,
        show_floating_control=show_floating_control,
    )
    app.mainloop()
    return 0
