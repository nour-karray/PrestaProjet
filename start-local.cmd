@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [ERREUR] Le fichier .env est absent. Executez setup-local.cmd.
  exit /b 1
)

start "TrainFlow AI Backend Python" cmd /k call "%~dp0scripts\start-backend.cmd"
start "TrainFlow AI Frontend" cmd /k call "%~dp0scripts\start-frontend.cmd"

echo Backend  : http://localhost:8000
echo Frontend : http://localhost:3000
echo API Docs : http://localhost:8000/docs
echo Spring Phase 1 : lancez manuellement backend\target\trainflow-backend-*.jar sur le port 8080

