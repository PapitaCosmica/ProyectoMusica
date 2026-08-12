# -*- coding: utf-8 -*-
"""Ventana Principal de MusicSync Studio Pro (Optimizada con Reproductor On-Demand y Modos)."""

import os
import threading
import customtkinter as ctk
from core.config import BASE_DIR, load_config, save_config
from core.task_manager import task_manager
from player.audio_engine import audio_player
from player.playlist_queue import playlist_queue

from .components.player_bar import PlayerBar
from .components.tab_library import TabLibrary
from .components.tab_sync import TabSync
from .components.tab_usb import TabUsb
from .components.tab_diagnostics import TabDiagnostics
from .components.tab_playlists import TabPlaylists
from .components.tab_settings import TabSettings

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class MainWindow(ctk.CTk):
    def __init__(self, mode="full"):
        super().__init__()
        self.mode = mode
        self.cached_song_count = 0
        self.is_scanning_count = False

        config = load_config()
        self.player_enabled = config.get("player_enabled", False)

        title_suffix = " (Modo Ultra Ligero)" if mode == "sync_usb" else ""
        self.title(f"🎵 MusicSync Studio Pro{title_suffix}")
        self.geometry("1040x780")
        self.minsize(920, 600)

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
        self.switch_player.pack(side="right", padx=(10, 0))

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

        # 2. Pestañas Principales
        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color="#18181b")
        self.tabview.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        if self.mode == "full":
            self.t_library = self.tabview.add("🎵 Biblioteca Local")
            self.t_sync = self.tabview.add("🎛️ Centro de Control")
            self.t_usb = self.tabview.add("💾 Memoria USB")
            self.t_diagnostics = self.tabview.add("📊 Diagnóstico & Almacenamiento")
            self.t_playlists = self.tabview.add("📋 Playlists & Fuentes")
            self.t_settings = self.tabview.add("⚙️ Ajustes & Estructura")

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
        else:
            # Modo Ligero (Solo Sync, USB y Diagnóstico)
            self.t_sync = self.tabview.add("🎛️ Centro de Control")
            self.t_usb = self.tabview.add("💾 Memoria USB")
            self.t_diagnostics = self.tabview.add("📊 Diagnóstico & Almacenamiento")
            self.t_playlists = self.tabview.add("📋 Playlists & Fuentes")
            self.t_settings = self.tabview.add("⚙️ Ajustes & Estructura")

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

        # 3. Barra de Reproducción Inferior Persistente (Solo si está encendido)
        self.player_bar = PlayerBar(self, on_track_change_callback=self.on_player_track_change)
        if self.player_enabled:
            audio_player.init_audio_system()
            self.player_bar.pack(fill="x", padx=14, pady=(0, 10))

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
        # Actualización de insignias de tareas (100% en memoria, cero I/O de disco)
        summary, num = task_manager.get_active_tasks_summary()
        if num > 0:
            self.badge_status.configure(text=f"🔄 {num} TAREA(S): {summary[:25].upper()}", text_color="#f59e0b", fg_color="#3f2d12")
        else:
            self.badge_status.configure(text="🟢 LISTO / INACTIVO", text_color="#10b981", fg_color="#27272a")

        self.after(2000, self.start_header_loop)
