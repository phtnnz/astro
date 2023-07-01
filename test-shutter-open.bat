@echo off
rem
rem Wrapper for Python script: runs a Python script with the same basename in the same directory as the .bat file
rem

rem Search for Python 3.11 or launcher
set PYTHON=NONE
set PY=NONE
if exist "C:\Program Files\Python311\python.exe" (set PYTHON=C:\Program Files\Python311\python.exe)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe)
if exist "C:\Windows\py.exe" (set PY=C:\Windows\py.exe)
if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" (set PYTHON=%LOCALAPPDATA%\Programs\Python\Launcher\py.exe)

set CWD=%~dp0
set SCRIPT=%~dpn0.py
echo CWD="%CWD%"
echo PYTHON="%PYTHON%"
echo PY="%PY%"
echo SCRIPT="%SCRIPT%"
echo ARGS=%*

"%SCRIPT%" %*