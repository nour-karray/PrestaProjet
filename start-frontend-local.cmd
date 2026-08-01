@echo off
setlocal
cd /d "%~dp0frontend"

if not exist "node_modules" (
  echo [ERREUR] Executez d'abord setup-local.cmd depuis la racine.
  exit /b 1
)

call npm.cmd run dev

