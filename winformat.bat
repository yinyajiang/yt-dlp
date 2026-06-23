@echo off
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

cd /d "%~dp0/yt_dlp"

call conda activate py314

echo %ESC%[31mRuff check and fix... dont close the window%ESC%[0m
ruff check . --fix --unsafe-fixes
echo %ESC%[31mAutopep8 fix... dont close the window%ESC%[0m
autopep8 -i .
echo %ESC%[32mDone.%ESC%[0m
pause