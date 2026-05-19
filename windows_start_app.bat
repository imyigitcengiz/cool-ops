@echo off
REM Windows: Cift tik — yalnizca baslatir; kurulum yapmaz.
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "LOG_DIR=%ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%i"
set "LOG_FILE=%LOG_DIR%\startup-%STAMP%.log"
set "LATEST_LOG=%LOG_DIR%\latest-windows.log"

call :log "=== GY Dashboard (Windows) ==="
call :log "Proje: %ROOT%"

if not exist "venv\Scripts\activate.bat" goto :missing_venv
if not exist "venv\Scripts\python.exe" goto :broken_venv

call "venv\Scripts\activate.bat"
if errorlevel 1 goto :missing_venv

python -c "import django" >nul 2>&1
if errorlevel 1 goto :missing_deps

for /f "delims=" %%v in ('python --version 2^>^&1') do call :log "Python: %%v"

set "LAN_IP="
for /f "delims=" %%i in ('python -c "import socket\ns=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)\ntry:\n s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()\nexcept OSError: pass" 2^>nul') do set "LAN_IP=%%i"

call :log "Bu bilgisayar:     http://127.0.0.1:8000"
if defined LAN_IP (
  call :log "Ayni WiFi agi:     http://!LAN_IP!:8000"
  echo.
  echo   Diger cihazlarda tarayiciya yazin:
  echo   http://!LAN_IP!:8000
  echo.
) else (
  call :log "WiFi IP bulunamadi; ipconfig ile kontrol edin."
)
call :log "Durdurmak: Ctrl+C  ^|  Log: %LOG_FILE%"

python manage.py runserver 0.0.0.0:8000
goto :eof

:missing_venv
call :log "Sanal ortam bulunamadi (venv\Scripts\activate.bat)."
call :show_setup_guide
goto :pause_exit

:broken_venv
call :log "Sanal ortam bozuk veya macOS'tan kopyalanmis olabilir."
echo.
echo   venv klasorunu silip kurulum adimlarini bastan uygulayin:
echo     rmdir /s /q venv
call :show_setup_guide
goto :pause_exit

:missing_deps
call :log "Django yuklu degil; bagimliliklar kurulmamis."
call :show_setup_guide
goto :pause_exit

:show_setup_guide
echo.
echo ================================================================
echo   Kurulum gerekli — asagidaki adimlari CMD veya PowerShell'de
echo   proje klasorunde uygulayin:
echo ================================================================
echo.
echo   1^) Python 3.10+ kurun:
echo        https://www.python.org/downloads/
echo      veya: winget install Python.Python.3.12
echo.
echo   2^) Proje klasorune gidin:
echo        cd /d "%ROOT%"
echo.
echo   3^) Sanal ortam olusturun:
echo        py -3 -m venv venv
echo.
echo   4^) Sanal ortami etkinlestirin:
echo        venv\Scripts\activate.bat
echo.
echo   5^) Bagimliliklari kurun:
echo        pip install -r requirements.txt
echo.
echo   6^) Veritabanini hazirlayin:
echo        python manage.py migrate
echo.
echo   7^) windows_start_app.bat dosyasini tekrar calistirin.
echo.
exit /b 0

:pause_exit
call :log "Log: %LOG_FILE%"
echo.
pause
exit /b 1

:log
echo [%date% %time%] %~1
echo [%date% %time%] %~1>> "%LOG_FILE%"
copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul 2>&1
exit /b 0
