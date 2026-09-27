@echo off
setlocal
cd /d "%~dp0..\backend-python"

if not exist ".venv\Scripts\python.exe" (
  echo [ERREUR] Executez d'abord ..\setup-local.cmd depuis la racine.
  exit /b 1
)

".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m app.db.seed
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

