@echo off
echo Starting setup for Multi-User Facial Recognition Attendance System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8+ and try again.
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed or not in PATH. Please install Node.js 16+ and try again.
    exit /b 1
)

REM Ask user if they want to install backend dependencies
echo Do you want to install/update backend dependencies? (Y/N)
set /p install_backend=

if /i "%install_backend%"=="Y" (
    echo Installing backend dependencies...
    cd backend
    pip install -r requirements.txt
    cd ..
    echo Backend dependencies installed.
    echo.
)

REM Ask user if they want to install frontend dependencies
echo Do you want to install/update frontend dependencies? (Y/N)
set /p install_frontend=

if /i "%install_frontend%"=="Y" (
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
    echo Frontend dependencies installed.
    echo.
)

REM Ask user if they want to start the application
echo Do you want to start the application? (Y/N)
set /p start_app=

if /i "%start_app%"=="Y" (
    REM Start backend server
    echo Starting backend server...
    start cmd /k "cd backend && python main.py"
    
    REM Wait a moment for backend to initialize
    timeout /t 5 /nobreak
    
    REM Start frontend development server
    echo Starting frontend development server...
    start cmd /k "cd frontend && npm run dev"
    
    echo Application started.
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:5173
)

echo Setup completed.
echo.
