@echo off
setlocal EnableDelayedExpansion

for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "ESC=%%b"
)

cd /d "%~dp0"
git pull

echo Fetching from upstream...
git fetch upstream

if %errorlevel% neq 0 (
    echo Error: Failed to fetch from upstream
    exit /b %errorlevel%
)

echo Merging upstream...
git merge upstream

if %errorlevel% equ 0 (
    echo Merge successful!
    echo Running winformat.bat...
    call winformat.bat

) else (
    echo Merge conflict detected!
    echo !ESC![31m
    set /p "confirm=Press Y to launch merge tool: "
    echo !ESC![0m
    echo Debug: You entered [!confirm!]
    if /i not "!confirm!"=="Y" (
        echo Merge cancelled by user.
		pause
        exit /b 1
    )
    echo Launching merge tool...
    git mergetool

    echo Waiting for you to resolve conflicts...
    echo Press any key when conflicts are resolved...
    pause >nul

    echo Running winformat.bat...
    call winformat.bat
)
