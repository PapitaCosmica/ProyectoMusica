# -*- coding: utf-8 -*-
"""Pestaña Gestor de Playlists y Enlaces de YouTube."""

import time
from tkinter import messagebox
import customtkinter as ctk
from core.config import load_config, save_config

class TabPlaylists(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.setup_ui()

    def setup_ui(self):
        pl_header = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        pl_header.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            pl_header,
            text="📋 Playlists y Enlaces de Descarga",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            pl_header,
            text="Agrega enlaces de YouTube (playlists, álbumes o videos) para sincronizarlos automáticamente.",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        add_frame = ctk.CTkFrame(self, fg_color="#1e1e24", corner_radius=10)
        add_frame.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(add_frame, text="Nombre de la Playlist:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")
        self.entry_pl_name = ctk.CTkEntry(add_frame, placeholder_text="Ej: Éxitos 2026", height=36)
        self.entry_pl_name.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(add_frame, text="Enlace de YouTube Playlist:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, padx=12, pady=(10, 2), sticky="w")
        self.entry_pl_url = ctk.CTkEntry(add_frame, placeholder_text="https://youtube.com/playlist?list=...", height=36)
        self.entry_pl_url.grid(row=1, column=1, padx=12, pady=(0, 10), sticky="ew")

        add_frame.columnconfigure(0, weight=1)
        add_frame.columnconfigure(1, weight=2)

        self.btn_add_pl = ctk.CTkButton(
            add_frame,
            text="➕ Agregar Playlist",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#10b981",
            hover_color="#059669",
            command=self.action_add_playlist
        )
        self.btn_add_pl.grid(row=1, column=2, padx=12, pady=(0, 10))

        ctk.CTkLabel(
            self,
            text="Playlists Registradas:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(12, 4))

        self.scroll_playlists = ctk.CTkScrollableFrame(self, fg_color="#09090b", corner_radius=10)
        self.scroll_playlists.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.render_playlist_list()

    def render_playlist_list(self):
        for widget in self.scroll_playlists.winfo_children():
            widget.destroy()

        config = load_config()
        playlists = config.get("playlists", [])

        if not playlists:
            ctk.CTkLabel(
                self.scroll_playlists, 
                text="No hay playlists configuradas. Agrega una arriba.", 
                text_color="#71717a"
            ).pack(pady=20)
            return

        for idx, pl in enumerate(playlists):
            card = ctk.CTkFrame(self.scroll_playlists, fg_color="#18181b", corner_radius=8)
            card.pack(fill="x", padx=6, pady=4)

            switch = ctk.CTkSwitch(
                card,
                text=pl.get("name", f"Playlist {idx+1}"),
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda i=idx: self.toggle_playlist(i)
            )
            if pl.get("active", True):
                switch.select()
            switch.pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(
                card,
                text=pl.get("url", ""),
                font=ctk.CTkFont(size=12),
                text_color="#a1a1aa",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10)

            btn_del = ctk.CTkButton(
                card,
                text="🗑️",
                width=36,
                height=32,
                fg_color="#3f3f46",
                hover_color="#ef4444",
                command=lambda i=idx: self.delete_playlist(i)
            )
            btn_del.pack(side="right", padx=10)

    def toggle_playlist(self, index):
        config = load_config()
        playlists = config.get("playlists", [])
        if 0 <= index < len(playlists):
            playlists[index]["active"] = not playlists[index].get("active", True)
            config["playlists"] = playlists
            save_config(config)

    def delete_playlist(self, index):
        config = load_config()
        playlists = config.get("playlists", [])
        if 0 <= index < len(playlists):
            del playlists[index]
            config["playlists"] = playlists
            save_config(config)
            self.render_playlist_list()

    def action_add_playlist(self):
        name = self.entry_pl_name.get().strip()
        url = self.entry_pl_url.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Por favor ingresa el enlace de la playlist.")
            return

        if not name:
            name = f"Playlist {int(time.time())}"

        config = load_config()
        playlists = config.get("playlists", [])
        playlists.append({"name": name, "url": url, "active": True})
        config["playlists"] = playlists
        save_config(config)

        self.entry_pl_name.delete(0, "end")
        self.entry_pl_url.delete(0, "end")
        self.render_playlist_list()
