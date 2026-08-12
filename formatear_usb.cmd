@echo off
cd /d "%~dp0"

set DISK_NUM=%1
if "%DISK_NUM%"=="" set DISK_NUM=2

set SCRIPT_FILE=%~dp0.diskpart_script.txt
set DONE_FILE=%~dp0.usb_format_done.txt

if exist "%DONE_FILE%" del /f /q "%DONE_FILE%"
if exist "%SCRIPT_FILE%" del /f /q "%SCRIPT_FILE%"

echo select disk %DISK_NUM% > "%SCRIPT_FILE%"
echo clean >> "%SCRIPT_FILE%"
echo create partition primary >> "%SCRIPT_FILE%"
echo active >> "%SCRIPT_FILE%"
echo format fs=fat32 quick label="MUSICA" >> "%SCRIPT_FILE%"
echo assign >> "%SCRIPT_FILE%"

diskpart /s "%SCRIPT_FILE%"
if exist "%SCRIPT_FILE%" del /f /q "%SCRIPT_FILE%"

echo OK > "%DONE_FILE%"
exit /b 0
