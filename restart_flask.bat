@echo off
echo Stopping Flask processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM py.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting Flask app with Supabase configuration...
cd /d "D:\Harun\Azure_Developer_Community\event-ticketing-app"
call venv\scripts\activate
echo.
echo DATABASE_URL configuration check:
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DB:', os.getenv('DATABASE_URL', 'NOT SET')[:50] + '...')"
echo.
echo Starting Flask app...
py app.py