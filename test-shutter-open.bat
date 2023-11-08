@echo off
rem
rem Wrapper for Python script: runs a Python script with the same basename in the same directory as the .bat file
rem

REM # Copyright 2023 Martin Junius
REM #
REM # Licensed under the Apache License, Version 2.0 (the "License");
REM # you may not use this file except in compliance with the License.
REM # You may obtain a copy of the License at
REM #
REM #     http://www.apache.org/licenses/LICENSE-2.0
REM #
REM # Unless required by applicable law or agreed to in writing, software
REM # distributed under the License is distributed on an "AS IS" BASIS,
REM # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM # See the License for the specific language governing permissions and
REM # limitations under the License.

rem Search for Python 3.11 or launcher
set PYTHON=NONE
set PY=NONE
if exist "C:\Program Files\Python311\python.exe" (set PYTHON=C:\Program Files\Python311\python.exe)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe)
if exist "C:\Windows\py.exe" (set PY=C:\Windows\py.exe)
if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" (set PYTHON=%LOCALAPPDATA%\Programs\Python\Launcher\py.exe)

rem echo PYTHON="%PYTHON%"
rem echo PY="%PY%"

set CWD=%~dp0
set SCRIPT=%~dpn0.py
echo CWD="%CWD%"
echo SCRIPT="%SCRIPT%" %*
echo ARGS=%*

"%SCRIPT%" %*