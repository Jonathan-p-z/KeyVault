@echo off
setlocal EnableExtensions

cd /d "%~dp0"

REM --- Pick a Python launcher (prefer py, fallback to python)
set "PYLAUNCHER="
where py >nul 2>nul && set "PYLAUNCHER=py -3"
if not defined PYLAUNCHER (
  where python >nul 2>nul && set "PYLAUNCHER=python"
)

if not defined PYLAUNCHER (
  echo.
  echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH.
  echo Installe Python 3.10+ puis relance ce fichier.
  echo https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

REM --- Create venv if missing
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creation de l'environnement virtuel .venv...
  %PYLAUNCHER% -m venv .venv
  if errorlevel 1 (
    echo.
    echo ERREUR: impossible de creer le venv.
    pause
    exit /b 1
  )
)

set "PY=%CD%\.venv\Scripts\python.exe"

echo [2/3] Installation / mise a jour des dependances...
"%PY%" -m pip install -U pip >nul
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERREUR: installation des dependances echouee.
  pause
  exit /b 1
)

echo [3/3] Lancement...
"%PY%" -m mdp_app

endlocal
