@echo off
setlocal
cd /d "%~dp0"
title MusicSync Studio - Empaquetador Portable
echo ========================================================
echo   Empaquetando MusicSync Studio en version Portable .EXE
echo ========================================================
echo.
python build_portable.py
echo.
pause
