# -*- coding: utf-8 -*-
"""Pestaña de Ajustes: Estructura por Álbum/Plano, Formato y Automatización."""

import os
import subprocess
from tkinter import messagebox
import customtkinter as ctk
from core.config import BASE_DIR, load_config, save_config
from core.sync_engine import consolidate_and_deduplicate

class TabSettings(ctk.CTkFrame):
    def __init__(self, master, on_reorganize_finished=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_reorganize_finished = on_reorganize_finished
        self.setup_ui()

    def setup_ui(self):
        settings_card = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        settings_card.pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkLabel(
            settings_card,
            text="⚙️ Estructura de Carpetas & Formato para Reproductores",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#10b981"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        config = load_config()
        current_structure = config.get("organization_structure", "flat")

        self.var_structure = ctk.StringVar(value=current_structure)

        opt_frame = ctk.CTkFrame(self, fg_color="#1e1e24", corner_radius=10)
        opt_frame.pack(fill="x", padx=12, pady=8)

        ctk.CTkRadioButton(
            opt_frame,
            text="📁 Plano: Todas en 'Musica/Artista - Canción.mp3' (Recomendado para estéreos de auto sencillos)",
            variable=self.var_structure,
            value="flat",
            font=ctk.CTkFont(size=13),
            command=self.save_structure_setting
        ).pack(anchor="w", padx=16, pady=10)

        ctk.CTkRadioButton(
            opt_frame,
            text="📂 Por Álbum: 'Musica/Artista/Álbum/Canción.mp3' (Ideal para reproductores avanzados)",
            variable=self.var_structure,
            value="by_album",
            font=ctk.CTkFont(size=13),
            command=self.save_structure_setting
        ).pack(anchor="w", padx=16, pady=10)

        ctk.CTkRadioButton(
            opt_frame,
            text="👤 Por Artista: 'Musica/Artista/Canción.mp3'",
            variable=self.var_structure,
            value="by_artist",
            font=ctk.CTkFont(size=13),
            command=self.save_structure_setting
        ).pack(anchor="w", padx=16, pady=10)

        ctk.CTkButton(
            opt_frame,
            text="🔄 Reorganizar Colección con la Estructura Seleccionada",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            command=self.action_reorganize
        ).pack(padx=16, pady=(4, 14), fill="x")

        # Tarea programada en segundo plano
        sched_card = ctk.CTkFrame(self, fg_color="#27272a", corner_radius=10)
        sched_card.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            sched_card,
            text="⏰ Sincronización Automática en Segundo Plano (Windows)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            sched_card,
            text="Configura Windows para que descargue y sincronice nuevas canciones automáticamente cada X horas.",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        sched_ctrls = ctk.CTkFrame(sched_card, fg_color="transparent")
        sched_ctrls.pack(fill="x", padx=14, pady=(0, 12))

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
