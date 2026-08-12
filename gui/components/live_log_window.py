# -*- coding: utf-8 -*-
"""Ventana Flotante de Logs y Registro en Tiempo Real para MusicSync Studio."""

import time
from tkinter import filedialog, messagebox
import customtkinter as ctk
from core.task_manager import task_manager

class LiveLogWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("📋 Registro en Tiempo Real (Live Logs) - MusicSync Studio")
        self.geometry("780x520")
        self.minsize(600, 380)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.auto_scroll = True
        self.current_filter = "TODOS"

        self.setup_ui()
        self.load_initial_history()

        # Registrarse como observador en el bus de logs
        task_manager.add_log_listener(self.on_new_log_entry)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # 1. Barra de Herramientas Superior
        toolbar = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10, height=48)
        toolbar.pack(fill="x", padx=12, pady=(12, 6))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar,
            text="⚡ Logs en Vivo:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#10b981"
        ).pack(side="left", padx=(12, 8), pady=8)

        # Filtro de Niveles
        self.combo_filter = ctk.CTkComboBox(
            toolbar,
            values=["TODOS", "INFO / DESCARGAS", "ADVERTENCIAS", "ERRORES"],
            width=170,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self.on_filter_changed,
            state="readonly"
        )
        self.combo_filter.set("TODOS")
        self.combo_filter.pack(side="left", padx=4)

        # Auto-scroll Switch
        self.chk_autoscroll = ctk.CTkCheckBox(
            toolbar,
            text="Seguir al final (Auto-scroll)",
            font=ctk.CTkFont(size=11),
            command=self.toggle_autoscroll
        )
        self.chk_autoscroll.select()
        self.chk_autoscroll.pack(side="left", padx=12)

        # Botón Exportar
        self.btn_export = ctk.CTkButton(
            toolbar,
            text="💾 Guardar Log...",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self.action_export_log
        )
        self.btn_export.pack(side="right", padx=(4, 12))

        # Botón Limpiar
        self.btn_clear = ctk.CTkButton(
            toolbar,
            text="🧹 Limpiar",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#3f3f46",
            hover_color="#ef4444",
            command=self.action_clear
        )
        self.btn_clear.pack(side="right", padx=4)

        # 2. Caja de Texto de Logs (Estilo Terminal Hacker/Studio)
        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#09090b",
            text_color="#e4e4e7",
            corner_radius=10,
            wrap="word"
        )
        self.textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.textbox.configure(state="disabled")

    def load_initial_history(self):
        history = task_manager.get_log_history()
        for entry in history:
            self.append_log_line(entry)

    def on_new_log_entry(self, entry):
        self.after(0, lambda: self.append_log_line(entry))

    def append_log_line(self, entry):
        level = entry.get("level", "INFO").upper()
        msg = entry.get("message", "")
        t = entry.get("time", time.strftime("%H:%M:%S"))

        # Aplicar Filtro
        if self.current_filter == "ERRORES" and "ERROR" not in level and "!" not in msg and "err" not in msg.lower():
            return
        elif self.current_filter == "ADVERTENCIAS" and "WARN" not in level and "⚠️" not in msg and "advertencia" not in msg.lower():
            return
        elif self.current_filter == "INFO / DESCARGAS" and "ERROR" in level:
            return

        # Formatear Prefijos Visuales
        prefix = f"[{t}] "
        line_text = f"{prefix}{msg}\n"

        try:
            self.textbox.configure(state="normal")
            self.textbox.insert("end", line_text)
            if self.auto_scroll:
                self.textbox.see("end")
            self.textbox.configure(state="disabled")
        except Exception:
            pass

    def on_filter_changed(self, val):
        self.current_filter = val
        self.action_clear()
        self.load_initial_history()

    def toggle_autoscroll(self):
        self.auto_scroll = bool(self.chk_autoscroll.get())

    def action_clear(self):
        try:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.configure(state="disabled")
        except Exception:
            pass

    def action_export_log(self):
        filepath = filedialog.asksaveasfilename(
            title="Guardar Registro de Logs",
            defaultextension=".txt",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if filepath:
            try:
                content = self.textbox.get("1.0", "end")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Éxito", f"Logs exportados correctamente a:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    def on_close(self):
        task_manager.remove_log_listener(self.on_new_log_entry)
        self.destroy()
