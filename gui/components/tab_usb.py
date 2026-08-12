# -*- coding: utf-8 -*-
"""Pestaña Gestor de Memoria USB: Formateo Universal y Sincronización Incremental Visual."""

import os
import threading
from tkinter import messagebox, filedialog
import customtkinter as ctk
from core.usb_manager import list_all_usb_devices, format_usb_drive, sync_to_usb, get_pending_sync_metrics
from core.config import BASE_DIR, load_config, save_config

class TabUsb(ctk.CTkFrame):
    def __init__(self, master, on_usb_action_finished=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_usb_action_finished = on_usb_action_finished
        self.usb_devices = []
        self.cancel_event = threading.Event()
        self.is_syncing = False

        self.setup_ui()
        self.refresh_usb_drives()

    def setup_ui(self):
        # 1. Cabecera
        usb_header = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        usb_header.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            usb_header,
            text="💾 Gestor & Sincronizador de Memoria USB",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            usb_header,
            text="Gestiona carpetas de origen/destino, detecta canciones faltantes y sincroniza a la USB de forma incremental con 1 clic.",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # 2. Tarjeta de Configuración de Rutas (Origen y Destino)
        paths_card = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        paths_card.pack(fill="x", padx=12, pady=6)

        config = load_config()
        src_path = config.get("source_folder") or os.path.join(BASE_DIR, "Musica")

        # Fila Origen
        row_src = ctk.CTkFrame(paths_card, fg_color="transparent")
        row_src.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(row_src, text="📂 Carpeta Origen (PC):", width=160, font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981", anchor="w").pack(side="left")
        self.lbl_src_path = ctk.CTkLabel(row_src, text=src_path, font=ctk.CTkFont(size=12), text_color="#e4e4e7", anchor="w")
        self.lbl_src_path.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkButton(
            row_src,
            text="📁 Cambiar Origen...",
            width=130,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.action_change_source
        ).pack(side="right")

        # Fila Destino USB
        row_usb = ctk.CTkFrame(paths_card, fg_color="transparent")
        row_usb.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkLabel(row_usb, text="💾 Unidad USB Destino:", width=160, font=ctk.CTkFont(size=12, weight="bold"), text_color="#6366f1", anchor="w").pack(side="left")

        self.combo_usb = ctk.CTkComboBox(
            row_usb,
            values=["Buscando USBs..."],
            height=30,
            font=ctk.CTkFont(size=12),
            command=lambda v: self.async_check_pending(),
            state="readonly"
        )
        self.combo_usb.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkButton(
            row_usb,
            text="🔄 Actualizar",
            width=90,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.refresh_usb_drives
        ).pack(side="right")

        # 3. Tarjeta de Estado de Sincronización
        status_card = ctk.CTkFrame(self, fg_color="#1e1e24", corner_radius=10)
        status_card.pack(fill="x", padx=12, pady=6)

        self.lbl_sync_status = ctk.CTkLabel(
            status_card,
            text="Calculando canciones pendientes...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f59e0b"
        )
        self.lbl_sync_status.pack(anchor="w", padx=14, pady=(10, 4))

        self.lbl_sync_details = ctk.CTkLabel(
            status_card,
            text="PC: ... canciones | USB: ... canciones",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_sync_details.pack(anchor="w", padx=14, pady=(0, 10))

        # 4. Barra de Progreso de Sincronización en Vivo
        self.prog_box = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        self.prog_box.pack(fill="x", padx=12, pady=6)

        self.lbl_copying_file = ctk.CTkLabel(
            self.prog_box,
            text="Listo para sincronizar.",
            font=ctk.CTkFont(size=12),
            text_color="#e4e4e7",
            anchor="w"
        )
        self.lbl_copying_file.pack(fill="x", padx=14, pady=(8, 2))

        self.bar_sync = ctk.CTkProgressBar(self.prog_box, height=14, corner_radius=7, progress_color="#10b981")
        self.bar_sync.pack(fill="x", padx=14, pady=4)
        self.bar_sync.set(0)

        self.lbl_sync_percent = ctk.CTkLabel(
            self.prog_box,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#a1a1aa",
            anchor="e"
        )
        self.lbl_sync_percent.pack(fill="x", padx=14, pady=(0, 8))

        # 5. Botones de Acción
        usb_actions = ctk.CTkFrame(self, fg_color="transparent")
        usb_actions.pack(fill="x", padx=12, pady=8)

        self.btn_sync_usb = ctk.CTkButton(
            usb_actions,
            text="⚡ Sincronizar Colección a USB Ahora",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=46,
            command=self.action_sync_to_usb
        )
        self.btn_sync_usb.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_format_usb = ctk.CTkButton(
            usb_actions,
            text="🛠️ Formatear USB (FAT32 Universal)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=46,
            width=220,
            command=self.action_format_usb
        )
        self.btn_format_usb.pack(side="right", padx=(6, 0))

    def action_change_source(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta origen de música")
        if folder and os.path.exists(folder):
            config = load_config()
            config["source_folder"] = folder
            save_config(config)
            self.lbl_src_path.configure(text=folder)
            self.async_check_pending()

    def get_selected_usb_letter(self):
        selected_str = self.combo_usb.get()
        for d in self.usb_devices:
            if f"Disco {d.get('Index')}" in selected_str:
                letters = d.get("Letters", "").split(",")
                for l in letters:
                    l = l.strip()
                    if l and os.path.exists(f"{l}\\"):
                        return l
        return None

    def refresh_usb_drives(self):
        self.usb_devices = list_all_usb_devices()
        if not self.usb_devices:
            self.combo_usb.configure(values=["No se detectaron discos USB"])
            self.combo_usb.set("No se detectaron discos USB")
            self.lbl_sync_status.configure(text="Conecta una memoria USB para sincronizar", text_color="#a1a1aa")
        else:
            values = []
            for d in self.usb_devices:
                idx = d.get("Index")
                name = d.get("Name", "USB")
                size = d.get("SizeGB", 0)
                letters = d.get("Letters", "Sin letra")
                values.append(f"Disco {idx}: {name} ({size} GB) - [{letters}]")
            self.combo_usb.configure(values=values)
            self.combo_usb.set(values[0])
            self.async_check_pending()

    def async_check_pending(self):
        usb_letter = self.get_selected_usb_letter()
        if not usb_letter:
            return

        def worker():
            metrics = get_pending_sync_metrics(usb_letter)
            def update():
                p_cnt = metrics["pending_count"]
                loc_cnt = metrics["local_count"]
                usb_cnt = metrics["usb_count"]

                if p_cnt > 0:
                    self.lbl_sync_status.configure(
                        text=f"⚠️ Faltan {p_cnt} canciones por transferir a la memoria USB ({usb_letter})",
                        text_color="#f59e0b"
                    )
                    self.btn_sync_usb.configure(text=f"⚡ Sincronizar {p_cnt} Canciones a USB Ahora")
                else:
                    self.lbl_sync_status.configure(
                        text=f"✔ Toda tu colección ({loc_cnt} canciones) está 100% sincronizada en la USB",
                        text_color="#10b981"
                    )
                    self.btn_sync_usb.configure(text="⚡ Sincronizar Colección a USB Ahora")

                self.lbl_sync_details.configure(
                    text=f"PC: {loc_cnt} canciones en {metrics['src_dir']} | USB: {usb_cnt} canciones en {metrics['usb_dir']}"
                )
            self.after(0, update)
        threading.Thread(target=worker, daemon=True).start()

    def action_sync_to_usb(self):
        usb_letter = self.get_selected_usb_letter()
        if not usb_letter:
            messagebox.showerror("Error", "Por favor conecta y selecciona una memoria USB válida.")
            return

        if self.is_syncing:
            return
        self.is_syncing = True
        self.cancel_event.clear()
        self.btn_sync_usb.configure(state="disabled")

        def worker():
            def on_progress(idx, total, filename, frac):
                self.after(0, lambda: self.bar_sync.set(frac))
                self.after(0, lambda: self.lbl_sync_percent.configure(text=f"{frac*100:.1f}% ({idx}/{total})"))
                self.after(0, lambda: self.lbl_copying_file.configure(text=f"Copiando [{idx}/{total}]: {filename[:55]}"))

            ok, msg = sync_to_usb(usb_letter, progress_callback=on_progress, cancel_event=self.cancel_event)
            def finished():
                self.is_syncing = False
                self.btn_sync_usb.configure(state="normal")
                self.async_check_pending()
                if ok:
                    messagebox.showinfo("Sincronización Exitosa", msg)
                else:
                    messagebox.showerror("Aviso", msg)
                if self.on_usb_action_finished:
                    self.on_usb_action_finished()
            self.after(0, finished)

        threading.Thread(target=worker, daemon=True).start()

    def action_format_usb(self):
        if not self.usb_devices:
            messagebox.showerror("Error", "No se detectó ningún dispositivo USB.")
            return

        selected_str = self.combo_usb.get()
        disk_index = None
        for d in self.usb_devices:
            if f"Disco {d.get('Index')}" in selected_str:
                disk_index = d.get("Index")
                break

        if disk_index is None:
            messagebox.showerror("Error", "Selecciona una memoria USB válida.")
            return

        confirm = messagebox.askyesno(
            "⚠️ Confirmar Formateo Total de USB",
            f"¡ATENCIÓN!\n\n¿Estás seguro de preparar y formatear el DISCO #{disk_index}?\n\n"
            f"• Se borrarán todas las particiones existentes.\n"
            f"• Se creará una sola partición limpia en FAT32 con el nombre 'MUSICA'.\n\n"
            f"¿Deseas continuar?"
        )
        if not confirm:
            return

        def worker():
            ok, msg = format_usb_drive(disk_index, label="MUSICA", filesystem="FAT32")
            self.after(0, self.refresh_usb_drives)
            if ok:
                messagebox.showinfo("Éxito", f"¡Memoria USB formateada con éxito!\n\nUnidad asignada: {msg}\nYa puedes sincronizar tus canciones.")
            else:
                messagebox.showerror("Error de Formateo", f"No se pudo completar el formateo:\n{msg}")
            if self.on_usb_action_finished:
                self.after(0, self.on_usb_action_finished)

        threading.Thread(target=worker, daemon=True).start()
