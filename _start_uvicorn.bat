@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

:: Virtual muhitni faollashtirish
call .\venv\Scripts\activate.bat

:: Uvicorn ishga tushirish (xavfsiz loglash va yashirin headerlar bilan)
:: 4 ta worker xavfsizlik va tezlik uchun
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips="*" --timeout-keep-alive 65 --log-level info --header server:None > logs\backend_prod.log 2>&1
