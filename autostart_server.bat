@echo off
rem 每日情報站 —— 背景開伺服器（開機自動用，唔會擋住螢幕）
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
for /d %%d in ("%LOCALAPPDATA%\hermes\tools\python-3.14*") do set "PY=%%~fd\python.exe"
if defined PY if exist "%PY%" goto run
set "PY=python"
:run
"%PY%" serve.py
