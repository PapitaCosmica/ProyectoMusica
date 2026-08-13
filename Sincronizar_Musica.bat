@echo off
setlocal
cd /d "%~dp0"
title MusicSync Studio Pro

:: 1. Si existe el ejecutable independiente compilado, abrirlo directamente
if exist "dist\MusicSync_Studio\MusicSync_Studio.exe" (
    start "" "dist\MusicSync_Studio\MusicSync_Studio.exe"
    exit
)

:: 2. Buscar ruta directa de Python en AppData
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app_gui.py
    exit
)

:: 3. Intentar con python del sistema
start "" python app_gui.py
exit
