# Code Weaver Pro - PowerShell Launcher
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Code Weaver Pro - Launching..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting Streamlit server..." -ForegroundColor Yellow
Write-Host "Open your browser to: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot
python -m streamlit run app.py --server.port 8501

Read-Host -Prompt "Press Enter to exit"
