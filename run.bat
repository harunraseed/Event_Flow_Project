@echo off
echo 🎫 Event Ticketing System
echo ========================

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created!
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Run setup if needed
if not exist ".env" (
    echo 🛠️ Running first-time setup...
    python setup.py
) else (
    echo 🚀 Starting application...
    python app.py
)

pause