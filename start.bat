@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"

echo [finanzuebersicht] Starte Root-Orchestrator...

if not exist "%VENV_PYTHON%" (
  echo [finanzuebersicht] FEHLER: .venv fehlt. Bitte einmalig ausfuehren: uv venv .venv
  exit /b 2
)

"%VENV_PYTHON%" -m orchestrator
endlocal
