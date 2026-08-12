# -*- coding: utf-8 -*-
"""Puente de compatibilidad hacia el motor modular en core/sync_engine.py."""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.sync_engine import *
from core.downloader import download_playlists
from core.usb_manager import format_usb_drive, sync_to_usb, list_all_usb_devices

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MusicSync Engine CLI")
    parser.add_argument("--download", action="store_true", help="Descargar playlists")
    parser.add_argument("--sync", action="store_true", help="Sincronizar y desduplicar")
    args = parser.parse_args()

    if args.download:
        download_playlists(progress_callback=print)
    elif args.sync:
        consolidate_and_deduplicate(dry_run=False, progress_callback=lambda c, t, m: print(f"[{c}/{t}] {m}"))
