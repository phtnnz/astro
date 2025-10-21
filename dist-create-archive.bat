@echo off
set DISTARC=dist\IAS-templates.7z
set DISTLIST=dist\files1.dist
echo Creating new distribution archive %DISTARC% ...
del %DISTARC%
"C:\Program Files\7-Zip\7z.exe" a -t7z -spf -xr!__pycache__ %DISTARC% @%DISTLIST%

set DISTARC=dist\IAS-astro-python.7z
set DISTLIST=dist\files2.dist
echo Creating new distribution archive %DISTARC% ...
del %DISTARC%
"C:\Program Files\7-Zip\7z.exe" a -t7z -spf -xr!__pycache__ %DISTARC% @%DISTLIST%
