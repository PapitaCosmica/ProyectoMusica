# -*- coding: utf-8 -*-
"""Módulo de configuración y persistencia para MusicSync Studio."""

import os
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def get_default_config():
    default_music_dir = os.path.join(BASE_DIR, "Musica")
    return {
        "playlists": [
            {
                "name": "Playlist Principal",
                "url": "https://youtube.com/playlist?list=PLOH9HZ7ecZx8",
                "active": True
            }
        ],
        "source_folder": default_music_dir,    # Ruta completa de la colección local
        "target_folder": "Musica",            # Nombre de subcarpeta relativo por compatibilidad
        "usb_target_folder": "Musica",        # Carpeta destino en USB
        "active_library_folder": default_music_dir, # Carpeta que el reproductor está escuchando actualmente
        "organization_structure": "flat",     # "flat", "by_album", "by_artist"
        "audio_format": "mp3",
        "audio_quality": "320K",
        "id3_version": "v2.3",
        "clean_names": True,
        "remove_old_empty_folders": True,
        "historial_file": "historial.txt",
        "cookies_file": "cookies_netscape.txt",
        "browser_cookies": "edge",            # "edge", "chrome", "firefox", "none"
        "last_sync_timestamp": None,
        "last_sync_target": None,
        "preferred_audio_device": None,
        "default_volume": 0.8,
        "player_enabled": True,
        "remember_launch_mode": False,
        "default_launch_mode": "hub"
    }

def load_config():
    config = get_default_config()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if "playlist_url" in loaded and "playlists" not in loaded:
                    loaded["playlists"] = [{"name": "Playlist Principal", "url": loaded["playlist_url"], "active": True}]
                config.update(loaded)
        except Exception as e:
            print(f"[!] Error leyendo config.json: {e}")
            
    # Validar que source_folder sea absoluta
    if not os.path.isabs(config.get("source_folder", "")):
        config["source_folder"] = os.path.join(BASE_DIR, config.get("source_folder", "Musica"))
    if not os.path.exists(config["source_folder"]):
        try: os.makedirs(config["source_folder"], exist_ok=True)
        except Exception: pass

    return config

def save_config(config_dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[!] Error guardando config.json: {e}")
        return False

def record_sync_event(target_drive, tracks_count):
    config = load_config()
    config["last_sync_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    config["last_sync_target"] = target_drive
    config["last_sync_count"] = tracks_count
    save_config(config)
