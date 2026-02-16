@echo off
title HisseRadar Frontend
cd /d %~dp0frontend
echo ========================================
echo    HisseRadar Frontend Baslatiliyor
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo.
npm run dev
pause
