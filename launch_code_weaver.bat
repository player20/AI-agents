@echo off
echo ========================================
echo   Code Weaver Pro - Launching...
echo ========================================
echo.
echo Starting Streamlit server...
echo Open your browser to: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
python -m streamlit run app.py --server.headless false --server.port 8501

pause
