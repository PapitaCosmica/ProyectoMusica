# -*- coding: utf-8 -*-
"""Gestor de cola de reproducción, metadatos y carátulas con soporte multi-carpeta."""

import os
import io
import random
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

from core.config import BASE_DIR, load_config, save_config
from .audio_engine import audio_player

class PlaylistQueue:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlaylistQueue, cls).__new__(cls)
            cls._instance._init_queue()
        return cls._instance

    def _init_queue(self):
        self.tracks = []  # Lista de rutas absolutas
        self.current_index = -1
        self.shuffle = False
        self.repeat = False
        config = load_config()
        self.library_dir = config.get("active_library_folder") or config.get("source_folder") or os.path.join(BASE_DIR, "Musica")

    def set_library_folder(self, folder_path):
        """Cambia la carpeta activa que lee el reproductor de música."""
        if folder_path and os.path.exists(folder_path):
            self.library_dir = folder_path
            config = load_config()
            config["active_library_folder"] = folder_path
            save_config(config)
            return self.load_library_tracks(force_refresh=True)
        return self.tracks

    def get_current_library_folder(self):
        return self.library_dir

    def load_library_tracks(self, force_refresh=False):
        """Carga todas las canciones de la carpeta activa de forma ultra rápida."""
        if self.tracks and not force_refresh:
            return self.tracks

        target_dir = self.library_dir
        self.tracks = []
        if os.path.exists(target_dir):
            try:
                entries = []
                with os.scandir(target_dir) as it:
                    for entry in it:
                        if entry.is_file() and entry.name.lower().endswith(".mp3"):
                            entries.append(entry.path)
                        elif entry.is_dir():
                            for root, _, files in os.walk(entry.path):
                                for f in files:
                                    if f.lower().endswith(".mp3"):
                                        entries.append(os.path.join(root, f))
                self.tracks = sorted(entries)
            except Exception as e:
                print(f"[!] Error listando archivos de biblioteca: {e}")
        return self.tracks

    def get_track_metadata(self, filepath):
        """Lee título, artista, duración y carátula de un archivo MP3."""
        meta = {
            "path": filepath,
            "title": os.path.splitext(os.path.basename(filepath))[0],
            "artist": "Desconocido",
            "album": "Varios",
            "duration": 0,
            "duration_str": "0:00",
            "cover_image": None
        }

        if not filepath or not os.path.exists(filepath):
            return meta

        try:
            mp3_obj = MP3(filepath)
            if mp3_obj.info:
                meta["duration"] = int(mp3_obj.info.length)
                mins = meta["duration"] // 60
                secs = meta["duration"] % 60
                meta["duration_str"] = f"{mins}:{secs:02d}"

            try:
                audio = EasyID3(filepath)
                meta["title"] = audio.get("title", [meta["title"]])[0]
                meta["artist"] = audio.get("artist", ["Desconocido"])[0]
                meta["album"] = audio.get("album", ["Varios"])[0]
            except Exception:
                pass

            # Extraer carátula si existe
            try:
                id3 = ID3(filepath)
                for tag in id3.values():
                    if isinstance(tag, APIC):
                        img_data = tag.data
                        img = Image.open(io.BytesIO(img_data)).convert("RGB")
                        meta["cover_image"] = img
                        break
            except Exception:
                pass
        except Exception as e:
            print(f"[!] Error leyendo metadatos de pista: {e}")

        return meta

    def play_index(self, index):
        if not self.tracks:
            self.load_library_tracks()
        if 0 <= index < len(self.tracks):
            self.current_index = index
            track = self.tracks[self.current_index]
            audio_player.play(track)
            return self.get_track_metadata(track)
        return None

    def play_track(self, filepath):
        if filepath in self.tracks:
            self.current_index = self.tracks.index(filepath)
        else:
            self.tracks.append(filepath)
            self.current_index = len(self.tracks) - 1
        audio_player.play(filepath)
        return self.get_track_metadata(filepath)

    def next_track(self):
        if not self.tracks:
            return None
        if self.shuffle:
            self.current_index = random.randint(0, len(self.tracks) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.tracks)
        return self.play_index(self.current_index)

    def prev_track(self):
        if not self.tracks:
            return None
        self.current_index = (self.current_index - 1) % len(self.tracks)
        return self.play_index(self.current_index)

    def get_current_metadata(self):
        if 0 <= self.current_index < len(self.tracks):
            return self.get_track_metadata(self.tracks[self.current_index])
        return None

playlist_queue = PlaylistQueue()
