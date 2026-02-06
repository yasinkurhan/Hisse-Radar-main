@echo off
title HisseRadar Backend
cd /d %~dp0backend
echo ========================================
echo    HisseRadar Backend Baslatiliyor
echo ========================================
echo.
if exist venv\Scripts\activate (
    call venv\Scripts\activate
) else (
    echo Virtual environment bulunamadi (venv).
    pause
    exit
)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
