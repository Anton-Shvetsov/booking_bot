@echo off
setlocal

set ROOT=%USERPROFILE%\BookingBot
set ZIP_URL=https://github.com/Anton-Shvetsov/booking_bot/archive/refs/heads/master.zip
set ZIP_FILE=%ROOT%\archive.zip

echo ============================================================================
echo Downloading BookingBot from GitHub
echo Target folder: %ROOT%
echo ============================================================================

if not exist "%ROOT%" mkdir "%ROOT%"

set "IS_EMPTY=1"
for /f %%i in ('dir "%ROOT%" /a /b') do set "IS_EMPTY=0"

if "%IS_EMPTY%"=="1" (
    set "DOWNLOADED=1"
    if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%"
    echo Downloading archive...
    powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_FILE%'"
    echo Extracting archive...
    powershell -Command "Expand-Archive -LiteralPath '%ZIP_FILE%' -DestinationPath '%ROOT%' -Force"
    if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%"
    for /d %%D in ("%ROOT%\*-main") do (
        echo Moving contents from %%~nxD to ROOT...
        xcopy "%%D\*" "%ROOT%\" /s /e /y >nul
        echo Removing temporary folder %%~nxD...
        rmdir /s /q "%%D"
    )
) else (
    echo Folder is not empty. Uninstall BookingBot first.
    set "DOWNLOADED=0"
)

echo ============================================================================
echo Repository ready in: %ROOT%
echo ============================================================================

if "%DOWNLOADED%"=="1" (
    if exist "%ROOT%\SetUp.bat" (
        echo Running SetUp.bat...
        call "%ROOT%\SetUp.bat"
    )
)

pause
