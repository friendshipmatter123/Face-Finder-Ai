@echo off
echo ========================================
echo   Starting FaceFind Backend Server
echo ========================================
echo.
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
