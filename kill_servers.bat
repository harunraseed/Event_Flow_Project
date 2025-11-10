@echo off
echo ========================================
echo Stopping All MCP Servers and Ports
echo ========================================

echo Checking for processes on MCP ports...

echo.
echo Checking Port 5000 (Web App)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    echo Killing process %%a on port 5000
    taskkill /PID %%a /F 2>nul
)

echo.
echo Checking Port 8001 (Movie Server)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    echo Killing process %%a on port 8001
    taskkill /PID %%a /F 2>nul
)

echo.
echo Checking Port 8002 (Ticket Server)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8002') do (
    echo Killing process %%a on port 8002
    taskkill /PID %%a /F 2>nul
)

echo.
echo Checking Port 8003 (Banking Server)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8003') do (
    echo Killing process %%a on port 8003
    taskkill /PID %%a /F 2>nul
)

echo.
echo Killing any remaining Python processes...
tasklist /fi "imagename eq python.exe" | findstr python.exe
if %errorlevel%==0 (
    echo Found Python processes, killing them...
    taskkill /im python.exe /F 2>nul
) else (
    echo No Python processes found.
)

echo.
echo ========================================
echo All MCP servers and processes stopped!
echo ========================================
echo You can now restart servers individually.
pause