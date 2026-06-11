@echo off
set ARC=IAS-astro-python.7z
echo Uploading iasdata:remote-config/scripts/%ARC% ...
rclone copy .\dist\%ARC% iasdata:remote-config/scripts -vP