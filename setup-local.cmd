@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Fichier .env cree. Configurez DATABASE_URL et JWT_SECRET avant de continuer.
  exit /b 1
)

if not exist "backend-python\.venv\Scripts\python.exe" (
  python -m venv "backend-python\.venv"
  if errorlevel 1 exit /b 1
)

echo Installation du backend...
"backend-python\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"backend-python\.venv\Scripts\python.exe" -m pip install -e "backend-python[dev]"
if errorlevel 1 exit /b 1

echo Installation du frontend...
call npm.cmd --prefix frontend install
if errorlevel 1 exit /b 1

echo Migration de la base...
pushd backend-python
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
  popd
  exit /b 1
)
".venv\Scripts\python.exe" -m app.db.seed
if errorlevel 1 (
  popd
  exit /b 1
)
popd

echo.
echo Installation locale terminee. Lancez ensuite : start-local.cmd

