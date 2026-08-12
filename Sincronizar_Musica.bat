@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title MusicSync Studio Pro

:: Intentar ejecutar con python
python app_gui.py %*
if %ERRORLEVEL% EQU 0 goto :fin

:: Si python falla, intentar con py
py -3 app_gui.py %*
if %ERRORLEVEL% EQU 0 goto :fin

echo.
echo [!] No se pudo iniciar MusicSync Studio Pro.
echo Asegurate de tener Python 3 instalado en tu computadora.
echo.
pause

:fin
exit /b 0
