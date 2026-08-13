# -*- coding: utf-8 -*-
"""Pestaña de Diagnóstico, Escáner de Duplicados y Comparador Inteligente PC vs USB."""

import os
import threading
from tkinter import messagebox
import customtkinter as ctk
from core.usb_manager import get_storage_diagnostics, list_all_usb_devices, sync_to_usb
from core.sync_engine import inspect_collection_detailed, resolve_and_clean_duplicates
from core.config import load_config, open_path_in_explorer
from core.task_manager import task_manager

class TabDiagnostics(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.selected_usb_letter = None
        self.is_scanning = False
        self.last_report = None

        self.setup_ui()
        self.async_run_scan()

    def setup_ui(self):
        # 1. Cabecera y Botón de Escaneo
        header = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        header.pack(fill="x", padx=12, pady=(10, 6))

        top_h = ctk.CTkFrame(header, fg_color="transparent")
        top_h.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            top_h,
            text="🔍 Inspector & Comparador de Colección (PC vs USB)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#10b981"
        ).pack(side="left")

        self.btn_scan = ctk.CTkButton(
            top_h,
            text="🔍 Escanear Colección Completa",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            fg_color="#10b981",
            hover_color="#059669",
            command=self.async_run_scan
        )
        self.btn_scan.pack(side="right")

        self.lbl_scan_status = ctk.CTkLabel(
            header,
            text="Inicia un escaneo para comparar canciones entre tu PC y la memoria USB y detectar duplicados.",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_scan_status.pack(anchor="w", padx=14, pady=(0, 10))

        # 2. Resumen de Métricas (Grid 4 Tarjetas)
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=12, pady=4)
        for i in range(4):
            metrics_row.columnconfigure(i, weight=1)

        # Tarjeta 1: PC Local
        self.card_pc = ctk.CTkFrame(metrics_row, fg_color="#18181b", corner_radius=8)
        self.card_pc.grid(row=0, column=0, padx=4, sticky="nsew")
        ctk.CTkLabel(self.card_pc, text="💻 PC Local", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(8, 2))
        self.lbl_count_pc = ctk.CTkLabel(self.card_pc, text="... canciones", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f4f4f5")
        self.lbl_count_pc.pack(anchor="w", padx=10, pady=(0, 8))

        # Tarjeta 2: USB
        self.card_usb = ctk.CTkFrame(metrics_row, fg_color="#18181b", corner_radius=8)
        self.card_usb.grid(row=0, column=1, padx=4, sticky="nsew")
        ctk.CTkLabel(self.card_usb, text="💾 Memoria USB", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(8, 2))
        self.lbl_count_usb = ctk.CTkLabel(self.card_usb, text="... canciones", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f4f4f5")
        self.lbl_count_usb.pack(anchor="w", padx=10, pady=(0, 8))

        # Tarjeta 3: Pendientes
        self.card_pend = ctk.CTkFrame(metrics_row, fg_color="#18181b", corner_radius=8)
        self.card_pend.grid(row=0, column=2, padx=4, sticky="nsew")
        ctk.CTkLabel(self.card_pend, text="⚠️ Faltantes en USB", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(8, 2))
        self.lbl_count_pend = ctk.CTkLabel(self.card_pend, text="... pendientes", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f59e0b")
        self.lbl_count_pend.pack(anchor="w", padx=10, pady=(0, 8))

        # Tarjeta 4: Duplicados
        self.card_dups = ctk.CTkFrame(metrics_row, fg_color="#18181b", corner_radius=8)
        self.card_dups.grid(row=0, column=3, padx=4, sticky="nsew")
        ctk.CTkLabel(self.card_dups, text="🔁 Duplicados", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a1a1aa").pack(anchor="w", padx=10, pady=(8, 2))
        self.lbl_count_dups = ctk.CTkLabel(self.card_dups, text="... duplicados", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ef4444")
        self.lbl_count_dups.pack(anchor="w", padx=10, pady=(0, 8))

        # 3. Sub-Pestañas Interactivas del Inspector
        self.sub_tabview = ctk.CTkTabview(self, corner_radius=10, fg_color="#18181b", height=340)
        self.sub_tabview.pack(fill="both", expand=True, padx=12, pady=6)

        self.tab_missing = self.sub_tabview.add("⚠️ Faltantes en USB")
        self.tab_dups = self.sub_tabview.add("🔁 Duplicados Locales")
        self.tab_usb_only = self.sub_tabview.add("💾 Solo en USB")
        self.tab_storage = self.sub_tabview.add("📊 Almacenamiento & Tareas")

        # Configurar Tab Faltantes
        self.setup_missing_tab()

        # Configurar Tab Duplicados
        self.setup_dups_tab()

        # Configurar Tab Solo en USB
        self.setup_usb_only_tab()

        # Configurar Tab Almacenamiento
        self.setup_storage_tab()

    def setup_missing_tab(self):
        bar = ctk.CTkFrame(self.tab_missing, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(4, 6))

        self.lbl_missing_summary = ctk.CTkLabel(
            bar,
            text="Canciones que están en tu PC pero aún no se han transferido a la memoria USB:",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_missing_summary.pack(side="left")

        self.btn_sync_missing = ctk.CTkButton(
            bar,
            text="⚡ Sincronizar Faltantes a USB",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=28,
            fg_color="#10b981",
            hover_color="#059669",
            command=self.action_sync_missing_now
        )
        self.btn_sync_missing.pack(side="right")

        self.scroll_missing = ctk.CTkScrollableFrame(self.tab_missing, fg_color="#09090b", corner_radius=8)
        self.scroll_missing.pack(fill="both", expand=True, padx=4, pady=4)

    def setup_dups_tab(self):
        bar = ctk.CTkFrame(self.tab_dups, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(4, 6))

        self.lbl_dups_summary = ctk.CTkLabel(
            bar,
            text="Canciones duplicadas detectadas en tu colección (nombres o metadatos idénticos):",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_dups_summary.pack(side="left")

        self.btn_clean_dups = ctk.CTkButton(
            bar,
            text="🧹 Resolver & Limpiar Duplicados",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=28,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            command=self.action_clean_duplicates_now
        )
        self.btn_clean_dups.pack(side="right")

        self.scroll_dups = ctk.CTkScrollableFrame(self.tab_dups, fg_color="#09090b", corner_radius=8)
        self.scroll_dups.pack(fill="both", expand=True, padx=4, pady=4)

    def setup_usb_only_tab(self):
        bar = ctk.CTkFrame(self.tab_usb_only, fg_color="transparent")
        bar.pack(fill="x", padx=6, pady=(4, 6))

        self.lbl_usb_only_summary = ctk.CTkLabel(
            bar,
            text="Canciones que existen en la memoria USB pero no están en la colección de tu PC:",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_usb_only_summary.pack(side="left")

        self.scroll_usb_only = ctk.CTkScrollableFrame(self.tab_usb_only, fg_color="#09090b", corner_radius=8)
        self.scroll_usb_only.pack(fill="both", expand=True, padx=4, pady=4)

    def setup_storage_tab(self):
        storage_row = ctk.CTkFrame(self.tab_storage, fg_color="transparent")
        storage_row.pack(fill="x", padx=6, pady=6)
        storage_row.columnconfigure(0, weight=1)
        storage_row.columnconfigure(1, weight=1)

        # Disco Local
        card_l = ctk.CTkFrame(storage_row, fg_color="#18181b", corner_radius=8)
        card_l.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        ctk.CTkLabel(card_l, text="💻 Disco Local", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.lbl_local_gb = ctk.CTkLabel(card_l, text="...", font=ctk.CTkFont(size=11), text_color="#a1a1aa")
        self.lbl_local_gb.pack(anchor="w", padx=12, pady=2)
        self.bar_local = ctk.CTkProgressBar(card_l, height=10, progress_color="#6366f1")
        self.bar_local.pack(fill="x", padx=12, pady=6)

        # USB
        card_u = ctk.CTkFrame(storage_row, fg_color="#18181b", corner_radius=8)
        card_u.grid(row=0, column=1, padx=(4, 0), sticky="nsew")
        ctk.CTkLabel(card_u, text="💾 Memoria USB", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.lbl_usb_gb = ctk.CTkLabel(card_u, text="...", font=ctk.CTkFont(size=11), text_color="#a1a1aa")
        self.lbl_usb_gb.pack(anchor="w", padx=12, pady=2)
        self.bar_usb = ctk.CTkProgressBar(card_u, height=10, progress_color="#10b981")
        self.bar_usb.pack(fill="x", padx=12, pady=6)

        # Guardrails y tareas
        card_t = ctk.CTkFrame(self.tab_storage, fg_color="#18181b", corner_radius=8)
        card_t.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(card_t, text="🛡️ Monitor de Guardrails y Procesos", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.lbl_active_tasks = ctk.CTkLabel(card_t, text="🟢 Inactivo", font=ctk.CTkFont(size=12), text_color="#10b981")
        self.lbl_active_tasks.pack(anchor="w", padx=12, pady=(2, 10))

    def async_run_scan(self):
        if self.is_scanning:
            return
        self.is_scanning = True
        self.btn_scan.configure(state="disabled", text="⏳ Escaneando...")
        self.lbl_scan_status.configure(text="Analizando pistas en disco local y memoria USB...", text_color="#f59e0b")

        def worker():
            devices = list_all_usb_devices()
            usb_letter = None
            for d in devices:
                letters = d.get("Letters", "").split(",")
                for l in letters:
                    l = l.strip()
                    if l and os.path.exists(f"{l}\\"):
                        usb_letter = l
                        break
                if usb_letter:
                    break

            self.selected_usb_letter = usb_letter

            report = inspect_collection_detailed(
                usb_letter=usb_letter,
                progress_callback=lambda msg: self.after(0, lambda m=msg: self.lbl_scan_status.configure(text=m))
            )
            diag = get_storage_diagnostics(usb_letter=usb_letter)
            self.last_report = report

            def render_results():
                self.btn_scan.configure(state="normal", text="🔍 Escanear Colección Completa")
                self.is_scanning = False

                loc_count = len(report["local_tracks"])
                usb_count = len(report["usb_tracks"])
                miss_count = len(report["missing_on_usb"])
                dups_count = report["total_duplicates_count"]

                # Tarjetas
                self.lbl_count_pc.configure(text=f"{loc_count} ({report['total_local_size_gb']} GB)")
                if usb_letter:
                    self.lbl_count_usb.configure(text=f"{usb_count} ({report['total_usb_size_gb']} GB)")
                else:
                    self.lbl_count_usb.configure(text="Desconectada")

                if miss_count > 0:
                    self.lbl_count_pend.configure(text=f"{miss_count} pendientes", text_color="#f59e0b")
                    self.btn_sync_missing.configure(text=f"⚡ Sincronizar {miss_count} Faltantes a USB", state="normal")
                else:
                    self.lbl_count_pend.configure(text="✔ Al día (100%)", text_color="#10b981")
                    self.btn_sync_missing.configure(text="✔ Toda la Colección Sincronizada", state="disabled")

                if dups_count > 0:
                    self.lbl_count_dups.configure(text=f"{dups_count} detectados", text_color="#ef4444")
                    self.btn_clean_dups.configure(text=f"🧹 Resolver {dups_count} Duplicados", state="normal")
                else:
                    self.lbl_count_dups.configure(text="✔ Sin duplicados", text_color="#10b981")
                    self.btn_clean_dups.configure(text="✔ Colección Limpia", state="disabled")

                self.lbl_scan_status.configure(
                    text=f"✔ Escaneo completado: {loc_count} canciones en PC, {usb_count} en USB ({usb_letter or 'N/A'}), {dups_count} duplicados.",
                    text_color="#10b981"
                )

                # Renderizar listas
                self.render_missing_list(report["missing_on_usb"])
                self.render_dups_list(report["duplicate_groups"])
                self.render_usb_only_list(report["only_on_usb"])

                # Almacenamiento
                loc = diag["local"]
                self.lbl_local_gb.configure(text=f"Usado: {loc['used_gb']} GB de {loc['total_gb']} GB ({loc['free_gb']} GB libres)")
                self.bar_local.set(loc["percent"] / 100.0)

                usb = diag["usb"]
                if usb:
                    self.lbl_usb_gb.configure(text=f"Unidad {usb['drive']} - Usado: {usb['used_gb']} GB de {usb['total_gb']} GB")
                    self.bar_usb.set(usb["percent"] / 100.0)
                else:
                    self.lbl_usb_gb.configure(text="Memoria USB no detectada.")
                    self.bar_usb.set(0)

                summary, cnt = task_manager.get_active_tasks_summary()
                if cnt > 0:
                    self.lbl_active_tasks.configure(text=f"🔄 {cnt} tarea(s) en curso: {summary}", text_color="#f59e0b")
                else:
                    self.lbl_active_tasks.configure(text="🟢 No hay procesos concurrentes activos.", text_color="#10b981")

            self.after(0, render_results)

        threading.Thread(target=worker, daemon=True).start()

    def render_missing_list(self, missing_tracks):
        for w in self.scroll_missing.winfo_children():
            w.destroy()

        if not missing_tracks:
            ctk.CTkLabel(
                self.scroll_missing,
                text="🎉 ¡Felicidades! Toda tu colección de música está sincronizada en la memoria USB.",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#10b981"
            ).pack(pady=30)
            return

        for idx, track in enumerate(missing_tracks, 1):
            row = ctk.CTkFrame(self.scroll_missing, fg_color="#18181b", corner_radius=6, height=32)
            row.pack(fill="x", padx=4, pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=f"{idx}.", width=36, font=ctk.CTkFont(size=11), text_color="#71717a").pack(side="left")
            ctk.CTkLabel(
                row,
                text=f"{track['artist']} - {track['title']}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="#e4e4e7"
            ).pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkLabel(row, text=f"{track['size_mb']} MB", font=ctk.CTkFont(size=11), text_color="#a1a1aa", width=60).pack(side="right", padx=8)

    def render_dups_list(self, duplicate_groups):
        for w in self.scroll_dups.winfo_children():
            w.destroy()

        if not duplicate_groups:
            ctk.CTkLabel(
                self.scroll_dups,
                text="✨ ¡Excelente! No se detectaron canciones duplicadas en tu colección.",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#10b981"
            ).pack(pady=30)
            return

        for idx, group in enumerate(duplicate_groups, 1):
            card = ctk.CTkFrame(self.scroll_dups, fg_color="#18181b", corner_radius=8)
            card.pack(fill="x", padx=4, pady=4)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(8, 4))

            ctk.CTkLabel(top, text=f"🔁 Grupo #{idx}: {group['name']}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f59e0b").pack(side="left")
            ctk.CTkLabel(top, text=f"{group['total_count']} archivos duplicados", font=ctk.CTkFont(size=11), text_color="#a1a1aa").pack(side="right")

            # Mejor pista (a conservar)
            best = group["best"]
            r_best = ctk.CTkFrame(card, fg_color="#102a1d", corner_radius=6)
            r_best.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(r_best, text="[CONSERVAR - MEJOR CALIDAD]", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10b981", width=180, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(r_best, text=best["filename"][:45], font=ctk.CTkFont(size=11), text_color="#e4e4e7", anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(r_best, text=f"{best['bitrate_kbps']} kbps ({best['size_mb']} MB)", font=ctk.CTkFont(size=10), text_color="#10b981").pack(side="right", padx=8)

            # Pistas duplicadas (a eliminar)
            for dup in group["duplicates"]:
                r_dup = ctk.CTkFrame(card, fg_color="#2b1414", corner_radius=6)
                r_dup.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(r_dup, text="[DUPLICADO - A ELIMINAR]", font=ctk.CTkFont(size=10, weight="bold"), text_color="#ef4444", width=180, anchor="w").pack(side="left", padx=6)
                ctk.CTkLabel(r_dup, text=dup["filename"][:45], font=ctk.CTkFont(size=11), text_color="#a1a1aa", anchor="w").pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(r_dup, text=f"{dup['bitrate_kbps']} kbps ({dup['size_mb']} MB)", font=ctk.CTkFont(size=10), text_color="#ef4444").pack(side="right", padx=8)

    def render_usb_only_list(self, usb_only_tracks):
        for w in self.scroll_usb_only.winfo_children():
            w.destroy()

        if not usb_only_tracks:
            ctk.CTkLabel(
                self.scroll_usb_only,
                text="No hay canciones exclusivas en la memoria USB.",
                font=ctk.CTkFont(size=12),
                text_color="#71717a"
            ).pack(pady=30)
            return

        for idx, track in enumerate(usb_only_tracks, 1):
            row = ctk.CTkFrame(self.scroll_usb_only, fg_color="#18181b", corner_radius=6, height=32)
            row.pack(fill="x", padx=4, pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=f"{idx}.", width=36, font=ctk.CTkFont(size=11), text_color="#71717a").pack(side="left")
            ctk.CTkLabel(
                row,
                text=f"{track['artist']} - {track['title']}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="#e4e4e7"
            ).pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkLabel(row, text=f"{track['size_mb']} MB", font=ctk.CTkFont(size=11), text_color="#a1a1aa", width=60).pack(side="right", padx=8)

    def action_clean_duplicates_now(self):
        if not self.last_report or not self.last_report.get("duplicate_groups"):
            messagebox.showinfo("Duplicados", "No hay duplicados para limpiar.")
            return

        cnt = self.last_report["total_duplicates_count"]
        confirm = messagebox.askyesno(
            "Confirmar Limpieza de Duplicados",
            f"Se eliminarán {cnt} archivos duplicados conservando siempre la pista de mayor calidad/bitrate en tu colección.\n\n¿Deseas continuar?"
        )
        if not confirm:
            return

        def worker():
            removed, errs = resolve_and_clean_duplicates(self.last_report["duplicate_groups"])
            self.after(0, lambda: messagebox.showinfo("Limpieza Completada", f"Se eliminaron {removed} pistas duplicadas con éxito."))
            self.after(0, self.async_run_scan)

        threading.Thread(target=worker, daemon=True).start()

    def action_sync_missing_now(self):
        if not self.selected_usb_letter:
            messagebox.showerror("Error", "Por favor conecta una memoria USB.")
            return

        def worker():
            ok, msg = sync_to_usb(self.selected_usb_letter)
            self.after(0, lambda: messagebox.showinfo("Sincronización USB", msg))
            self.after(0, self.async_run_scan)

        threading.Thread(target=worker, daemon=True).start()

    def async_refresh_diagnostics(self):
        self.async_run_scan()
