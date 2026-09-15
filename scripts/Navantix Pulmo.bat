@echo off
title Navantix Pulmo - Clinical Decision Support
color 0B

echo.
echo  ================================================================
echo.
echo    NAVANTIX PULMO
echo    Clinical AI for Chest Radiograph Triage
echo.
echo  ================================================================
echo.
echo    Starting services...
echo.

echo  [1/4] Clearing previous sessions...
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo  [2/4] Launching backend service...
start "Navantix Pulmo - Backend" /min cmd /c "C:\Users\brahn\cxr-ai-assist\scripts\start-backend.bat"

echo  [3/4] Waiting for inference engine...
timeout /t 12 /nobreak >nul

echo  [4/4] Launching clinical dashboard...
start "Navantix Pulmo - Frontend" /min cmd /c "C:\Users\brahn\cxr-ai-assist\scripts\start-frontend.bat"

echo.
echo  ================================================================
echo    Services are running.
echo    Opening clinical dashboard in your browser...
echo  ================================================================
echo.

timeout /t 10 /nobreak >nul
start http://localhost:3000

echo.
echo    Navantix Pulmo is now running.
echo.
echo    Press any key to close this launcher.
echo.
pause >nul