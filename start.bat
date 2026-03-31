@echo off
echo ============================================
echo  Clinic OCR - Setup and Start
echo ============================================

set PROJECT=%~dp0
set PYTHON=C:\Users\RWongmalasit\AppData\Local\Programs\Python\Python313\python.exe
set VENV=%PROJECT%venv
set VENV_PYTHON=%VENV%\Scripts\python.exe
set VENV_PIP=%VENV%\Scripts\pip.exe

:: Create venv if it doesn't exist
if not exist "%VENV%\Scripts\activate.bat" (
    echo.
    echo [1/3] Creating virtual environment...
    "%PYTHON%" -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: Failed to create venv.
        pause & exit /b 1
    )
    echo     Done.
) else (
    echo [1/3] Virtual environment already exists, skipping.
)

:: Install / update dependencies
echo.
echo [2/3] Installing dependencies...
"%VENV_PIP%" install fastapi "uvicorn[standard]" google-genai openpyxl Pillow python-multipart --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection.
    pause & exit /b 1
)
echo     Done.

:: Start server
echo.
echo [3/3] Starting server at http://localhost:8000
echo     Press Ctrl+C to stop.
echo.
cd /d "%PROJECT%"
"%VENV_PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
