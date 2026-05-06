@echo off
REM ==========================================================
REM  Fallback: caso o antivirus bloqueie o .exe, este .bat
REM  faz exatamente a mesma coisa chamando o script PowerShell.
REM ==========================================================
setlocal
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%iniciar-aplicacao.ps1"
endlocal
