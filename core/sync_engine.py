# -*- coding: utf-8 -*-
"""Motor de Sincronización, Desduplicación y Organización de Música."""

import os
import re
import shutil
import hashlib
from collections import defaultdict
from .config import BASE_DIR, load_config
from .task_manager import task_manager

def sanitize_filename(filename):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip('. ')
    return cleaned if cleaned else "Pista_Sin_Nombre"

def clean_music_title(title):
    if not title:
        return ""
    junk_patterns = [
        r'\s*[\(\[]\s*(official|oficial)\s*(music\s*)?(video|audio|visualizer|lyric\s*video|clip)\s*[\)\]]',
        r'\s*[\(\[]\s*(video|audio|visualizer|lyric\s*video|letra|video\s*con\s*letra)\s*(oficial|official)?\s*[\)\]]',
        r'\s*[\(\[]\s*remaster(ed)?(\s*\d{4})?\s*[\)\]]',
        r'\s*[\(\[]\s*en\s*vivo\s*[\)\]]',
        r'\s*[\(\[]\s*live(\s*\d{4})?\s*[\)\]]',
        r'\s*\|\s*AVC\s*',
        r'\s*\|\s*Video\s*Oficial\s*',
        r'\s*\|\s*Audio\s*Oficial\s*',
        r'\s*-\s*Video\s*Oficial\s*',
        r'\s*-\s*Audio\s*Oficial\s*',
        r'\s*-\s*Official\s*Video\s*',
    ]
    for pattern in junk_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    return title.strip()

def strip_track_prefix(name):
    if not name:
        return ""
    name = re.sub(r'^\d{1,4}\s*-\s+', '', name)
    name = re.sub(r'^\d{1,4}\.\s+', '', name)
    return name.strip()

def clean_artist_name(artist):
    if not artist:
        return "Artista Desconocido"
    parts = re.split(r'[,;/]', artist)
    if len(parts) > 2:
        artist = ", ".join([p.strip() for p in parts[:2]])
    else:
        artist = artist.strip()
    if len(artist) > 40:
        artist = artist[:40].strip()
    return artist

def normalize_for_comparison(text):
    if not text:
        return ""
    text = text.lower()
    replacements = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ñ':'n', 'ü':'u'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[\(\[]\s*(feat|ft|with|con)\.?\s+.*?[\)\]]', '', text)
    text = re.sub(r'[^a-z0-9]', '', text)
    return text.strip()

def get_audio_info(filepath):
    title = ""
    artist = ""
    album = "Varios"
    bitrate = 0
    size_bytes = 0
    try:
        size_bytes = os.path.getsize(filepath)
    except Exception:
        pass

    try:
        from mutagen.easyid3 import EasyID3
        from mutagen.mp3 import MP3

        try:
            mp3_obj = MP3(filepath)
            if mp3_obj.info and hasattr(mp3_obj.info, 'bitrate'):
                bitrate = mp3_obj.info.bitrate
        except Exception:
            pass

        try:
            audio = EasyID3(filepath)
            title = audio.get('title', [''])[0]
            artist = audio.get('artist', [''])[0]
            album = audio.get('album', ['Varios'])[0]
        except Exception:
            pass
    except ImportError:
        pass

    fname = os.path.basename(filepath)
    raw_name, _ = os.path.splitext(fname)

    if not title:
        cleaned_raw = strip_track_prefix(clean_music_title(raw_name))
        if " - " in cleaned_raw:
            parts = cleaned_raw.split(" - ", 1)
            artist = artist or parts[0].strip()
            title = parts[1].strip()
        else:
            title = cleaned_raw

    return {
        "path": filepath,
        "title": title.strip(),
        "artist": artist.strip(),
        "album": album.strip() or "Varios",
        "bitrate": bitrate,
        "size": size_bytes,
        "raw_name": raw_name
    }

def fix_id3_for_car_players(filepath):
    """Guarda ID3v2.3 con UTF-16 para estéreos de autos y reproductores de música."""
    try:
        from mutagen.id3 import ID3
        try:
            id3 = ID3(filepath)
            id3.save(filepath, v2_version=3)
        except Exception:
            pass
    except Exception:
        pass

