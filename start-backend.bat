@echo off
title HisseRadar Backend
cd /d C:\Users\kurha\Desktop\HisseRadar\backend
echo ========================================
echo    HisseRadar Backend Baslatiliyor
echo ========================================
echo.
call .venv\Scripts\activate
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
