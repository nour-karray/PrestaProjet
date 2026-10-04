@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Fichier .env cree. Configurez DATABASE_URL et JWT_SECRET avant de continuer.
  exit /b 1
)

echo Installation du backend...
call mvn.cmd -f backend\pom.xml package -DskipTests
if errorlevel 1 exit /b 1

echo Installation du frontend...
call npm.cmd --prefix frontend install
if errorlevel 1 exit /b 1

echo.
echo Installation locale terminee. Lancez ensuite : start-local.cmd
echo Spring Boot appliquera les migrations Flyway sur la base MySQL configuree.

