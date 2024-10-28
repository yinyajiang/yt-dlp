REM windows7 python https://github.com/adang1345/PythonWin7/blob/master/3.10.11

@echo off

set "PYTHON_VERSION=3.10.11"
set "PYTHON_DIR_NAME=Python310"

if not defined ProgramFiles(x86) (
    echo 32 bit system
	set "PYTHON_DIR_NAME=%PYTHON_DIR_NAME%-32"
)

set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\%PYTHON_DIR_NAME%"
if not exist "%PYTHON_PATH%" (
	set "PYTHON_PATH=%APPDATA%\Python\%PYTHON_DIR_NAME%"
)
set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"

echo %PATH%

%PYTHON_PATH%\python -V
for /f "delims=" %%i in ('python -V 2^>^&1') do set "CUR_PYTHON_VERSION=%%i"
if "%CUR_PYTHON_VERSION%" neq "%PYTHON_VERSION%" (
    echo Python version is not 3.10.11, exiting...
    exit /b 1
)
echo "python version is good!!"

REM Install Requirements
%PYTHON_PATH%\python devscripts/install_deps.py -o --include build
%PYTHON_PATH%\python devscripts/install_deps.py --include curl-cffi
%PYTHON_PATH%\python -m pip install -U "https://yt-dlp.github.io/Pyinstaller-Builds/x86_64/pyinstaller-6.10.0-py3-none-any.whl"


REM Prepare
%PYTHON_PATH%\python devscripts/update-version.py "2024.01.01"
%PYTHON_PATH%\python devscripts/make_lazy_extractors.py
      
REM Prepare
%PYTHON_PATH%\python -m bundle.pyinstaller --onedir
%PYTHON_PATH%\powershell -Command "Compress-Archive -Path ./dist/yt-dlp/* -DestinationPath ./dist/yt-dlp_win7.zip"