@echo off
setlocal enabledelayedexpansion

echo ----------------------------------------
powershell -NoProfile -Command "Write-Host ' Welcome To Make It Setup ' -ForegroundColor Blue"
powershell -NoProfile -Command "Write-Host ' Developer : Niranjan Kumar K ' -ForegroundColor Green"
powershell -NoProfile -Command "Write-Host ' Version   : 1.0 ' -ForegroundColor Red"
echo ----------------------------------------

set INSTALL=C:\makeit
set BIN=%INSTALL%\bin
set DATA=%INSTALL%\data

if not exist "%BIN%" mkdir "%BIN%"
if not exist "%DATA%" mkdir "%DATA%"

echo.
powershell -NoProfile -Command "Write-Host 'Downloading Make It...' -ForegroundColor Yellow"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"Invoke-WebRequest -Uri 'https://hacker1514.github.io/make/download/make_it_win.exe' -OutFile '%BIN%\makeit.exe'"

if not exist "%BIN%\makeit.exe" (
    echo.
    powershell -NoProfile -Command "Write-Host 'ERROR: Download failed' -ForegroundColor Red"
    pause
    exit /b 1
)

powershell -NoProfile -Command "Write-Host 'Download successful!' -ForegroundColor Green"

echo.
powershell -NoProfile -Command "Write-Host 'Adding PATH...' -ForegroundColor Yellow"

setx PATH "%PATH%;%BIN%" >nul

powershell -NoProfile -Command "Write-Host 'PATH updated.' -ForegroundColor Green"

echo.
echo ----------------------------------------
powershell -NoProfile -Command "Write-Host 'Make It Installed Successfully!' -ForegroundColor Green"
echo ----------------------------------------

echo Location : %INSTALL%
echo Binary   : %BIN%\makeit.exe

echo.
echo Close this CMD and open a new one.
echo Run:
echo.
echo     makeit
echo.

pause
del "%~f0" >nul 2>&1
endlocal
