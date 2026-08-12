# -*- coding: utf-8 -*-
"""Gestor de dispositivos USB, formateo universal FAT32 MBR y sincronización incremental precisa."""

import os
import time
import json
import psutil
import shutil
import ctypes
import subprocess
from .config import BASE_DIR, load_config, record_sync_event
from .task_manager import task_manager

def list_all_usb_devices():
    """Detecta todos los discos USB físicos y sus letras de partición."""
    devices = []
    try:
        script = """
        Get-CimInstance Win32_DiskDrive | Where-Object InterfaceType -eq 'USB' | ForEach-Object {
            $disk = $_
            $partitions = Get-CimInstance -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($disk.DeviceID)'} WHERE AssocClass = Win32_DiskDriveToDiskPartition"
            $letters = @()
            foreach ($part in $partitions) {
                $logical = Get-CimInstance -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($part.DeviceID)'} WHERE AssocClass = Win32_LogicalDiskToPartition"
                foreach ($log in $logical) {
                    if ($log.DeviceID) { $letters += $log.DeviceID }
                }
            }
            [PSCustomObject]@{
                Index = $disk.Index
                Name = $disk.Caption
                SizeGB = [math]::Round($disk.Size / 1GB, 2)
                Letters = ($letters -join ', ')
                DeviceID = $disk.DeviceID
            }
        } | ConvertTo-Json
        """
        res = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
        if res.stdout.strip():
            raw = json.loads(res.stdout)
            if isinstance(raw, dict):
                devices.append(raw)
            elif isinstance(raw, list):
                devices.extend(raw)
    except Exception as e:
        print(f"[!] Error detectando discos USB: {e}")
    return devices

def get_storage_diagnostics(usb_letter=None):
    """Devuelve estadísticas de espacio y porcentajes para disco local y USB."""
    config = load_config()
    src_dir = config.get("source_folder") or os.path.join(BASE_DIR, "Musica")

    stats = {
        "local": {
            "path": src_dir,
            "drive": os.path.splitdrive(src_dir)[0] or "D:",
            "total_gb": 0,
            "used_gb": 0,
            "free_gb": 0,
            "percent": 0.0
        },
        "usb": None
    }

    try:
        local_usage = psutil.disk_usage(src_dir if os.path.exists(src_dir) else BASE_DIR)
        stats["local"]["total_gb"] = round(local_usage.total / (1024**3), 2)
        stats["local"]["used_gb"] = round(local_usage.used / (1024**3), 2)
        stats["local"]["free_gb"] = round(local_usage.free / (1024**3), 2)
        stats["local"]["percent"] = local_usage.percent
    except Exception:
        pass

    if usb_letter and os.path.exists(f"{usb_letter}\\"):
        try:
            usb_usage = psutil.disk_usage(f"{usb_letter}\\")
            stats["usb"] = {
                "drive": usb_letter,
                "total_gb": round(usb_usage.total / (1024**3), 2),
                "used_gb": round(usb_usage.used / (1024**3), 2),
                "free_gb": round(usb_usage.free / (1024**3), 2),
                "percent": usb_usage.percent
            }
        except Exception:
            pass

    return stats

def get_pending_sync_metrics(usb_letter, src_dir=None):
    """Calcula con precisión matemática cuántas canciones faltan por sincronizar a la memoria USB."""
    if not usb_letter or not os.path.exists(f"{usb_letter}\\"):
        return {"pending_files": [], "pending_count": 0, "local_count": 0, "usb_count": 0, "status": "USB no conectada"}

    config = load_config()
    if not src_dir:
        src_dir = config.get("source_folder") or os.path.join(BASE_DIR, "Musica")

    usb_subfolder = config.get("usb_target_folder", "Musica")
    usb_dir = os.path.join(f"{usb_letter}\\", usb_subfolder)

    # 1. Mapear archivos locales
    local_map = {}  # {rel_path_lower: full_path}
    if os.path.exists(src_dir):
        for root, _, files in os.walk(src_dir):
            for f in files:
                if f.lower().endswith(".mp3"):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, src_dir)
                    local_map[rel.lower()] = (rel, full)

    # 2. Mapear archivos en USB
    usb_map = set()
    if os.path.exists(usb_dir):
        for root, _, files in os.walk(usb_dir):
            for f in files:
                if f.lower().endswith(".mp3"):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, usb_dir)
                    usb_map.add(rel.lower())

    # 3. Diferencia
    missing_keys = set(local_map.keys()) - usb_map
    pending_items = [local_map[k] for k in missing_keys]  # [(rel, full), ...]

    return {
        "pending_files": pending_items,
        "pending_count": len(pending_items),
        "local_count": len(local_map),
        "usb_count": len(usb_map),
        "usb_dir": usb_dir,
        "src_dir": src_dir,
        "status": f"{len(pending_items)} canciones pendientes" if pending_items else "✔ Toda tu colección está sincronizada"
    }

