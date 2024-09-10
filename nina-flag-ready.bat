@echo off
rem
rem Flag exposure series as ready by creating TARGET.ready file in N.I.N.A data directory
rem
rem usage: nina-flag-ready.bat "TARGET"
rem
rem "TARGET" must not contain / or :
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

rem Search for data directory
set NINADATA=NONE
if exist "D:\Users\remote\Documents\NINA-Data\" (set NINADATA=D:\Users\remote\Documents\NINA-Data)
if exist "D:\Users\remote\Documents\N.I.N.A-Data\" (set NINADATA=D:\Users\remote\Documents\N.I.N.A-Data)
if %NINADATA%==NONE (exit /b 1)

set CWD=%~dp0
set TARGET=%1
echo NINDATA="%NINADATA%" TARGET="%TARGET%"
echo Target %TARGET% - ready. > %NINADATA%\%TARGET%.ready