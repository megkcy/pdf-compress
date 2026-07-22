@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    set PY=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PY=py
    ) else (
        echo Python not found. Install it from https://python.org and try again.
        pause
        exit /b 1
    )
)

%PY% -c "import pypdf" >nul 2>nul
if not %errorlevel%==0 (
    echo Installing dependencies...
    %PY% -m pip install -r requirements.txt
)

%PY% compress_pdf.py

pause
