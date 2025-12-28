@echo off
set "scriptPath=%~dp0fix_vpn.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%scriptPath%\"' -Verb RunAs"
echo Proceso lanzado. Revisa la nueva ventana de PowerShell.
pause