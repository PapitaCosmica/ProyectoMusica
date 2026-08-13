# -*- coding: utf-8 -*-
"""Ventana Principal de MusicSync Studio Pro (Optimizada con Hub Integrado, Reproductor On-Demand y Cierre Seguro)."""

import os
import sys
import threading
import customtkinter as ctk
from core.config import BASE_DIR, load_config, save_config
from core.task_manager import task_manager
from player.audio_engine import audio_player
from player.playlist_queue import playlist_queue

from .launcher_hub import LauncherHub
from .components.player_bar import PlayerBar
from .components.live_log_window import LiveLogWindow
from .components.tab_library import TabLibrary
from .components.tab_sync import TabSync
from .components.tab_usb import TabUsb
from .components.tab_diagnostics import TabDiagnostics
from .components.tab_playlists import TabPlaylists
from .components.tab_settings import TabSettings

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class MainWindow(ctk.CTk):
    def __init__(self, mode="hub"):
        super().__init__()
        self.mode = mode
        self.cached_song_count = 0
        self.is_scanning_count = False
        self.hub_frame = None
        self.tabview = None
        self.log_window = None

        config = load_config()
        self.player_enabled = config.get("player_enabled", False)

        self.title("🎵 MusicSync Studio Pro")
        self.geometry("1060x800")
        self.minsize(920, 620)

        # Manejador de cierre seguro
        self.protocol("WM_DELETE_WINDOW", self.on_app_close)

        self.setup_ui()
        self.async_update_song_count()
        self.start_header_loop()

    def setup_ui(self):
        # 1. Header Superior
        self.header_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#18181b")
        self.header_frame.pack(fill="x", padx=14, pady=(10, 6))

        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=8)

        self.lbl_title = ctk.CTkLabel(
            title_box, 
            text="🎵 MusicSync Studio Pro", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box, 
            text="Gestor de Música, Descargas, USB Universal y Salidas de Audio (Voicemeeter/Bluetooth/HDMI)", 
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa"
        )
        self.lbl_subtitle.pack(anchor="w")

        # Controles y Estadísticas en Header
        stats_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        stats_box.pack(side="right", padx=16, pady=8)

        # Botón para cambiar / volver al Hub de Herramientas
        self.btn_hub = ctk.CTkButton(
            stats_box,
            text="🚀 Menú",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=self.show_hub_view
        )
        self.btn_hub.pack(side="right", padx=(6, 0))

        # Botón para abrir la Ventana de Logs en Tiempo Real
        self.btn_open_logs = ctk.CTkButton(
            stats_box,
            text="📋 Logs",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=self.open_live_logs
        )
        self.btn_open_logs.pack(side="right", padx=(6, 0))

        # Interruptor para Encender / Apagar el Reproductor
        self.switch_player = ctk.CTkSwitch(
            stats_box,
            text="🎵 Reproductor",
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color="#10b981",
            command=self.toggle_player_switch
        )
        if self.player_enabled:
            self.switch_player.select()
        else:
            self.switch_player.deselect()
        self.switch_player.pack(side="right", padx=(8, 0))

        self.badge_status = ctk.CTkLabel(
            stats_box,
            text="🟢 LISTO / INACTIVO",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#27272a",
            text_color="#10b981",
            corner_radius=8,
            padx=10,
            pady=4
        )
        self.badge_status.pack(side="right", padx=6)

        self.lbl_song_count = ctk.CTkLabel(
            stats_box,
            text="Canciones: ...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f4f4f5"
        )
        self.lbl_song_count.pack(side="right", padx=10)

        # 2. Contenedor Central Dinámico
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # 3. Barra de Reproducción Inferior Persistente (Solo si está encendido)
        self.player_bar = PlayerBar(self, on_track_change_callback=self.on_player_track_change)

        if self.mode == "hub":
            self.show_hub_view()
        else:
            self.build_mode_view(self.mode)

        if self.player_enabled:
            audio_player.init_audio_system()
            self.player_bar.pack(fill="x", padx=14, pady=(0, 10))

    def show_hub_view(self):
        """Muestra el Launcher Hub dentro de la ventana."""
        if self.tabview:
            self.tabview.pack_forget()
        if self.hub_frame is None:
            self.hub_frame = LauncherHub(self.main_container, on_select_mode_callback=self.switch_mode)
        self.hub_frame.pack(fill="both", expand=True)
        self.title("🚀 MusicSync Studio Pro - Selector de Herramientas")

    def switch_mode(self, mode):
        """Cambia dinámicamente de modo sin reiniciar la ventana."""
        self.mode = mode
        if self.hub_frame:
            self.hub_frame.pack_forget()
        self.build_mode_view(mode)

    def build_mode_view(self, mode):
        if self.tabview:
            self.tabview.destroy()

        title_suffix = " (Modo Ultra Ligero)" if mode in ["sync_usb", "usb_only"] else ""
        self.title(f"🎵 MusicSync Studio Pro{title_suffix}")

        self.tabview = ctk.CTkTabview(self.main_container, corner_radius=12, fg_color="#18181b")
        self.tabview.pack(fill="both", expand=True)

        if mode == "full":
            self.t_library = self.tabview.add("🎵 Biblioteca Local")
            self.t_sync = self.tabview.add("🎛️ Centro de Control")
            self.t_usb = self.tabview.add("💾 Memoria USB")
            self.t_diagnostics = self.tabview.add("🔍 Inspector & Duplicados")
            self.t_playlists = self.tabview.add("📋 Playlists & Fuentes")
            self.t_settings = self.tabview.add("⚙️ Rutas & Configuración")

            self.comp_library = TabLibrary(self.t_library, on_play_track_callback=self.play_track_from_library)
            self.comp_library.pack(fill="both", expand=True)

            self.comp_sync = TabSync(self.t_sync, on_sync_finished=self.on_data_updated)
            self.comp_sync.pack(fill="both", expand=True)

            self.comp_usb = TabUsb(self.t_usb, on_usb_action_finished=self.on_data_updated)
            self.comp_usb.pack(fill="both", expand=True)

            self.comp_diagnostics = TabDiagnostics(self.t_diagnostics)
            self.comp_diagnostics.pack(fill="both", expand=True)

            self.comp_playlists = TabPlaylists(self.t_playlists)
            self.comp_playlists.pack(fill="both", expand=True)

            self.comp_settings = TabSettings(self.t_settings, on_reorganize_finished=self.on_data_updated)
            self.comp_settings.pack(fill="both", expand=True)
        elif mode == "usb_only":
            self.t_usb = self.tabview.add("💾 Memoria USB & Formateo")
            self.t_diagnostics = self.tabview.add("🔍 Inspector de Almacenamiento")

            self.comp_usb = TabUsb(self.t_usb, on_usb_action_finished=self.on_data_updated)
            self.comp_usb.pack(fill="both", expand=True)

            self.comp_diagnostics = TabDiagnostics(self.t_diagnostics)
            self.comp_diagnostics.pack(fill="both", expand=True)
        else:
            # Modo Rápido / Ultra Ligero (Sync, USB, Diagnósticos, Playlists, Ajustes)
            self.t_sync = self.tabview.add("🎛️ Centro de Control")
            self.t_usb = self.tabview.add("💾 Memoria USB")
            self.t_diagnostics = self.tabview.add("🔍 Inspector & Duplicados")
            self.t_playlists = self.tabview.add("📋 Playlists & Fuentes")
            self.t_settings = self.tabview.add("⚙️ Rutas & Configuración")

            self.comp_sync = TabSync(self.t_sync, on_sync_finished=self.on_data_updated)
            self.comp_sync.pack(fill="both", expand=True)

            self.comp_usb = TabUsb(self.t_usb, on_usb_action_finished=self.on_data_updated)
            self.comp_usb.pack(fill="both", expand=True)

            self.comp_diagnostics = TabDiagnostics(self.t_diagnostics)
            self.comp_diagnostics.pack(fill="both", expand=True)

            self.comp_playlists = TabPlaylists(self.t_playlists)
            self.comp_playlists.pack(fill="both", expand=True)

            self.comp_settings = TabSettings(self.t_settings, on_reorganize_finished=self.on_data_updated)
            self.comp_settings.pack(fill="both", expand=True)

    def open_live_logs(self):
        """Abre o trae al frente la ventana de logs en tiempo real."""
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = LiveLogWindow(self)
        else:
            self.log_window.lift()
            self.log_window.focus()

    def toggle_player_switch(self):
        self.player_enabled = bool(self.switch_player.get())
        config = load_config()
        config["player_enabled"] = self.player_enabled
        save_config(config)

        if self.player_enabled:
            audio_player.init_audio_system()
            self.player_bar.pack(fill="x", padx=14, pady=(0, 10))
            self.player_bar.update_device_list()
        else:
            audio_player.stop()
            audio_player.unload_audio_system()
            self.player_bar.pack_forget()

    def play_track_from_library(self, filepath):
        if not self.player_enabled:
            self.switch_player.select()
            self.toggle_player_switch()
        self.player_bar.play_track(filepath)

    def on_player_track_change(self, meta):
        pass

    def on_data_updated(self):
        self.async_update_song_count()
        if hasattr(self, 'comp_library'):
            self.comp_library.async_refresh_library(force=True)
        if hasattr(self, 'comp_diagnostics'):
            self.comp_diagnostics.async_refresh_diagnostics()

    def async_update_song_count(self):
        if self.is_scanning_count:
            return
        self.is_scanning_count = True

        def worker():
            config = load_config()
            target_dir = os.path.join(BASE_DIR, config.get("target_folder", "Musica"))
            count = 0
            if os.path.exists(target_dir):
                try:
                    with os.scandir(target_dir) as it:
                        for entry in it:
                            if entry.is_file() and entry.name.lower().endswith(".mp3"):
                                count += 1
                            elif entry.is_dir():
                                count += sum(1 for _, _, f in os.walk(entry.path) for x in f if x.lower().endswith(".mp3"))
                except Exception:
                    pass
            self.cached_song_count = count
            self.after(0, lambda: self.lbl_song_count.configure(text=f"Canciones: {count}"))
            self.is_scanning_count = False

        threading.Thread(target=worker, daemon=True).start()

    def start_header_loop(self):
        summary, num = task_manager.get_active_tasks_summary()
        if num > 0:
            self.badge_status.configure(text=f"🔄 {num} TAREA(S): {summary[:25].upper()}", text_color="#f59e0b", fg_color="#3f2d12")
        else:
            self.badge_status.configure(text="🟢 LISTO / INACTIVO", text_color="#10b981", fg_color="#27272a")

        self.after(2000, self.start_header_loop)

    def on_app_close(self):
        """Cierre ordenado y limpio de la aplicación."""
        try:
            audio_player.stop()
            audio_player.unload_audio_system()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)
