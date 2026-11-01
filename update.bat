@echo off
rem 每日情報站 —— 更新一次資料（可以放去 Windows 工作排程器每日執行）
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
for /d %%d in ("%LOCALAPPDATA%\hermes\tools\python-3.14*") do set "PY=%%~fd\python.exe"
if defined PY if exist "%PY%" goto run
set "PY=python"
:run
"%PY%" refresh.py
