@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
for /d %%d in ("%LOCALAPPDATA%\hermes\tools\python-3.14*") do set "PY=%%~fd\python.exe"
if defined PY if exist "%PY%" goto run
set "PY=python"
:run
echo.
echo  1) 開本機伺服器 (8090)...
start "" /min "%PY%" serve.py
timeout /t 3 >nul
echo  2) 開 Cloudflare 臨時隧道（網上版，唔需要帳號）...
echo     隧道網址會印在下面，形式係 https://xxx-xxx.trycloudflare.com
echo     關掉這個視窗就會斷線；重開會有一個新網址。
echo.
if exist "%USERPROFILE%\tools\cloudflared\cloudflared.exe" (
  "%USERPROFILE%\tools\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:8090 --no-autoupdate
) else (
  echo 找不到 cloudflared.exe，只開本機版： http://localhost:8090/
  pause
)
