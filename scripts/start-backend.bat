@echo off
title Navantix Pulmo - Backend Service
cd /d "C:\Users\brahn\cxr-ai-assist\backend"
echo.
echo  ============================================================
echo   NAVANTIX PULMO - BACKEND SERVICE
echo   Starting FastAPI + ONNX inference engine...
echo  ============================================================
echo.
poetry run uvicorn app.main:app --reload --port 8000
pause