@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

:: Virtual muhitni faollashtirish
call .\venv\Scripts\activate.bat

:: Turniket eventlarini qabul qiluvchi xizmatni ishga tushirish
:: Loglar alohida faylga yoziladi, shunda xatolarni kuzatish oson bo'ladi
python backend\turniked.py > logs\turniked_prod.log 2>&1