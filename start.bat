@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting Enhanced Autonomous BOM Platform with QA Classification...
echo ============================================================

REM Check if we're in the right directory
if not exist "start.bat" (
    echo ❌ Please run this script from the autonomous_bom_platform_qa_enhanced directory
    pause
    exit /b 1
)

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)

echo ℹ️  Starting backend and frontend services...

REM Configure environment
if not exist "backend\.env" (
    echo ℹ️  Setting up backend environment...
    copy "backend\.env.example" "backend\.env"
    echo ⚠️  Please configure your GEMINI_API_KEY in backend\.env for full AI functionality
)

if not exist "frontend\.env.local" (
    echo ℹ️  Setting up frontend environment...
    echo VITE_API_BASE_URL=http://localhost:8000 > frontend\.env.local
)

REM Start backend
echo ℹ️  Setting up Python virtual environment...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install Python dependencies
echo ℹ️  Installing Python dependencies...
pip install -r requirements.txt

REM Start backend server
echo ✅ Starting backend server on http://localhost:8000
start "Backend Server" cmd /k "python main.py"

REM Give backend time to start
timeout /t 3 /nobreak >nul

REM Start frontend
cd ..\frontend
echo ℹ️  Installing Node.js dependencies...
call npm install

echo ✅ Starting frontend development server on http://localhost:3000
start "Frontend Server" cmd /k "npm run dev"

echo.
echo ✅ Enhanced Autonomous BOM Platform is starting up!
echo ==================================
echo ℹ️  Backend: http://localhost:8000
echo ℹ️  Frontend: http://localhost:3000
echo ℹ️  API Docs: http://localhost:8000/docs
echo ℹ️  Health Check: http://localhost:8000/health
echo.
echo ✅ 🤖 Autonomous Agents with QA Classification Enabled!
echo ℹ️     - Translation Agent: Document processing
echo ℹ️     - Extraction Agent: QA classification (13 categories)
echo ℹ️     - Supplier BOM Agent: Excel/CSV processing
echo ℹ️     - Comparison Agent: Intelligent matching
echo.
echo ✅ 📋 Test Documents Available:
echo ℹ️     - frontend/test-documents/japanese-qa-document.txt
echo ℹ️     - frontend/test-documents/supplier-bom.csv
echo.
echo ⚠️  Configure GEMINI_API_KEY in backend\.env for full AI functionality
echo ℹ️  Close the backend and frontend windows to stop all services
echo.
pause
