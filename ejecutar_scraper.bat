@echo off
chcp 65001 >nul
echo ============================================================
echo   LANZADOR DEL SCRAPER DE BOLIVIA (INCREMENTAL)
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

%PYTHON_EXE% run_bolivia_scraper.py %*

if "%~1"=="" (
    echo.
    echo Presiona cualquier tecla para cerrar...
    pause >nul
)
