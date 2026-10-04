@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [ERREUR] Le fichier .env est absent. Executez setup-local.cmd.
  exit /b 1
)

start "TrainFlow AI Backend Spring" cmd /k call "%~dp0scripts\start-backend.cmd"
start "TrainFlow AI Frontend" cmd /k call "%~dp0scripts\start-frontend.cmd"

echo Backend  : http://localhost:8080
echo Frontend : http://localhost:5173
echo Sante    : http://localhost:8080/health

