@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  啟動每日情報站...
echo.
python serve.py
if errorlevel 1 (
  echo.
  echo  找不到 python，試下用 py 啟動：
  py serve.py
)
pause
