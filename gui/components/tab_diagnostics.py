# -*- coding: utf-8 -*-
"""Pestaña de Diagnóstico, Almacenamiento y Estado de Sincronización (100% Asíncrona)."""

import threading
import customtkinter as ctk
from core.usb_manager import get_storage_diagnostics, get_pending_sync_metrics, list_all_usb_devices
from core.config import load_config
from core.task_manager import task_manager

class TabDiagnostics(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.selected_usb_letter = None
        self.is_refreshing = False
        self.setup_ui()
        self.async_refresh_diagnostics()

    def setup_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        header.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            header,
            text="📊 Diagnóstico del Sistema y Almacenamiento",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            header,
            text="Supervisa el espacio en disco, el estado de sincronización entre tu PC y la memoria USB y los procesos en segundo plano.",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # 1. Tarjetas de Almacenamiento (Disco Local y USB)
        storage_row = ctk.CTkFrame(self, fg_color="transparent")
        storage_row.pack(fill="x", padx=12, pady=6)
        storage_row.columnconfigure(0, weight=1)
        storage_row.columnconfigure(1, weight=1)

        # Tarjeta Disco Local
        self.card_local = ctk.CTkFrame(storage_row, fg_color="#18181b", corner_radius=10)
        self.card_local.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        ctk.CTkLabel(self.card_local, text="💻 Disco Local (D:)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 4))
        self.lbl_local_gb = ctk.CTkLabel(self.card_local, text="Cargando espacio...", font=ctk.CTkFont(size=12), text_color="#a1a1aa")
        self.lbl_local_gb.pack(anchor="w", padx=14, pady=2)

        self.bar_local = ctk.CTkProgressBar(self.card_local, height=12, corner_radius=6, progress_color="#6366f1")
        self.bar_local.pack(fill="x", padx=14, pady=8)
        self.bar_local.set(0)

        self.lbl_local_percent = ctk.CTkLabel(self.card_local, text="0% usado", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa", anchor="e")
        self.lbl_local_percent.pack(fill="x", padx=14, pady=(0, 12))

        # Tarjeta Memoria USB
        self.card_usb = ctk.CTkFrame(storage_row, fg_color="#18181b", corner_radius=10)
        self.card_usb.grid(row=0, column=1, padx=(6, 0), sticky="nsew")

        ctk.CTkLabel(self.card_usb, text="💾 Memoria USB", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 4))
        self.lbl_usb_gb = ctk.CTkLabel(self.card_usb, text="Detectando unidad...", font=ctk.CTkFont(size=12), text_color="#a1a1aa")
        self.lbl_usb_gb.pack(anchor="w", padx=14, pady=2)

        self.bar_usb = ctk.CTkProgressBar(self.card_usb, height=12, corner_radius=6, progress_color="#10b981")
        self.bar_usb.pack(fill="x", padx=14, pady=8)
        self.bar_usb.set(0)

        self.lbl_usb_percent = ctk.CTkLabel(self.card_usb, text="0% usado", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa", anchor="e")
        self.lbl_usb_percent.pack(fill="x", padx=14, pady=(0, 12))

        # 2. Tarjeta de Estado de Sincronización y Canciones Pendientes
        sync_status_card = ctk.CTkFrame(self, fg_color="#1e1e24", corner_radius=10)
        sync_status_card.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(sync_status_card, text="🔄 Estado de Sincronización", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f59e0b").pack(anchor="w", padx=14, pady=(12, 4))

        self.lbl_pending_tracks = ctk.CTkLabel(
            sync_status_card,
            text="Analizando archivos pendientes...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f4f4f5"
        )
        self.lbl_pending_tracks.pack(anchor="w", padx=14, pady=2)

        self.lbl_last_sync = ctk.CTkLabel(
            sync_status_card,
            text="Última sincronización: Sin registro previo",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_last_sync.pack(anchor="w", padx=14, pady=(2, 12))

        # 3. Monitor de Procesos y Guardrails
        proc_card = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        proc_card.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        proc_header = ctk.CTkFrame(proc_card, fg_color="transparent")
        proc_header.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(proc_header, text="🛡️ Monitor de Guardrails y Procesos Activos", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        self.btn_refresh = ctk.CTkButton(
            proc_header,
            text="🔄 Actualizar Diagnóstico",
            font=ctk.CTkFont(size=11),
            width=140,
            height=28,
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.async_refresh_diagnostics
        )
        self.btn_refresh.pack(side="right")

        self.lbl_active_tasks = ctk.CTkLabel(
            proc_card,
            text="🟢 No hay procesos concurrentes bloqueantes activos.",
            font=ctk.CTkFont(size=13),
            text_color="#10b981"
        )
        self.lbl_active_tasks.pack(anchor="w", padx=14, pady=(4, 10))

    def async_refresh_diagnostics(self):
        if self.is_refreshing:
            return
        self.is_refreshing = True
        self.btn_refresh.configure(state="disabled", text="⏳ Analizando...")

        def worker():
            # 1. Encontrar letra de USB
            devices = list_all_usb_devices()
            usb_letter = None
            for d in devices:
                letters = d.get("Letters", "").split(",")
                for l in letters:
                    l = l.strip()
                    if l:
                        usb_letter = l
                        break
                if usb_letter:
                    break

            self.selected_usb_letter = usb_letter
            diag = get_storage_diagnostics(usb_letter=usb_letter)
            metrics = get_pending_sync_metrics(usb_letter)
            config = load_config()
            last_t = config.get("last_sync_timestamp")
            last_d = config.get("last_sync_target")
            summary, count = task_manager.get_active_tasks_summary()

            def update_ui():
                loc = diag["local"]
                self.lbl_local_gb.configure(text=f"Usado: {loc['used_gb']} GB de {loc['total_gb']} GB ({loc['free_gb']} GB libres)")
                self.bar_local.set(loc["percent"] / 100.0)
                self.lbl_local_percent.configure(text=f"{loc['percent']}% en uso")

                usb = diag["usb"]
                if usb:
                    self.lbl_usb_gb.configure(text=f"Unidad {usb['drive']} - Usado: {usb['used_gb']} GB de {usb['total_gb']} GB ({usb['free_gb']} GB libres)")
                    self.bar_usb.set(usb["percent"] / 100.0)
                    self.lbl_usb_percent.configure(text=f"{usb['percent']}% en uso")
                else:
                    self.lbl_usb_gb.configure(text="No se detectó memoria USB formateada.")
                    self.bar_usb.set(0)
                    self.lbl_usb_percent.configure(text="Desconectada")

                p_cnt = metrics["pending_count"]
                if p_cnt > 0:
                    self.lbl_pending_tracks.configure(text=f"⚠️ {p_cnt} canciones nuevas pendientes por transferir a la memoria USB", text_color="#f59e0b")
                else:
                    self.lbl_pending_tracks.configure(text=f"✔ Toda tu colección local ({metrics['local_count']} canciones) está sincronizada en la USB", text_color="#10b981")

                if last_t:
                    self.lbl_last_sync.configure(text=f"Última sincronización exitosa: {last_t} (Destino: {last_d})")
                else:
                    self.lbl_last_sync.configure(text="Última sincronización: Sin registro previo")

                if count > 0:
                    self.lbl_active_tasks.configure(text=f"🔄 {count} tarea(s) en curso: {summary} (Guardrails activos)", text_color="#f59e0b")
                else:
                    self.lbl_active_tasks.configure(text="🟢 No hay procesos concurrentes bloqueantes activos.", text_color="#10b981")

                self.btn_refresh.configure(state="normal", text="🔄 Actualizar Diagnóstico")
                self.is_refreshing = False

            self.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()
