@echo off
setlocal enabledelayedexpansion
title Stop AI Resume Portfolio Generator
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"

exit /b %ERRORLEVEL%
