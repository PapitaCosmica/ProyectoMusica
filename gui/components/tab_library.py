# -*- coding: utf-8 -*-
"""Pestaña de Biblioteca Local con Selector de Carpeta y Reproducción Fluida."""

import os
import threading
from tkinter import filedialog
import customtkinter as ctk
from player.playlist_queue import playlist_queue
from core.config import load_config, save_config

class TabLibrary(ctk.CTkFrame):
    def __init__(self, master, on_play_track_callback=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_play_track_callback = on_play_track_callback
        self.all_tracks = []
        self.filtered_tracks = []
        self.page = 0
        self.page_size = 30

        self.setup_ui()
        self.async_refresh_library()

    def setup_ui(self):
        # 1. Barra de Selección de Carpeta Origen/Lectura
        folder_bar = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        folder_bar.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            folder_bar,
            text="📂 Carpeta a Reproducir:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10b981"
        ).pack(side="left", padx=(12, 6), pady=8)

        self.lbl_folder_path = ctk.CTkLabel(
            folder_bar,
            text=playlist_queue.get_current_library_folder()[:55],
            font=ctk.CTkFont(size=12),
            text_color="#e4e4e7",
            anchor="w"
        )
        self.lbl_folder_path.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_change_folder = ctk.CTkButton(
            folder_bar,
            text="📁 Cambiar Carpeta...",
            width=140,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.action_change_folder
        )
        self.btn_change_folder.pack(side="right", padx=10, pady=6)

        # 2. Barra con Buscador y Contador
        search_bar = ctk.CTkFrame(self, fg_color="#1e1e24", corner_radius=10)
        search_bar.pack(fill="x", padx=10, pady=4)

        self.entry_search = ctk.CTkEntry(
            search_bar, 
            placeholder_text="🔍 Buscar por canción, artista o álbum...", 
            height=36,
            font=ctk.CTkFont(size=13)
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=8)
        self.entry_search.bind("<KeyRelease>", self.on_search)

        self.btn_refresh = ctk.CTkButton(
            search_bar,
            text="🔄 Actualizar",
            width=100,
            height=36,
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=lambda: self.async_refresh_library(force=True)
        )
        self.btn_refresh.pack(side="right", padx=(0, 12), pady=8)

        self.lbl_count = ctk.CTkLabel(
            search_bar,
            text="Cargando...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#a1a1aa"
        )
        self.lbl_count.pack(side="right", padx=(0, 12))

        # 3. Lista de Canciones Paginada
        self.scroll_list = ctk.CTkScrollableFrame(self, fg_color="#09090b", corner_radius=10)
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        # 4. Barra de Paginación Inferior
        self.pagination_bar = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=8, height=36)
        self.pagination_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.pagination_bar.pack_propagate(False)

        self.btn_prev_page = ctk.CTkButton(
            self.pagination_bar,
            text="◀ Anterior",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=self.prev_page
        )
        self.btn_prev_page.pack(side="left", padx=10, pady=5)

        self.lbl_page_info = ctk.CTkLabel(
            self.pagination_bar,
            text="Página 1 de 1",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#a1a1aa"
        )
        self.lbl_page_info.pack(side="left", expand=True)

        self.btn_next_page = ctk.CTkButton(
            self.pagination_bar,
            text="Siguiente ▶",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=self.next_page
        )
        self.btn_next_page.pack(side="right", padx=10, pady=5)

    def action_change_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta de música a reproducir")
        if folder and os.path.exists(folder):
            playlist_queue.set_library_folder(folder)
            self.lbl_folder_path.configure(text=folder[:55])
            self.async_refresh_library(force=True)

    def async_refresh_library(self, force=False):
        self.lbl_count.configure(text="Escaneando biblioteca...")
        def worker():
            tracks = playlist_queue.load_library_tracks(force_refresh=force)
            def update():
                self.all_tracks = tracks
                self.filtered_tracks = list(self.all_tracks)
                self.page = 0
                self.lbl_count.configure(text=f"{len(self.all_tracks)} canciones")
                self.render_current_page()
            self.after(0, update)
        threading.Thread(target=worker, daemon=True).start()

    def on_search(self, event=None):
        query = self.entry_search.get().strip().lower()
        if not query:
            self.filtered_tracks = list(self.all_tracks)
        else:
            self.filtered_tracks = [t for t in self.all_tracks if query in os.path.basename(t).lower()]
        self.page = 0
        self.lbl_count.configure(text=f"{len(self.filtered_tracks)} de {len(self.all_tracks)} canciones")
        self.render_current_page()

    def render_current_page(self):
        for w in self.scroll_list.winfo_children():
            w.destroy()

        total = len(self.filtered_tracks)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page = max(0, min(self.page, total_pages - 1))

        self.lbl_page_info.configure(text=f"Página {self.page + 1} de {total_pages} ({total} canciones)")
        self.btn_prev_page.configure(state="normal" if self.page > 0 else "disabled")
        self.btn_next_page.configure(state="normal" if self.page < total_pages - 1 else "disabled")

        if not self.filtered_tracks:
            ctk.CTkLabel(
                self.scroll_list, 
                text="No se encontraron canciones MP3 en esta carpeta.",
                text_color="#71717a"
            ).pack(pady=40)
            return

        start = self.page * self.page_size
        end = min(start + self.page_size, total)

        for idx, track_path in enumerate(self.filtered_tracks[start:end], start + 1):
            fname = os.path.splitext(os.path.basename(track_path))[0]
            
            row = ctk.CTkFrame(self.scroll_list, fg_color="#18181b", corner_radius=6, height=36)
            row.pack(fill="x", padx=4, pady=2)
            row.pack_propagate(False)

            btn_play = ctk.CTkButton(
                row,
                text="▶",
                width=28,
                height=26,
                fg_color="#10b981",
                hover_color="#059669",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=track_path: self.play_selected(p)
            )
            btn_play.pack(side="left", padx=6, pady=4)

            lbl_num = ctk.CTkLabel(row, text=f"{idx}.", width=32, font=ctk.CTkFont(size=11), text_color="#71717a")
            lbl_num.pack(side="left")

            lbl_name = ctk.CTkLabel(
                row, 
                text=fname, 
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="#e4e4e7"
            )
            lbl_name.pack(side="left", fill="x", expand=True, padx=6)

    def next_page(self):
        self.page += 1
        self.render_current_page()

    def prev_page(self):
        self.page -= 1
        self.render_current_page()

    def play_selected(self, filepath):
        if self.on_play_track_callback:
            self.on_play_track_callback(filepath)
