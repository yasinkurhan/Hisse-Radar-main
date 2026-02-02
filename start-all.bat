@echo off
title HisseRadar - Tum Sistemler
echo ========================================
echo    HisseRadar Baslatiliyor
echo ========================================
echo.

:: Node.js PATH'e ekle (yeni kurulumlar icin)
set PATH=C:\Program Files\nodejs;%PATH%

:: Backend'i yeni pencerede baslat
start "HisseRadar Backend" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 3 saniye bekle
timeout /t 3 /nobreak > nul

:: Frontend'i yeni pencerede baslat
start "HisseRadar Frontend" cmd /k "cd /d %~dp0frontend && set PATH=C:\Program Files\nodejs;%%PATH%% && npm run dev"

echo.
echo Backend ve Frontend baslatildi!
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Bu pencereyi kapatabilirsiniz.
timeout /t 5
