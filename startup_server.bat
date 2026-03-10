@echo off
setlocal EnableDelayedExpansion
title University Attendance System - Secure Server Manager
color 0B

echo ===================================================================
echo   [UAS] SECURE SERVER BOOTSTRAPPER (PRODUCTION MODE)
echo   OS: Windows 11 Pro / Environment: Production
echo ===================================================================
echo.

:: 1. Loyiha papkasini to'g'irlash
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: 2. Loglar uchun papka yaratish
if not exist "logs" mkdir logs

echo [*] Muhit sozlanmoqda...
echo     Loyiha: %PROJECT_ROOT%
echo     Sana  : %date% %time%
echo.

:: =====================================================================================
:: 3. Backend (Uvicorn 4x Workers) ishga tushirish
:: =====================================================================================
echo [*] Backend Service (Uvicorn 4x Workers) ishga tushirilmoqda...
start "UAS Backend [Uvicorn]" /MIN cmd /c "_start_uvicorn.bat"

:: Bazaga ulanishi uchun 5 soniya taymer
timeout /t 5 >nul

:: =====================================================================================
:: 4. Frontend (Next.js Production) ishga tushirish
:: =====================================================================================
echo [*] Frontend Service (Next.js) ishga tushirilmoqda...

:: Frontend tekshiruvi: Agar Next.js build qilinmagan bo'lsa, uni build qilamiz
if not exist "frontend\.next\BUILD_ID" (
    echo [*] Build topilmadi. Frontend toza holatda o'rnatilmoqda va build qilinmoqda...
    cd frontend
    call npm install

    echo [*] React2Shell RCE xavfsizlik patchi o'rnatilmoqda...
    call npx fix-react2shell-next

    echo [*] RCE dan himoyalangan xavfsiz build boshlanmoqda...
    set NEXT_PUBLIC_API_URL=https://api.davomat.uznpu.uz
    call npm run build
    cd ..
)

start "UAS Frontend [Next.js]" /MIN cmd /c "_start_next.bat"

echo.
echo ===================================================================
echo [SUCCESS] TIZIM XAVFSIZ VA BARQAROR (PRODUCTION) REJIMDA ISHGA TUSHTI!
echo ===================================================================
echo [I] Backend  : 0.0.0.0:8000 (4 ta Worker)
echo [I] Frontend : 0.0.0.0:3000 (NPM START REJIMI)
echo [I] Loglar   : "logs\backend_prod.log" va "logs\frontend_prod.log" fayllariga yozilmoqda.
echo.
echo Tizim orqa fonda xavfsiz holda ishlashni davom ettiradi. Oynani yopsangiz ham bo'ladi.
timeout /t 10 >nul
exit