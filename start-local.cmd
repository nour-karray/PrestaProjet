@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [ERREUR] Le fichier .env est absent. Executez setup-local.cmd.
  exit /b 1
)

start "PrestaCode Backend" cmd /k call "%~dp0start-backend-local.cmd"
start "PrestaCode Frontend" cmd /k call "%~dp0start-frontend-local.cmd"

echo Backend  : http://localhost:8000
echo Frontend : http://localhost:3000
echo API Docs : http://localhost:8000/docs

