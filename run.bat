@echo off

set ROOT=%CD%
set VENV_DIR=%ROOT%\runtime\venv
set PYTHONPATH=%ROOT%

call "%VENV_DIR%\Scripts\activate.bat"

echo Запуск BookingBot...

"%VENV_DIR%\Scripts\python.exe" "%ROOT%\bot.py"

call "%VENV_DIR%\Scripts\deactivate.bat"
