# -*- coding: utf-8 -*-
"""Vista / Frame de Selección de Herramientas y Lanzador Inicial (Launcher Hub)."""

import customtkinter as ctk
from core.config import load_config, save_config

class LauncherHub(ctk.CTkFrame):
    def __init__(self, master, on_select_mode_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_select_mode = on_select_mode_callback
        self.setup_ui()

    def setup_ui(self):
        # Contenedor Centrado
        center_box = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=14, width=640)
        center_box.pack(expand=True, padx=20, pady=20)

        # Cabecera
        header = ctk.CTkFrame(center_box, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="🚀 MusicSync Studio Launcher",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            header,
            text="Selecciona la herramienta o modo de trabajo optimizado para hoy:",
            font=ctk.CTkFont(size=13),
            text_color="#a1a1aa"
        ).pack(anchor="w")

        # Tarjetas de Opciones
        cards_box = ctk.CTkFrame(center_box, fg_color="transparent")
        cards_box.pack(fill="both", expand=True, padx=20, pady=8)

        # Opción 1: Modo Rápido / Ultra Ligero (Recomendado)
        card_quick = ctk.CTkFrame(cards_box, fg_color="#1e1e24", corner_radius=10)
        card_quick.pack(fill="x", pady=6)

        btn_quick = ctk.CTkButton(
            card_quick,
            text="⚡ MODO RÁPIDO: Descargas & Gestor USB (Ultra Ligero)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=46,
            command=lambda: self.select_mode("sync_usb")
        )
        btn_quick.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            card_quick,
            text="Ideal para sincronizar a tu USB o descargar sin sobrecargar la memoria ni el CPU.",
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Opción 2: Modo Completo Studio Pro
        card_full = ctk.CTkFrame(cards_box, fg_color="#1e1e24", corner_radius=10)
        card_full.pack(fill="x", pady=6)

        btn_full = ctk.CTkButton(
            card_full,
            text="🎵 MODO COMPLETO: Studio Pro (Con Reproductor y Salidas de Audio)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6366f1",
            hover_color="#4f46e5",
            height=46,
            command=lambda: self.select_mode("full")
        )
        btn_full.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            card_full,
            text="Incluye explorador local, barra estilo Spotify y enrutador de audio para Voicemeeter / Bluetooth / HDMI.",
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        # Opción 3: Formateador Directo de USB
        card_usb = ctk.CTkFrame(cards_box, fg_color="#1e1e24", corner_radius=10)
        card_usb.pack(fill="x", pady=6)

        btn_usb = ctk.CTkButton(
            card_usb,
            text="🛠️ HERRAMIENTA: Formatear y Reparar Memoria USB (FAT32)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3f3f46",
            hover_color="#52525b",
            height=40,
            command=lambda: self.select_mode("usb_only")
        )
        btn_usb.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            card_usb,
            text="Limpia particiones corruptas y prepara la USB en formato FAT32 universal para autos.",
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        # Footer con Checkbox para Recordar
        footer = ctk.CTkFrame(center_box, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(8, 20))

        self.chk_remember = ctk.CTkCheckBox(
            footer,
            text="Recordar mi elección y abrir directamente este modo en el futuro",
            font=ctk.CTkFont(size=11),
            text_color="#d4d4d8"
        )
        self.chk_remember.pack(side="left")

    def select_mode(self, mode):
        remember = bool(self.chk_remember.get())
        config = load_config()
        config["remember_launch_mode"] = remember
        config["default_launch_mode"] = mode
        save_config(config)

        if self.on_select_mode:
            self.on_select_mode(mode)
