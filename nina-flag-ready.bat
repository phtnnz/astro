@echo off
rem
rem Flag exposure series as ready by creating TARGET.ready file in N.I.N.A data directory
rem
rem usage: nina-flag-ready.bat "TARGET"
rem
rem "TARGET" must not contain / or :
rem

rem Search for data directory
set NINADATA=NONE
if exist "D:\Users\remote\Documents\NINA-Data\" (set NINADATA=D:\Users\remote\Documents\NINA-Data)
if exist "D:\Users\remote\Documents\N.I.N.A-Data\" (set NINADATA=D:\Users\remote\Documents\N.I.N.A-Data)
if %NINADATA%==NONE (exit /b 1)

set CWD=%~dp0
set TARGET=%1
echo CWD="%CWD%"
echo NINDATA="%NINADATA%"
echo TARGET="%TARGET%"
rem @echo on
echo Target %TARGET% - ready. > %NINADATA%\%TARGET%.ready