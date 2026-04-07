@echo off
setlocal

set ROOT=%USERPROFILE%\BookingBot
set SHORTCUT=%USERPROFILE%\Desktop\BookingBot.lnk

echo ============================================================================
echo Удаление BookingBot
echo ============================================================================

if exist "%ROOT%" (
    echo Удаление файлов проекта...
    rmdir /s /q "%ROOT%"
) else (
    echo Папка проекта не найдена. Пропуск.
)

if exist "%SHORTCUT%" (
    echo Удаление ярлыка с Рабочего стола...
    del /f /q "%SHORTCUT%"
) else (
    echo Ярлык не найден. Пропуск.
)

echo ============================================================================
echo BookingBot успешно удалён
echo ============================================================================
pause
