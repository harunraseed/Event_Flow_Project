@echo off
REM Event Dashboard Backup and Restore Script
REM ==========================================

echo 🔄 Event Dashboard Backup System
echo ==================================

if "%1"=="backup" (
    echo 📦 Creating backup...
    copy "templates\event_dashboard.html" "backup\event_dashboard_manual_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.html"
    echo ✅ Backup created successfully!
    goto end
)

if "%1"=="restore" (
    echo 🔄 Available backups:
    dir /b backup\event_dashboard_*.html
    echo.
    set /p filename="Enter backup filename to restore: "
    copy "backup\%filename%" "templates\event_dashboard.html"
    echo ✅ Dashboard restored from backup!
    goto end
)

if "%1"=="list" (
    echo 📋 Available backups:
    dir /b backup\event_dashboard_*.html
    goto end
)

echo Usage:
echo   backup_dashboard.bat backup   - Create a backup
echo   backup_dashboard.bat restore  - Restore from backup
echo   backup_dashboard.bat list     - List available backups

:end
pause