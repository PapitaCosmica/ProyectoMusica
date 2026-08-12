# 🎵 MusicSync Studio Pro

**Gestor integral de música con descarga automática de YouTube, sincronización a memorias USB, reproductor integrado estilo Spotify y empaquetado portable.**

> Hecho con ❤️ por [@PapitaCosmica](https://github.com/PapitaCosmica)

---

## ✨ Características

- **⬇️ Descarga automática** de playlists de YouTube con yt-dlp
- **🔄 Sincronización incremental** a memorias USB con barra de progreso en vivo
- **🎵 Reproductor integrado** estilo Spotify con selector de salidas de audio (Voicemeeter, Bluetooth, HDMI, Realtek)
- **📊 Diagnóstico del sistema** con monitoreo de almacenamiento y estado de sincronización
- **🛠️ Formateo universal** de memorias USB a FAT32 MBR (compatible con estéreos de auto)
- **🏷️ Metadatos automáticos** ID3v2.3 UTF-16 para compatibilidad con reproductores de música
- **📋 Gestor de playlists** multi-enlace con activación/desactivación individual
- **⚡ Modo rápido y modo completo** con selector al inicio (Launcher Hub)
- **📦 Empaquetado portable** en `.exe` y `.zip` para llevar a cualquier PC

---

## 📁 Estructura del Proyecto

```
ProyectoMusica/
│
├── app_gui.py                  # 🚀 Punto de entrada principal
├── sync_engine.py              # Puente CLI hacia core/
│
├── core/                       # Capa de Lógica y Datos
│   ├── config.py               # Configuración y persistencia JSON
│   ├── downloader.py           # Descargas con yt-dlp + auto-cookies
│   ├── sync_engine.py          # Desduplicación y metadatos ID3
│   ├── usb_manager.py          # Detección USB, formateo y sync incremental
│   └── task_manager.py         # Concurrencia y guardrails de seguridad
│
├── player/                     # Capa de Audio
│   ├── audio_engine.py         # Motor Pygame + SDL2 con selector de dispositivos
│   └── playlist_queue.py       # Cola de reproducción y metadatos/carátulas
│
├── gui/                        # Interfaz Gráfica (CustomTkinter)
│   ├── launcher_hub.py         # Menú selector de herramientas al iniciar
│   ├── main_window.py          # Ventana principal con pestañas
│   └── components/             # Componentes modulares por pestaña
│       ├── player_bar.py       # Barra inferior estilo Spotify
│       ├── tab_library.py      # Explorador de biblioteca local
│       ├── tab_sync.py         # Centro de control de descargas
│       ├── tab_usb.py          # Gestor de memoria USB
│       ├── tab_diagnostics.py  # Diagnóstico y almacenamiento
│       ├── tab_playlists.py    # Gestor de playlists de YouTube
│       └── tab_settings.py     # Ajustes de estructura y automatización
│
├── formatear_usb.cmd           # Script de formateo FAT32 con permisos elevados
├── Sincronizar_Musica.bat      # Lanzador rápido desde escritorio
├── build_portable.py           # Empaquetador PyInstaller + ZIP
├── empaquetar_portable.bat     # Lanzador del empaquetado en 1 clic
├── requirements.txt            # Dependencias del proyecto
└── config.json                 # Configuración persistente (ejemplo)
```

---

## 🚀 Instalación

### Requisitos
- **Python 3.11+**
- **Node.js** (requerido por yt-dlp para extraer contenido de YouTube)
- **Windows 10/11**

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/PapitaCosmica/ProyectoMusica.git
cd ProyectoMusica

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app_gui.py
```

### Cookies de YouTube (obligatorio para descargas)
Para evitar el bloqueo "Sign in to confirm you're not a bot":

1. Instala la extensión **[Cookie Editor](https://cookie-editor.com/)** en tu navegador
2. Ve a [youtube.com](https://youtube.com) e inicia sesión
3. Abre Cookie Editor → **Exportar como JSON**
4. Guarda el archivo `.json` en la carpeta del proyecto
5. MusicSync lo detectará y convertirá automáticamente al formato Netscape

---

## 📦 Generar Versión Portable (.exe)

```bash
python build_portable.py
```

Esto genera:
- `dist/MusicSync_Studio/MusicSync_Studio.exe` — Ejecutable directo
- `dist/MusicSync_Studio_Portable.zip` — ZIP listo para llevar a otra PC

---

## 🛠️ Tecnologías

| Tecnología | Uso |
|---|---|
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interfaz gráfica moderna dark-mode |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Descarga de audio de YouTube |
| [Pygame](https://www.pygame.org/) + SDL2 | Motor de audio y selector de dispositivos |
| [Mutagen](https://mutagen.readthedocs.io/) | Lectura/escritura de metadatos ID3 |
| [Pillow](https://python-pillow.org/) | Procesamiento de carátulas embebidas |
| [psutil](https://github.com/giampaolo/psutil) | Diagnóstico de almacenamiento |
| [PyInstaller](https://pyinstaller.org/) | Empaquetado portable .exe |

---

## 📄 Licencia

Este proyecto es de uso personal. Siéntete libre de adaptarlo a tus necesidades.

---

## 🎧 Versión Actual: `v1.0.0`
