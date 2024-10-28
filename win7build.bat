REM windows7 python https://github.com/adang1345/PythonWin7/blob/master/3.10.11

@echo off

if defined ProgramFiles(x86) (
    echo 64 bit system
	set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python310"
	if not exist "%PYTHON_PATH%" (
		set "PYTHON_PATH=%APPDATA%\Python\Python310"
	)
) else (
    echo 32 bit system
	set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python310-32"
	if not exist "%PYTHON_PATH%" (
		set "PYTHON_PATH=%APPDATA%\Python\Python310-32"
	)
)
set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"
python -V
for /f "delims=" %%i in ('python -V 2^>^&1') do set "PYTHON_VERSION=%%i"
if "%PYTHON_VERSION%" neq "Python 3.10.11" (
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