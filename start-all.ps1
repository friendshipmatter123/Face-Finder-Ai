# ========================================
#   FaceFind - Start Both Servers
# ========================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🚀 Starting FaceFind Application" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend in new window
Write-Host "🔧 Starting Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'd:\VS CODE\VS_COPILOT\Photo detector\backend'; .\start.ps1"

Start-Sleep -Seconds 3

# Start Frontend in new window
Write-Host "🎨 Starting Frontend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'd:\VS CODE\VS_COPILOT\Photo detector\frontend'; Write-Host ''; Write-Host '🎨 FaceFind Frontend' -ForegroundColor Cyan; Write-Host ''; npm run dev"

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ FaceFind is Starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "⚙️  Backend:  http://localhost:8001" -ForegroundColor Yellow
Write-Host "📚 API Docs: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔐 Admin Login:" -ForegroundColor Cyan
Write-Host "   Email:    admin"
Write-Host "   Password: (set in backend/.env)"
Write-Host ""
Write-Host "Press any key to exit this launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
