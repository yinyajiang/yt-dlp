REM windows7 python https://github.com/adang1345/PythonWin7/blob/master/3.10.11

@echo off

set "PYTHON_VERSION=3.10.11"
if defined ProgramFiles(x86) (
    echo 64 bit system
	set "PYTHON_DIR=Python310"
) else (
    echo 32 bit system
	set "PYTHON_DIR=Python310-32"
)

set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"

python -V
for /f "delims=" %%i in ('python -V 2^>^&1') do set "CUR_PYTHON_VERSION=%%i"
if "%CUR_PYTHON_VERSION%" neq "%PYTHON_VERSION%" (
    echo Python version is not 3.10.11, exiting...
    exit /b 1
)
echo "python version is good!!"

REM Install Requirements
python devscripts/install_deps.py -o --include build
python devscripts/install_deps.py --include curl-cffi
python -m pip install -U "https://yt-dlp.github.io/Pyinstaller-Builds/x86_64/pyinstaller-6.10.0-py3-none-any.whl"


REM Prepare
python devscripts/update-version.py "2024.01.01"
python devscripts/make_lazy_extractors.py
      
REM Prepare
python -m bundle.pyinstaller --onedir
powershell -Command "Compress-Archive -Path ./dist/yt-dlp/* -DestinationPath ./dist/yt-dlp_win7.zip"