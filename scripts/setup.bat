@echo off
setlocal enabledelayedexpansion

echo Setting up MoneyOS development environment...

REM Copy .env.example to .env if .env doesn't exist
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
) else (
    echo .env already exists, skipping...
)

REM Setup frontend dependencies
echo Installing frontend dependencies...
cd apps\frontend

REM Check if node_modules exists to skip if already setup
if exist "node_modules" (
    echo Frontend already setup, skipping...
) else (
    npm install
)
cd ..\..

REM Setup backend
echo Setting up Python virtual environment...
if exist "apps\backend\venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv apps\backend\venv
)

echo Activating virtual environment...
cd apps\backend
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ❌ Virtual environment activation script not found
    exit /b 1
)

pip install --upgrade pip
pip install -r requirements.txt

cd ..\..

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Install Docker Desktop if not already installed
echo 2. Start services with: docker-compose up
echo 3. Frontend will be available at http://localhost:3000
echo 4. Backend API will be available at http://localhost:8000