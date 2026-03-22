@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

cd /d "%SCRIPT_DIR%"
echo [finanzuebersicht] Starte Root-Orchestrator...
uv run finanzuebersicht
endlocal
