# -*- coding: utf-8 -*-
"""
Script unificado de empaquetado automatico para MusicSync Studio.
Genera el ejecutable portable (.exe) y el archivo ZIP comprimido listo para cualquier PC.
"""

import os
import sys
import shutil
import zipfile
import subprocess

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
APP_NAME = "MusicSync_Studio"
APP_DIR = os.path.join(DIST_DIR, APP_NAME)

def build_and_package():
    print("=" * 60)
    print("[*] INICIANDO EMPAQUETADO UNIFICADO DE MUSICSYNC STUDIO")
    print("=" * 60)

    # 1. Compilar con PyInstaller
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", APP_NAME,
        "--collect-all", "customtkinter",
        "--collect-all", "mutagen",
        os.path.join(BASE_DIR, "app_gui.py")
    ]

    print("[*] Compilando ejecutable...")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print("[!] Error durante la compilacion.")
        return False

    # 2. Copiar complementos y configuraciones
    print(f"[*] Copiando recursos a {APP_DIR}...")
    for fname in ["formatear_usb.cmd", "config.json", "historial.txt", "cookies_netscape.txt"]:
        src = os.path.join(BASE_DIR, fname)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(APP_DIR, fname))
            print(f"  + Copiado: {fname}")

    # 3. Crear lanzador .bat dentro de la carpeta portable
    bat_file = os.path.join(APP_DIR, "Iniciar_MusicSync.bat")
    with open(bat_file, "w", encoding="ascii", errors="ignore") as f:
        f.write("@echo off\r\n")
        f.write("cd /d \"%~dp0\"\r\n")
        f.write("start \"\" \"MusicSync_Studio.exe\"\r\n")
        f.write("exit\r\n")
    print("  + Creado: Iniciar_MusicSync.bat")

    # 4. Crear ZIP portable listo para distribuir
    zip_path = os.path.join(DIST_DIR, "MusicSync_Studio_Portable.zip")
    print(f"[*] Comprimiendo paquete en {zip_path}...")
    if os.path.exists(zip_path):
        try: os.remove(zip_path)
        except Exception: pass

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(APP_DIR):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, APP_DIR)
                zipf.write(full_p, arcname=os.path.join("MusicSync_Studio_Portable", rel_p))

    # 5. Limpieza de carpetas temporales de compilación
    if os.path.exists(BUILD_DIR):
        try: shutil.rmtree(BUILD_DIR)
        except Exception: pass
    spec_file = os.path.join(BASE_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec_file):
        try: os.remove(spec_file)
        except Exception: pass

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print("=" * 60)
    print("[✔] EMPAQUETADO FINALIZADO CON EXITO")
    print(f"[*] Archivo ZIP listo para llevar a otras PCs: {zip_path} ({zip_size_mb:.2f} MB)")
    print(f"[*] Carpeta Ejecutable Portable: {APP_DIR}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    build_and_package()
