# -*- coding: utf-8 -*-
"""Motor de Audio con Pygame y Selector de Dispositivos de Salida (Bluetooth/HDMI/Voicemeeter)."""

import os
import time
import pygame
from pygame._sdl2 import audio as sdl2_audio

class AudioPlayer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioPlayer, cls).__new__(cls)
            cls._instance._init_player()
        return cls._instance

    def _init_player(self):
        self.is_initialized = False
        self.current_device = None
        self.volume = 0.8
        self.current_track = None
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0
        self.track_length = 0

    def init_audio_system(self, device_name=None):
        """Inicializa el motor de audio bajo demanda."""
        if not self.is_initialized:
            try:
                pygame.init()
                self._init_mixer(device_name=device_name)
                self.is_initialized = True
            except Exception as e:
                print(f"[!] Error inicializando audio: {e}")

    def unload_audio_system(self):
        """Apaga y libera el motor de audio por completo de la memoria."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            self.is_initialized = False
            self.current_track = None
            self.is_paused = False
            print("[*] Motor de audio apagado y memoria liberada.")
        except Exception as e:
            print(f"[!] Error liberando audio: {e}")

    def _init_mixer(self, device_name=None):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()

            if device_name and device_name != "Altavoces (Por Defecto)":
                pygame.mixer.init(devicename=device_name)
                self.current_device = device_name
            else:
                pygame.mixer.init()
                self.current_device = "Altavoces (Por Defecto)"
            pygame.mixer.music.set_volume(self.volume)
            self.is_initialized = True
        except Exception as e:
            print(f"[!] Error inicializando mixer de audio: {e}")

    def get_available_output_devices(self):
        """Devuelve la lista de nombres de salidas de audio disponibles en Windows."""
        try:
            if not pygame.get_init():
                pygame.init()
            devices = sdl2_audio.get_audio_device_names(False)
            return list(devices) if devices else ["Altavoces (Por Defecto)"]
        except Exception as e:
            return ["Altavoces (Por Defecto)"]

    def set_output_device(self, device_name):
        """Cambia dinámicamente la salida de audio (ej: Voicemeeter, Bluetooth, HDMI, Realtek)."""
        if device_name == self.current_device:
            return True

        current_file = self.current_track
        current_pos = self.get_current_position()
        was_playing = self.is_playing()

        self._init_mixer(device_name=device_name)

        if was_playing and current_file and os.path.exists(current_file):
            self.play(current_file, start_pos=current_pos)
        return True

    def play(self, filepath, start_pos=0.0):
        if not filepath or not os.path.exists(filepath):
            return False

        if not self.is_initialized:
            self.init_audio_system()

        try:
            self.current_track = filepath
            pygame.mixer.music.load(filepath)
            if start_pos > 0:
                pygame.mixer.music.play(start=start_pos)
                self.start_time = time.time() - start_pos
            else:
                pygame.mixer.music.play()
                self.start_time = time.time()

            self.is_paused = False
            pygame.mixer.music.set_volume(self.volume)
            return True
        except Exception as e:
            print(f"[!] Error reproduciendo pista: {e}")
            return False

    def pause(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy() and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self.pause_time = time.time()
        except Exception:
            pass

    def unpause(self):
        try:
            if pygame.mixer.get_init() and self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.start_time += (time.time() - self.pause_time)
        except Exception:
            pass

    def stop(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_paused = False
        self.current_track = None

    def is_playing(self):
        try:
            if pygame.mixer.get_init():
                return pygame.mixer.music.get_busy() and not self.is_paused
        except Exception:
            pass
        return False

    def set_volume(self, val):
        self.volume = max(0.0, min(1.0, float(val)))
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def seek(self, seconds):
        if self.current_track and os.path.exists(self.current_track):
            self.play(self.current_track, start_pos=seconds)

    def get_current_position(self):
        if self.is_paused:
            return max(0.0, self.pause_time - self.start_time)
        elif self.is_playing():
            return max(0.0, time.time() - self.start_time)
        return 0.0

audio_player = AudioPlayer()
