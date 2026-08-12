# -*- coding: utf-8 -*-
"""Barra de Reproducción Inferior Persistente (Estilo Spotify) con Selector de Dispositivos."""

import os
import customtkinter as ctk
from PIL import Image
from player.audio_engine import audio_player
from player.playlist_queue import playlist_queue

class PlayerBar(ctk.CTkFrame):
    def __init__(self, master, on_track_change_callback=None, **kwargs):
        super().__init__(master, corner_radius=12, fg_color="#121214", height=90, **kwargs)
        self.pack_propagate(False)
        self.on_track_change_callback = on_track_change_callback

        self.current_meta = None
        self.is_seeking = False
        self.total_duration = 0

        self.setup_ui()
        self.update_device_list()
        self.start_progress_loop()

    def setup_ui(self):
        # 1. Lado Izquierdo: Carátula, Título y Artista
        self.left_box = ctk.CTkFrame(self, fg_color="transparent", width=260)
        self.left_box.pack(side="left", fill="y", padx=16, pady=8)
        self.left_box.pack_propagate(False)

        # Placeholder de carátula
        self.default_cover = Image.new("RGB", (56, 56), color="#27272a")
        self.img_cover_ctk = ctk.CTkImage(light_image=self.default_cover, dark_image=self.default_cover, size=(56, 56))
        self.lbl_cover = ctk.CTkLabel(self.left_box, image=self.img_cover_ctk, text="")
        self.lbl_cover.pack(side="left", padx=(0, 10))

        info_box = ctk.CTkFrame(self.left_box, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        self.lbl_title = ctk.CTkLabel(
            info_box, 
            text="Sin reproducción", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f4f4f5",
            anchor="w"
        )
        self.lbl_title.pack(fill="x", pady=(8, 0))

        self.lbl_artist = ctk.CTkLabel(
            info_box, 
            text="Selecciona una canción", 
            font=ctk.CTkFont(size=11),
            text_color="#a1a1aa",
            anchor="w"
        )
        self.lbl_artist.pack(fill="x")

        # 2. Lado Derecho: Volumen y Selector de Salida de Audio (Voicemeeter/Bluetooth/HDMI)
        self.right_box = ctk.CTkFrame(self, fg_color="transparent", width=300)
        self.right_box.pack(side="right", fill="y", padx=16, pady=8)

        # Selector de Salida de Audio
        dev_box = ctk.CTkFrame(self.right_box, fg_color="transparent")
        dev_box.pack(side="right", fill="x")

        ctk.CTkLabel(dev_box, text="🔊", font=ctk.CTkFont(size=14)).pack(side="left", padx=(4, 4))

        self.slider_vol = ctk.CTkSlider(
            dev_box, 
            from_=0, 
            to=1, 
            number_of_steps=100, 
            width=80, 
            height=12,
            progress_color="#10b981",
            command=self.on_volume_change
        )
        self.slider_vol.set(0.8)
        self.slider_vol.pack(side="left", padx=(0, 10))

        self.combo_audio_dev = ctk.CTkComboBox(
            dev_box,
            values=["Cargando salidas..."],
            width=150,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self.on_device_change,
            state="readonly"
        )
        self.combo_audio_dev.pack(side="left")

        # 3. Centro: Controles Multimedia y Barra de Tiempo
        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Botones de Control
        ctrls = ctk.CTkFrame(self.center_box, fg_color="transparent")
        ctrls.pack(pady=(4, 2))

        self.btn_shuffle = ctk.CTkButton(ctrls, text="🔀", width=32, height=30, font=ctk.CTkFont(size=13), fg_color="transparent", hover_color="#27272a", command=self.toggle_shuffle)
        self.btn_shuffle.pack(side="left", padx=4)

        self.btn_prev = ctk.CTkButton(ctrls, text="⏮️", width=36, height=30, font=ctk.CTkFont(size=14), fg_color="transparent", hover_color="#27272a", command=self.play_prev)
        self.btn_prev.pack(side="left", padx=4)

        self.btn_play = ctk.CTkButton(ctrls, text="▶", width=40, height=40, corner_radius=20, font=ctk.CTkFont(size=16, weight="bold"), fg_color="#10b981", hover_color="#059669", text_color="#000000", command=self.toggle_play_pause)
        self.btn_play.pack(side="left", padx=8)

        self.btn_next = ctk.CTkButton(ctrls, text="⏭️", width=36, height=30, font=ctk.CTkFont(size=14), fg_color="transparent", hover_color="#27272a", command=self.play_next)
        self.btn_next.pack(side="left", padx=4)

        self.btn_loop = ctk.CTkButton(ctrls, text="🔁", width=32, height=30, font=ctk.CTkFont(size=13), fg_color="transparent", hover_color="#27272a", command=self.toggle_loop)
        self.btn_loop.pack(side="left", padx=4)

        # Barra de Tiempo (0:00 --------- 3:45)
        timeline = ctk.CTkFrame(self.center_box, fg_color="transparent")
        timeline.pack(fill="x", padx=20)

        self.lbl_time_cur = ctk.CTkLabel(timeline, text="0:00", font=ctk.CTkFont(size=11), text_color="#71717a", width=35)
        self.lbl_time_cur.pack(side="left")

        self.slider_time = ctk.CTkSlider(
            timeline, 
            from_=0, 
            to=100, 
            height=12,
            progress_color="#10b981",
            command=self.on_seek
        )
        self.slider_time.set(0)
        self.slider_time.pack(side="left", fill="x", expand=True, padx=6)

        self.lbl_time_tot = ctk.CTkLabel(timeline, text="0:00", font=ctk.CTkFont(size=11), text_color="#71717a", width=35)
        self.lbl_time_tot.pack(side="left")

    def update_device_list(self):
        """Carga y muestra todas las salidas de audio disponibles."""
        devices = audio_player.get_available_output_devices()
        self.combo_audio_dev.configure(values=devices)
        if devices:
            self.combo_audio_dev.set(devices[0])

    def on_device_change(self, selected_device):
        audio_player.set_output_device(selected_device)

    def on_volume_change(self, val):
        audio_player.set_volume(val)

    def toggle_play_pause(self):
        if audio_player.is_playing():
            audio_player.pause()
            self.btn_play.configure(text="▶")
        elif audio_player.is_paused:
            audio_player.unpause()
            self.btn_play.configure(text="⏸")
        else:
            meta = playlist_queue.play_index(0)
            if meta:
                self.update_track_ui(meta)
                self.btn_play.configure(text="⏸")

    def play_track(self, filepath):
        meta = playlist_queue.play_track(filepath)
        if meta:
            self.update_track_ui(meta)
            self.btn_play.configure(text="⏸")
            if self.on_track_change_callback:
                self.on_track_change_callback(meta)

    def play_next(self):
        meta = playlist_queue.next_track()
        if meta:
            self.update_track_ui(meta)
            self.btn_play.configure(text="⏸")
            if self.on_track_change_callback:
                self.on_track_change_callback(meta)

    def play_prev(self):
        meta = playlist_queue.prev_track()
        if meta:
            self.update_track_ui(meta)
            self.btn_play.configure(text="⏸")
            if self.on_track_change_callback:
                self.on_track_change_callback(meta)

    def toggle_shuffle(self):
        playlist_queue.shuffle = not playlist_queue.shuffle
        self.btn_shuffle.configure(fg_color="#27272a" if playlist_queue.shuffle else "transparent", text_color="#10b981" if playlist_queue.shuffle else "#f4f4f5")

    def toggle_loop(self):
        playlist_queue.repeat = not playlist_queue.repeat
        self.btn_loop.configure(fg_color="#27272a" if playlist_queue.repeat else "transparent", text_color="#10b981" if playlist_queue.repeat else "#f4f4f5")

    def update_track_ui(self, meta):
        self.current_meta = meta
        self.lbl_title.configure(text=meta.get("title", "Desconocido")[:30])
        self.lbl_artist.configure(text=meta.get("artist", "Desconocido")[:30])
        self.total_duration = meta.get("duration", 0)
        self.lbl_time_tot.configure(text=meta.get("duration_str", "0:00"))
        self.slider_time.configure(to=max(1, self.total_duration))
        self.slider_time.set(0)

        # Actualizar carátula
        cover = meta.get("cover_image")
        if cover:
            img = ctk.CTkImage(light_image=cover, dark_image=cover, size=(56, 56))
            self.lbl_cover.configure(image=img)
        else:
            img = ctk.CTkImage(light_image=self.default_cover, dark_image=self.default_cover, size=(56, 56))
            self.lbl_cover.configure(image=img)

    def on_seek(self, val):
        audio_player.seek(float(val))

    def start_progress_loop(self):
        if audio_player.is_playing():
            pos = audio_player.get_current_position()
            if not self.is_seeking:
                self.slider_time.set(pos)
                mins = int(pos) // 60
                secs = int(pos) % 60
                self.lbl_time_cur.configure(text=f"{mins}:{secs:02d}")

            # Detección de fin de pista
            if self.total_duration > 0 and pos >= (self.total_duration - 1):
                if playlist_queue.repeat and self.current_meta:
                    self.play_track(self.current_meta["path"])
                else:
                    self.play_next()

        self.after(500, self.start_progress_loop)
