# -*- coding: utf-8 -*-
"""
Punto de entrada principal para MusicSync Studio.
Muestra el menú de selección de herramientas (Launcher Hub) o inicia el modo configurado.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import load_config
from gui.launcher_hub import LauncherHub
from gui.main_window import MainWindow

def launch_main_window(mode="full"):
    app = MainWindow(mode=mode)
    app.mainloop()

def main():
    config = load_config()

    # Checar argumentos de línea de comandos
    if "--full" in sys.argv:
        launch_main_window("full")
        return
    elif "--quick" in sys.argv or "--sync" in sys.argv:
        launch_main_window("sync_usb")
        return
    elif "--usb" in sys.argv:
        launch_main_window("usb_only")
        return

    remember = config.get("remember_launch_mode", False)
    default_mode = config.get("default_launch_mode", "hub")

    if remember and default_mode != "hub" and "--hub" not in sys.argv:
        launch_main_window(default_mode)
    else:
        hub = LauncherHub(on_select_mode_callback=launch_main_window)
        hub.mainloop()

if __name__ == '__main__':
    main()
