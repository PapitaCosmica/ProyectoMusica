@echo off
setlocal
cd /d "%~dp0"
title MusicSync Studio

python app_gui.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Hubo un detalle al iniciar la aplicacion con Python.
    echo Asegurate de tener Python instalado y accesible.
    pause
)
exit
