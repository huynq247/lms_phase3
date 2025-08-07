@echo off
REM Flashcard LMS Backend Setup Script for Windows

echo 🚀 Setting up Flashcard LMS Backend...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    exit /b 1
)

echo ✅ Python detected

REM Create virtual environment
echo 📦 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Dependencies installed successfully

REM Create upload directories
echo 📁 Creating upload directories...
if not exist "uploads\images" mkdir uploads\images
if not exist "uploads\audio" mkdir uploads\audio
echo ✅ Upload directories created

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Please create one based on the template in README.md
) else (
    echo ✅ .env file found
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Configure your .env file with proper database settings
echo 2. Start MongoDB (locally or use MongoDB Atlas)
echo 3. Run the application: uvicorn app.main:app --reload
echo.
echo 📚 Useful commands:
echo   • Start development server: uvicorn app.main:app --reload
echo   • Run tests: pytest
echo   • View API docs: http://localhost:8000/docs
echo.
