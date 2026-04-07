REM windows7 python https://github.com/adang1345/PythonWin7/blob/master/3.10.11

@echo off
setlocal enabledelayedexpansion

set "PYTHON_VERSION=3.10.11"
set "PYTHON_DIR_NAME=Python310"
set "isX86=0"

cd /d "%~dp0"

if not defined ProgramFiles(x86) (
    echo 32 bit system
	set "PYTHON_DIR_NAME=%PYTHON_DIR_NAME%-32"
	set "isX86=1"
)

set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\%PYTHON_DIR_NAME%"
if not exist "%PYTHON_PATH%" (
	set "PYTHON_PATH=%APPDATA%\Python\%PYTHON_DIR_NAME%"
)
set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"

echo %PATH%

python -V
for /f "tokens=2" %%i in ('python -V 2^>^&1') do set CUR_PYTHON_VERSION=%%i
if "%CUR_PYTHON_VERSION%" neq "%PYTHON_VERSION%" (
    echo Python version is not %PYTHON_VERSION%, exiting...
    exit /b 1
)
echo "python version is good!!"

git restore .
git pull

if %isx86% neq 1 (
    echo This is x64 architecture
	
	REM Install Requirements
	if not exist pyi-wheels mkdir pyi-wheels
	python -m pip install -U --require-hashes -r "bundle/requirements/requirements-pip.txt"
    python -m pip install -U --require-hashes -r "bundle/requirements/requirements-win-x64-pyinstaller.txt"
    python -m pip install -U --require-hashes -r "bundle/requirements/requirements-win-x64.txt"

	REM Prepare
	python devscripts/update-version.py -c "stable" -r "yt-dlp/yt-dlp" "2024.01.01"
    python devscripts/make_lazy_extractors.py

	REM Build
	python -m bundle.pyinstaller --onedir -n yt-dlp
	powershell -Command "Compress-Archive -Force -Path ./dist/yt-dlp/* -DestinationPath ./dist/yt-dlp_win7.zip"

) else (
    echo This is x32 architecture
	
	REM Install Requirements
	if not exist pyi-wheels mkdir pyi-wheels
	python -m pip install -U --require-hashes -r "bundle/requirements/requirements-pip.txt"
    python -m pip install -U --require-hashes -r "bundle/requirements/requirements-win-x86-pyinstaller.txt"
    python -m pip install -U --require-hashes -r "bundle/requirements/requirements-win-x86.txt"

	REM Prepare
	python devscripts/update-version.py -c "stable" -r "yt-dlp/yt-dlp" "2024.01.01"
    python devscripts/make_lazy_extractors.py

	REM Build
	python -m bundle.pyinstaller --onedir -n yt-dlp
	powershell -Command "Compress-Archive -Force -Path ./dist/yt-dlp/* -DestinationPath ./dist/yt-dlp_win7_x86.zip"
)


