# ========================================
#   FaceFind Backend Server Startup
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🚀 Starting FaceFind Backend Server" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Server: http://localhost:8001" -ForegroundColor Yellow
Write-Host "📚 API Docs: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host ""

& ".\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
