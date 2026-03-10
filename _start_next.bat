@echo off
cd /d "%~dp0frontend"

:: Standalone server porti va hostini ko'rsatish
set PORT=3000
set HOSTNAME=0.0.0.0

:: Next.js ni to'g'ridan to'g'ri standalone js faylidan ishga tushirish
:: Bu "npm start" ga nisbatan ancha barqaror va loglarni aniq ushlab qoladi.
node .next/standalone/server.js > ..\logs\frontend_prod.log 2>&1