def sync_to_usb(usb_letter, progress_callback=None, cancel_event=None):
    """Sincroniza la música de forma incremental y precisa en Python con feedback en vivo."""
    ok, conflict_msg = task_manager.register_task("usb_sync_task", "USB_SYNC", f"Sincronizando a {usb_letter}")
    if not ok:
        return False, conflict_msg

    config = load_config()
    src_dir = config.get("source_folder") or os.path.join(BASE_DIR, "Musica")
    usb_subfolder = config.get("usb_target_folder", "Musica")
    usb_dir = os.path.join(f"{usb_letter}\\", usb_subfolder)

    if not os.path.exists(src_dir):
        task_manager.unregister_task("usb_sync_task")
        return False, f"No existe la carpeta origen '{src_dir}'."

    os.makedirs(usb_dir, exist_ok=True)

    # Obtener canciones faltantes
    metrics = get_pending_sync_metrics(usb_letter, src_dir=src_dir)
    pending_items = metrics["pending_files"]
    total_to_copy = len(pending_items)

    if total_to_copy == 0:
        task_manager.unregister_task("usb_sync_task")
        record_sync_event(usb_letter, metrics["local_count"])
        return True, "Tu memoria USB ya tiene todas las canciones de tu colección. ¡Está 100% al día!"

    copied = 0
    errors = 0

    for idx, (rel_path, full_src) in enumerate(pending_items, 1):
        if cancel_event and cancel_event.is_set():
            break

        dest_file = os.path.join(usb_dir, rel_path)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        try:
            shutil.copy2(full_src, dest_file)
            copied += 1
        except Exception as e:
            errors += 1

        if progress_callback:
            frac = idx / total_to_copy
            fname = os.path.basename(rel_path)
            progress_callback(idx, total_to_copy, fname, frac)

    record_sync_event(usb_letter, metrics["local_count"])
    task_manager.unregister_task("usb_sync_task")

    if cancel_event and cancel_event.is_set():
        return False, f"Sincronización pausada. Se copiaron {copied} de {total_to_copy} canciones."

    return True, f"¡Sincronización completada con éxito! Se copiaron {copied} canciones nuevas a la memoria USB ({usb_letter})."

def format_usb_drive(disk_index, label="MUSICA", filesystem="FAT32"):
    """Limpia particiones corruptas y formatea el disco USB en FAT32 MBR con ShellExecuteW."""
    ok, conflict_msg = task_manager.register_task("format_task", "FORMAT", f"Formateando Disco {disk_index}")
    if not ok:
        return False, conflict_msg

    try:
        cmd_path = os.path.join(BASE_DIR, "formatear_usb.cmd")
        done_file = os.path.join(BASE_DIR, ".usb_format_done.txt")

        if os.path.exists(done_file):
            try: os.remove(done_file)
            except Exception: pass

        params = f'/c "{cmd_path}" {disk_index}'
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, BASE_DIR, 1)

        if ret <= 32:
            task_manager.unregister_task("format_task")
            return False, "La operación fue cancelada o no se otorgaron permisos de Administrador."

        for _ in range(60):
            time.sleep(1)
            if os.path.exists(done_file):
                try: os.remove(done_file)
                except Exception: pass

                time.sleep(1)
                devices = list_all_usb_devices()
                letter = "E:"
                for d in devices:
                    if d.get("Index") == int(disk_index):
                        letters = d.get("Letters", "").split(",")
                        for l in letters:
                            l = l.strip()
                            if l:
                                letter = l
                                break
                task_manager.unregister_task("format_task")
                return True, letter

        task_manager.unregister_task("format_task")
        return False, "El formateo tardó demasiado tiempo o la ventana fue cerrada."
    except Exception as e:
        task_manager.unregister_task("format_task")
        return False, str(e)
