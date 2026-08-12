# -*- coding: utf-8 -*-
"""
Punto de entrada principal para MusicSync Studio Pro.
Inicia la ventana principal directamente con el modo configurado o el Hub inicial.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import load_config
from gui.main_window import MainWindow

def main():
    config = load_config()

    # Prioridad 1: Argumentos explícitos por CLI
    if "--full" in sys.argv:
        mode = "full"
    elif "--quick" in sys.argv or "--sync" in sys.argv:
        mode = "sync_usb"
    elif "--usb" in sys.argv:
        mode = "usb_only"
    elif "--hub" in sys.argv:
        mode = "hub"
    else:
        remember = config.get("remember_launch_mode", False)
        default_mode = config.get("default_launch_mode", "hub")
        mode = default_mode if (remember and default_mode) else "hub"

    app = MainWindow(mode=mode)
    app.mainloop()

if __name__ == '__main__':
    main()
