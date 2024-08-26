@echo off
echo Creating new distribution archive ...
del IAS-astro-python.7z
"C:\Program Files\7-Zip\7z.exe" a -t7z -spf -xr!__pycache__ IAS-astro-python.7z @files.dist