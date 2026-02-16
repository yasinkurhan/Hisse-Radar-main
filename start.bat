@echo off
title HisseRadar Starter
echo ========================================
echo    HisseRadar Uygulamasi Baslatiliyor
echo ========================================
echo.

:: Backend'i baslat
echo [1/2] Backend baslatiliyor (Port 8000)...
start "HisseRadar Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 3 saniye bekle
timeout /t 3 /nobreak > nul

:: Frontend'i baslat
echo [2/2] Frontend baslatiliyor (Port 3000)...
start "HisseRadar Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: 5 saniye bekle ve tarayici ac
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo    Uygulama baslatildi!
echo ========================================
echo.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API Docs: http://localhost:8000/docs
echo.
echo    Tarayici aciliyor...
echo ========================================

:: Tarayiciyi ac
start http://localhost:3000

echo.
echo Bu pencereyi kapatabilirsiniz.
pause
