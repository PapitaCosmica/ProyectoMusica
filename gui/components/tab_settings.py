# -*- coding: utf-8 -*-
"""Pestaña de Ajustes: Gestor de Rutas, Historial, Cookies, Estructura y Automatización."""

import os
import subprocess
from tkinter import messagebox, filedialog
import customtkinter as ctk
from core.config import (
    BASE_DIR, load_config, save_config,
    get_historial_path, get_cookies_path, get_historial_count,
    open_path_in_explorer, open_file_in_editor
)
from core.sync_engine import consolidate_and_deduplicate

class TabSettings(ctk.CTkScrollableFrame):
    def __init__(self, master, on_reorganize_finished=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_reorganize_finished = on_reorganize_finished
        self.setup_ui()

    def setup_ui(self):
        # 1. Cabecera Principal
        header = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        header.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            header,
            text="⚙️ Configuración del Sistema & Gestor de Rutas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            header,
            text="Consulta y modifica las rutas del historial de descargas, cookies de YouTube, carpetas de música y automatizaciones.",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # 2. Tarjeta: Gestor de Rutas y Archivos del Sistema
        paths_card = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        paths_card.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(
            paths_card,
            text="📁 Rutas de Archivos y Almacenamiento",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f4f4f5"
        ).pack(anchor="w", padx=14, pady=(12, 6))

        config = load_config()

        # Fila 1: Carpeta de Música Local (PC)
        f_local = ctk.CTkFrame(paths_card, fg_color="#1e1e24", corner_radius=8)
        f_local.pack(fill="x", padx=12, pady=4)

        top_l = ctk.CTkFrame(f_local, fg_color="transparent")
        top_l.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(top_l, text="📂 Carpeta Colección Local (PC):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10b981").pack(side="left")

        self.lbl_src_path = ctk.CTkLabel(
            f_local,
            text=config.get("source_folder", os.path.join(BASE_DIR, "Musica")),
            font=ctk.CTkFont(size=11),
            text_color="#e4e4e7",
            anchor="w"
        )
        self.lbl_src_path.pack(fill="x", padx=10, pady=2)

        ctrl_l = ctk.CTkFrame(f_local, fg_color="transparent")
        ctrl_l.pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkButton(
            ctrl_l,
            text="📁 Cambiar Carpeta...",
            width=130,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.action_change_source_folder
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_l,
            text="📂 Abrir en Explorador",
            width=140,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=lambda: open_path_in_explorer(config.get("source_folder", os.path.join(BASE_DIR, "Musica")))
        ).pack(side="left")

        # Fila 2: Archivo Historial de Descargas (historial.txt)
        f_hist = ctk.CTkFrame(paths_card, fg_color="#1e1e24", corner_radius=8)
        f_hist.pack(fill="x", padx=12, pady=4)

        top_h = ctk.CTkFrame(f_hist, fg_color="transparent")
        top_h.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(top_h, text="📄 Archivo Historial de Descargas (historial.txt):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#6366f1").pack(side="left")
        
        self.lbl_hist_count = ctk.CTkLabel(
            top_h,
            text=f"✔ {get_historial_count()} pistas registradas",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_hist_count.pack(side="right")

        self.lbl_hist_path = ctk.CTkLabel(
            f_hist,
            text=get_historial_path(),
            font=ctk.CTkFont(size=11),
            text_color="#e4e4e7",
            anchor="w"
        )
        self.lbl_hist_path.pack(fill="x", padx=10, pady=2)

        ctrl_h = ctk.CTkFrame(f_hist, fg_color="transparent")
        ctrl_h.pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkButton(
            ctrl_h,
            text="📁 Cambiar Archivo...",
            width=130,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.action_change_historial_file
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_h,
            text="✏️ Ver / Editar en Bloc de Notas",
            width=180,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=lambda: open_file_in_editor(get_historial_path())
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            ctrl_h,
            text="📂 Abrir Carpeta",
            width=110,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=lambda: open_path_in_explorer(os.path.dirname(get_historial_path()))
        ).pack(side="left")

        # Fila 3: Archivo de Cookies de YouTube
        f_cookies = ctk.CTkFrame(paths_card, fg_color="#1e1e24", corner_radius=8)
        f_cookies.pack(fill="x", padx=12, pady=(4, 12))

        top_c = ctk.CTkFrame(f_cookies, fg_color="transparent")
        top_c.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(top_c, text="🍪 Archivo de Cookies de YouTube:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f59e0b").pack(side="left")

        self.lbl_cookies_path = ctk.CTkLabel(
            f_cookies,
            text=get_cookies_path(),
            font=ctk.CTkFont(size=11),
            text_color="#e4e4e7",
            anchor="w"
        )
        self.lbl_cookies_path.pack(fill="x", padx=10, pady=2)

        ctrl_c = ctk.CTkFrame(f_cookies, fg_color="transparent")
        ctrl_c.pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkButton(
            ctrl_c,
            text="📁 Seleccionar Cookies (JSON / TXT)...",
            width=210,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.action_change_cookies_file
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_c,
            text="✏️ Ver Archivo",
            width=100,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#27272a",
            hover_color="#3f3f46",
            command=lambda: open_file_in_editor(get_cookies_path())
        ).pack(side="left")

        # 3. Tarjeta: Estructura de Organización
        struct_card = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        struct_card.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(
            struct_card,
            text="🗂️ Organización de Carpetas & Formato MP3 ID3v2.3",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f4f4f5"
        ).pack(anchor="w", padx=14, pady=(12, 4))

        current_structure = config.get("organization_structure", "flat")
        self.var_structure = ctk.StringVar(value=current_structure)

        ctk.CTkRadioButton(
            struct_card,
            text="📁 Plano: Todas en 'Musica/Artista - Canción.mp3' (Recomendado para estéreos de auto)",
            variable=self.var_structure,
            value="flat",
            font=ctk.CTkFont(size=12),
            command=self.save_structure_setting
        ).pack(anchor="w", padx=16, pady=6)

        ctk.CTkRadioButton(
            struct_card,
            text="📂 Por Álbum: 'Musica/Artista/Álbum/Canción.mp3' (Ideal para reproductores avanzados)",
            variable=self.var_structure,
            value="by_album",
            font=ctk.CTkFont(size=12),
            command=self.save_structure_setting
        ).pack(anchor="w", padx=16, pady=6)

        ctk.CTkRadioButton(
            struct_card,
            text="👤 Por Artista: 'Musica/Artista/Canción.mp3'",
            variable=self.var_structure,
            value="by_artist",
            font=ctk.CTkFont(size=12),
            command=self.save_structure_setting
        ).pack(anchor="w", padx=16, pady=6)

        ctk.CTkButton(
            struct_card,
            text="🔄 Reorganizar Colección con la Estructura Seleccionada",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            command=self.action_reorganize
        ).pack(padx=16, pady=(6, 14), fill="x")

        # 4. Tarjeta: Sincronización Automática en Segundo Plano
        sched_card = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        sched_card.pack(fill="x", padx=12, pady=(6, 14))

        ctk.CTkLabel(
            sched_card,
            text="⏰ Sincronización Automática en Windows (Segundo Plano)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            sched_card,
            text="Configura Windows para que descargue y sincronice nuevas canciones automáticamente cada X horas.",
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        sched_ctrls = ctk.CTkFrame(sched_card, fg_color="transparent")
        sched_ctrls.pack(fill="x", padx=14, pady=(0, 14))

        self.combo_hours = ctk.CTkComboBox(
            sched_ctrls,
            values=["Cada 2 horas", "Cada 4 horas", "Cada 6 horas", "Cada 12 horas", "Diario"],
            width=180,
            state="readonly"
        )
        self.combo_hours.set("Cada 4 horas")
        self.combo_hours.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            sched_ctrls,
            text="🔔 Activar Tarea en Windows",
            fg_color="#10b981",
            hover_color="#059669",
            command=self.action_enable_schedule
        ).pack(side="left")

    def action_change_source_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta principal de tu música")
        if folder and os.path.exists(folder):
            config = load_config()
            config["source_folder"] = folder
            save_config(config)
            self.lbl_src_path.configure(text=folder)
            messagebox.showinfo("Configuración", f"Ruta de música actualizada a:\n{folder}")

    def action_change_historial_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecciona el archivo historial.txt",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filepath and os.path.exists(filepath):
            config = load_config()
            config["historial_file"] = filepath
            save_config(config)
            self.lbl_hist_path.configure(text=filepath)
            self.lbl_hist_count.configure(text=f"✔ {get_historial_count()} pistas registradas")
            messagebox.showinfo("Configuración", f"Archivo de historial vinculado a:\n{filepath}")

    def action_change_cookies_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecciona el archivo de cookies (JSON de Cookie Editor o TXT Netscape)",
            filetypes=[("Archivos de Cookies", "*.json;*.txt"), ("Todos los archivos", "*.*")]
        )
        if filepath and os.path.exists(filepath):
            config = load_config()
            config["cookies_file"] = filepath
            save_config(config)
            self.lbl_cookies_path.configure(text=filepath)
            messagebox.showinfo("Configuración", f"Archivo de cookies vinculado a:\n{filepath}")

    def save_structure_setting(self):
        val = self.var_structure.get()
        config = load_config()
        config["organization_structure"] = val
        save_config(config)

    def action_reorganize(self):
        ok, msg = consolidate_and_deduplicate(dry_run=False)
        if ok:
            messagebox.showinfo("Éxito", f"¡Colección reorganizada exitosamente!\n\n{msg}")
        else:
            messagebox.showerror("Error", msg)
        if self.on_reorganize_finished:
            self.on_reorganize_finished()

    def action_enable_schedule(self):
        hours_map = {
            "Cada 2 horas": 2,
            "Cada 4 horas": 4,
            "Cada 6 horas": 6,
            "Cada 12 horas": 12,
            "Diario": 24
        }
        hours = hours_map.get(self.combo_hours.get(), 4)
        task_name = "Sync_Musica_Auto"
        bat_path = os.path.join(BASE_DIR, "Sincronizar_Musica.bat")

        cmd = [
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", f'"{bat_path}" --auto',
            "/SC", "HOURLY",
            "/MO", str(hours),
            "/F"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                messagebox.showinfo("Programador de Tareas", f"¡Sincronización automática activada para ejecutarse cada {hours} hora(s)!")
            else:
                messagebox.showerror("Error", f"No se pudo crear la tarea:\n{res.stderr or res.stdout}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
