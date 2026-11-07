@echo off
chcp 65001 >nul
echo ============================================================
echo   INICIANDO DASHBOARD DE SEGURIDAD CIUDADANA (BOLIVIA)
echo ============================================================
echo.

REM Buscar Python 3.12 donde estan todas las librerias instaladas
set PYTHON_EXE=""

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_EXE=py -3.12
    ) else (
        set PYTHON_EXE=python
    )
)

echo Usando interprete: %PYTHON_EXE%
echo.
echo Abriendo servidor web en: http://127.0.0.1:5000/?ctx=bolivia
echo.

%PYTHON_EXE% app.py
pause