def build_destination_path(info, target_root, structure="flat"):
    title = clean_music_title(info["title"] or strip_track_prefix(info["raw_name"]))
    artist = clean_artist_name(clean_music_title(info["artist"]))
    album = sanitize_filename(clean_music_title(info["album"])) or "Sencillos"

    if artist and artist.lower() in title.lower() and " - " in title:
        file_base = title
    elif artist and title:
        file_base = f"{artist} - {title}"
    else:
        file_base = title or strip_track_prefix(info["raw_name"])

    file_base = sanitize_filename(file_base)
    if len(file_base) > 110:
        file_base = file_base[:110].strip('. ')
    filename = f"{file_base}.mp3"

    if structure == "by_album":
        dest_dir = os.path.join(target_root, sanitize_filename(artist), album)
    elif structure == "by_artist":
        dest_dir = os.path.join(target_root, sanitize_filename(artist))
    else:
        dest_dir = target_root

    os.makedirs(dest_dir, exist_ok=True)
    return os.path.join(dest_dir, filename)

def consolidate_and_deduplicate(dry_run=False, progress_callback=None):
    ok, conflict_msg = task_manager.register_task("sync_task", "SYNC", "Sincronizando y Desduplicando")
    if not ok:
        if progress_callback: progress_callback(0, 1, conflict_msg)
        return False, conflict_msg

    config = load_config()
    target_rel = config.get("target_folder", "Musica")
    target_dir = os.path.join(BASE_DIR, target_rel)
    structure = config.get("organization_structure", "flat")
    os.makedirs(target_dir, exist_ok=True)

    all_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            full_p = os.path.join(root, f)
            if f.lower().endswith(".mp3"):
                all_files.append(full_p)

    total_files = len(all_files)
    if not all_files:
        task_manager.unregister_task("sync_task")
        return True, "No hay canciones para procesar."

    audio_items = []
    for idx, p in enumerate(all_files, 1):
        info = get_audio_info(p)
        audio_items.append(info)
        if progress_callback and idx % 50 == 0:
            progress_callback(idx, total_files, "Analizando metadatos...")

    grouped_by_key = defaultdict(list)
    for item in audio_items:
        norm_art = normalize_for_comparison(item["artist"])
        norm_tit = normalize_for_comparison(item["title"] or clean_music_title(item["raw_name"]))
        key = (norm_art, norm_tit) if norm_art else ("", norm_tit)
        grouped_by_key[key].append(item)

    unique_count = len(grouped_by_key)
    moved_count = 0
    removed_dups = 0
    current_step = 0

    for key, items in grouped_by_key.items():
        current_step += 1
        items_sorted = sorted(items, key=lambda x: (x["bitrate"], x["size"]), reverse=True)
        best_item = items_sorted[0]
        duplicates = items_sorted[1:]

        target_file_path = build_destination_path(best_item, target_dir, structure=structure)
        src_path = best_item["path"]

        if not dry_run and os.path.exists(src_path):
            if os.path.abspath(src_path) != os.path.abspath(target_file_path):
                try:
                    if os.path.exists(target_file_path):
                        ex_info = get_audio_info(target_file_path)
                        if (best_item["bitrate"], best_item["size"]) > (ex_info["bitrate"], ex_info["size"]):
                            os.remove(target_file_path)
                            shutil.move(src_path, target_file_path)
                            fix_id3_for_car_players(target_file_path)
                            moved_count += 1
                        else:
                            try: os.remove(src_path)
                            except Exception: pass
                    else:
                        shutil.move(src_path, target_file_path)
                        fix_id3_for_car_players(target_file_path)
                        moved_count += 1
                except Exception:
                    pass
            else:
                fix_id3_for_car_players(target_file_path)

            for dup in duplicates:
                dup_p = dup["path"]
                if os.path.exists(dup_p) and os.path.abspath(dup_p) != os.path.abspath(target_file_path):
                    try:
                        os.remove(dup_p)
                        removed_dups += 1
                    except Exception:
                        pass

        if progress_callback and (current_step % 20 == 0 or current_step == unique_count):
            progress_callback(current_step, unique_count, os.path.basename(target_file_path))

    task_manager.unregister_task("sync_task")
    return True, f"Proceso finalizado. {moved_count} canciones organizadas, {removed_dups} duplicados eliminados."
