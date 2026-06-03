@echo off
title Asistente SmartHome
cd /d "%~dp0"

:: Esperar conexion de red (cambiar IP por la de tu SpaceLynk)
:wait_network
ping -n 1 192.168.X.X >nul 2>&1
if errorlevel 1 (
    timeout /t 3 >nul
    goto wait_network
)

:: Arrancar Ollama si no esta corriendo
tasklist | find "ollama.exe" >nul 2>&1
if errorlevel 1 start /b "" ollama.exe

:: Iniciar el asistente en modo voz (con API en segundo plano)
python asistente.py
