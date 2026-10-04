@echo off
setlocal
cd /d "%~dp0..\backend"

where mvn.cmd >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Maven est introuvable. Installez Maven 3.9 ou superieur.
  exit /b 1
)

call mvn.cmd spring-boot:run

