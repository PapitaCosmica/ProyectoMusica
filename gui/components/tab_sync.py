# -*- coding: utf-8 -*-
"""Pestaña Centro de Control: Descarga, Sincronización y Registro en Tiempo Real."""

import os
import time
import threading
from tkinter import messagebox
import customtkinter as ctk
from core.downloader import download_playlists
from core.sync_engine import consolidate_and_deduplicate
from core.task_manager import task_manager

class TabSync(ctk.CTkFrame):
    def __init__(self, master, on_sync_finished=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_sync_finished = on_sync_finished
        self.cancel_event = threading.Event()
        self.setup_ui()

    def setup_ui(self):
        # Botones de Acción
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(10, 8))

        self.btn_download = ctk.CTkButton(
            actions_frame,
            text="⬇️ Descargar Playlist y Sincronizar",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=42,
            command=self.action_download
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_sync_local = ctk.CTkButton(
            actions_frame,
            text="🔄 Unificar y Desduplicar Colección",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6366f1",
            hover_color="#4f46e5",
            height=42,
            command=self.action_sync
        )
        self.btn_sync_local.pack(side="left", fill="x", expand=True, padx=6)

        self.btn_stop = ctk.CTkButton(
            actions_frame,
            text="⏹️ Detener",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=42,
            width=100,
            state="disabled",
            command=self.action_stop
        )
        self.btn_stop.pack(side="left", padx=(6, 0))

        # Barra de Progreso y Pista Actual
        prog_frame = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        prog_frame.pack(fill="x", padx=10, pady=6)

        self.lbl_current_track = ctk.CTkLabel(
            prog_frame,
            text="Pista actual: Esperando inicio...",
            font=ctk.CTkFont(size=13),
            text_color="#e4e4e7",
            anchor="w"
        )
        self.lbl_current_track.pack(fill="x", padx=14, pady=(10, 4))

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=14, corner_radius=7, progress_color="#10b981")
        self.progress_bar.pack(fill="x", padx=14, pady=4)
        self.progress_bar.set(0)

        self.lbl_progress_percent = ctk.CTkLabel(
            prog_frame,
            text="0% (0/0 canciones)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#a1a1aa",
            anchor="e"
        )
        self.lbl_progress_percent.pack(fill="x", padx=14, pady=(2, 10))

        # Consola de Registro
        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            log_header, 
            text="📋 Registro de Actividad en Tiempo Real:", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#a1a1aa"
        ).pack(side="left")

        ctk.CTkButton(
            log_header,
            text="Limpiar Log",
            font=ctk.CTkFont(size=11),
            width=80,
            height=24,
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.clear_log
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#09090b",
            text_color="#a1a1aa",
            corner_radius=10
        )
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        self.log_textbox.configure(state="disabled")

    def log(self, message):
        def _write():
            self.log_textbox.configure(state="normal")
            timestamp = time.strftime("[%H:%M:%S] ")
            self.log_textbox.insert("end", timestamp + message + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(0, _write)

    def clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def set_busy(self, busy):
        self.btn_download.configure(state="disabled" if busy else "normal")
        self.btn_sync_local.configure(state="disabled" if busy else "normal")
        self.btn_stop.configure(state="normal" if busy else "disabled")
        if not busy:
            self.progress_bar.set(0)
            self.lbl_progress_percent.configure(text="0% (0/0 canciones)")
            self.lbl_current_track.configure(text="Pista actual: Completado")

    def action_download(self):
        self.cancel_event.clear()
        self.set_busy(True)
        self.log("🚀 INICIANDO DESCARGA DE PLAYLISTS DE YOUTUBE...")

        def worker():
            def on_ytdl_line(line):
                self.log(line)
                if "[download]" in line and "%" in line:
                    try:
                        part = line.split("%")[0].split()[-1]
                        val = float(part) / 100.0
                        self.after(0, lambda: self.progress_bar.set(val))
                        self.after(0, lambda: self.lbl_progress_percent.configure(text=f"{part}%"))
                    except Exception:
                        pass
                elif "[ExtractAudio]" in line or "[Metadata]" in line:
                    fname = os.path.basename(line)
                    self.after(0, lambda: self.lbl_current_track.configure(text=f"Procesando: {fname[:60]}"))

            ok, msg = download_playlists(progress_callback=on_ytdl_line, cancel_event=self.cancel_event)
            self.after(0, lambda: self.set_busy(False))
            self.log(f"[✔] {msg}")
            if self.on_sync_finished:
                self.after(0, self.on_sync_finished)

        threading.Thread(target=worker, daemon=True).start()

    def action_sync(self):
        self.set_busy(True)
        self.log("🔄 INICIANDO UNIFICACIÓN Y DESDUPLICACIÓN LOCAL...")

        def worker():
            def on_sync_progress(current, total, msg):
                frac = current / total if total > 0 else 1.0
                self.after(0, lambda: self.progress_bar.set(frac))
                self.after(0, lambda: self.lbl_progress_percent.configure(text=f"{frac*100:.1f}% ({current}/{total})"))
                self.after(0, lambda: self.lbl_current_track.configure(text=f"Pista: {msg}"))

            ok, msg = consolidate_and_deduplicate(dry_run=False, progress_callback=on_sync_progress)
            self.after(0, lambda: self.set_busy(False))
            self.log(f"[✔] {msg}")
            if self.on_sync_finished:
                self.after(0, self.on_sync_finished)

        threading.Thread(target=worker, daemon=True).start()

    def action_stop(self):
        self.cancel_event.set()
        self.log("[!] Solicitud de detención enviada...")
        self.set_busy(False)
