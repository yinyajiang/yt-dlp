REM windows7 python https://github.com/adang1345/PythonWin7/blob/master/3.10.11

@echo off
setlocal enabledelayedexpansion

set "PYTHON_VERSION=3.10.11"
set "PYTHON_DIR_NAME=Python310"
set "isX86=0"

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

git pull

if %isx86% neq 1 (
    echo This is x64 architecture
	
	REM Install Requirements
	python devscripts/install_deps.py -o --include build
	python devscripts/install_deps.py --include curl-cffi
	python -m pip install -U "https://yt-dlp.github.io/Pyinstaller-Builds/x86_64/pyinstaller-6.10.0-py3-none-any.whl"

	REM Prepare
	python devscripts/update-version.py "2024.01.01"
	python devscripts/make_lazy_extractors.py
		  
	REM Prepare
	python -m bundle.pyinstaller --onedir -n yt-dlp
	powershell -Command "Compress-Archive -Path ./dist/yt-dlp/* -DestinationPath ./dist/yt-dlp_win7.zip"

) else (
    echo This is x32 architecture
	
	REM Install Requirements
	python devscripts/install_deps.py -o --include build
	python devscripts/install_deps.py
	python -m pip install -U "https://yt-dlp.github.io/Pyinstaller-Builds/i686/pyinstaller-6.10.0-py3-none-any.whl"

	REM Prepare
	python devscripts/update-version.py -c "${{ inputs.channel }}" -r "${{ needs.process.outputs.origin }}" "${{ inputs.version }}"
	python devscripts/make_lazy_extractors.py

	REM Build
	python -m bundle.pyinstaller
	python -m bundle.pyinstaller --onedir -n yt-dlp
	powershell -Command "Compress-Archive -Path ./dist/yt-dlp/* -DestinationPath ./dist/yt-dlp_win_x86.zip"
)
pause

