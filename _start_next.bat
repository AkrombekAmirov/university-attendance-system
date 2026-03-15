@echo off
cd /d "%~dp0frontend"

:: Server porti va hostini ko'rsatish
set PORT=3000
set HOSTNAME=0.0.0.0

:: Standalone'dan voz kechdik! 100% muammosiz ishlaydigan npm start'ni ishlatamiz
npm start >> ..\logs\frontend_prod.log 2>&1