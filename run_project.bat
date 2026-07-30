@echo off
TITLE Teachable Machine Edge AI Smart Classroom Telemetry System
COLOR 0A
cls
echo ========================================================================
echo       TEACHABLE MACHINE EDGE AI SMART CLASSROOM TELEMETRY SYSTEM        
echo ========================================================================
echo.
echo [1/2] Starting FastAPI Edge Backend (Keras Engine)...
start "Smart Classroom Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 >nul

echo [2/2] Starting Next.js Glassmorphism Telemetry Dashboard...
start "Smart Classroom Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================================
echo SYSTEM READY!
echo.
echo - Backend API:  http://localhost:8000
echo - Swagger Docs: http://localhost:8000/docs
echo - UI Dashboard: http://localhost:3000
echo ========================================================================
echo.
pause
