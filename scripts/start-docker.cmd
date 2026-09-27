@echo off
setlocal
cd /d "%~dp0.."

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Docker est introuvable. Installez ou demarrez Docker Desktop.
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Docker Desktop n'est pas demarre.
  exit /b 1
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Fichier .env cree.
)

echo Construction et demarrage de l'application...
docker compose up --build -d
if errorlevel 1 (
  echo [ERREUR] Le demarrage a echoue. Consultez les messages ci-dessus.
  exit /b 1
)

echo.
echo Application demarree :
echo   Frontend : http://localhost:3000
echo   Backend Python : http://localhost:8000/health
echo   API Docs       : http://localhost:8000/docs
echo   Backend Spring : http://localhost:8080/health
echo.
start "" "http://localhost:3000"

