@echo off
cd /d "%~dp0"
title MusicSync Studio Pro

if exist "dist\MusicSync_Studio\MusicSync_Studio.exe" (
    start "" "dist\MusicSync_Studio\MusicSync_Studio.exe"
    exit
)

start "" python app_gui.py
exit
