@echo off
rem 每日情報站 —— 一鍵開放 Windows 防火牆 port 8090（手機會要用）
rem 會彈出 UAC 確認視窗，按「是」即可。
chcp 65001 >nul
powershell -NoProfile -Command "Start-Process netsh -ArgumentList 'advfirewall firewall add rule name=\"DailyBrief 8090\" dir=in action=allow protocol=TCP localport=8090' -Verb RunAs"
echo.
echo 已請求開放 port 8090。如果手機仍然連唔到：
echo   1. 確認手機同電腦連同一個 Wi-Fi
echo   2. 確認 start.bat 個黑色視窗仍然開住
echo   3. 用 start.bat 顯示嘅網址（ipconfig 可能已轉 IP）
pause
