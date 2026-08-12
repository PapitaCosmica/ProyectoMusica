# -*- coding: utf-8 -*-
"""Gestor de tareas en segundo plano, concurrencia y guardrails de seguridad."""

import os
import time
import json
import threading

class TaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.active_tasks = {}
        self.task_lock = threading.Lock()

    def register_task(self, task_id, task_type, description):
        """Registra una tarea activa. Retorna (True, None) o (False, mensaje_conflicto)."""
        with self.task_lock:
            # Guardrails de concurrencia:
            if task_type == "FORMAT":
                if any(t["type"] in ["USB_SYNC", "DOWNLOAD", "SYNC"] for t in self.active_tasks.values()):
                    return False, "⚠️ No se puede formatear el disco mientras hay una descarga o sincronización en curso."
            elif task_type == "USB_SYNC":
                if any(t["type"] in ["FORMAT"] for t in self.active_tasks.values()):
                    return False, "⚠️ No se puede sincronizar a la USB mientras se está formateando la memoria."
            elif task_type == "SYNC":
                if any(t["type"] in ["FORMAT"] for t in self.active_tasks.values()):
                    return False, "⚠️ No se puede reorganizar la colección mientras se formatea el almacenamiento."

            self.active_tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "description": description,
                "start_time": time.time(),
                "progress": 0.0,
                "status_text": "Iniciando..."
            }
            return True, None

    def update_task(self, task_id, progress=None, status_text=None):
        with self.task_lock:
            if task_id in self.active_tasks:
                if progress is not None:
                    self.active_tasks[task_id]["progress"] = progress
                if status_text is not None:
                    self.active_tasks[task_id]["status_text"] = status_text

    def unregister_task(self, task_id):
        with self.task_lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    def get_active_tasks_count(self):
        with self.task_lock:
            return len(self.active_tasks)

    def get_active_tasks_summary(self):
        with self.task_lock:
            if not self.active_tasks:
                return "Inactivo", 0
            types = [t["description"] for t in self.active_tasks.values()]
            return ", ".join(types), len(self.active_tasks)

    def is_any_busy(self):
        with self.task_lock:
            return len(self.active_tasks) > 0

task_manager = TaskManager()
