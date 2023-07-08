#!/usr/bin/python

# Automatically archive N.I.N.A exposure when a target sequence has been completed,
# relying on the .ready flags created by nina-flag-ready.bat run as an External Script
# from within N.I.N.A
# - Search TARGET.ready files in DATADIR
# - Look for corresponding TARGET.7z archive in ZIPDIR
# - If exists, skip
# - If not, run 7z.exe to archive TARGET data subdir in DATA to TARGET.7z in ZIPDIR
# - Loop continuously

# ChangeLog
# Version 0.1 / 2023-07-08
#       First version of script

import sys
import os
import argparse
import subprocess
import time


global VERSION, AUTHOR
VERSION = "0.1 / 2023-07-08"
AUTHOR  = "Martin Junius"

global DATADIR, ZIPDIR, ZIPPROG, TIMER
DATADIR = "D:/Users/remote/Documents/NINA-Data"
# use %ONEDRIVE%
ZIPDIR  = "C:/Users/remote/OneDrive/Remote-Upload"
ZIPPROG = "C:/Program Files/7-Zip/7z.exe"
TIMER   = 60



def scan_data_dir(datadir, zipdir):
    ready = [f.replace(".ready", "") for f in os.listdir(datadir) if f.endswith(".ready")]
    # print(ready)

    for target in ready:
        if OPT_V:
            print("Target ready:", target)
        zipfile = os.path.join(zipdir, target + ".7z")
        if os.path.exists(zipfile):
            if OPT_V:
                print("  Zip file", zipfile, "already exists")
        else:
            if OPT_V:
                print("  Zip file", zipfile, "must be created")
            create_zip_archive(target, datadir, zipfile)



def create_zip_archive(target, datadir, zipfile):
    # 7z.exe a -t7z -mx=7 -r -spf zipfile target
    subprocess.run(args=[ZIPPROG, "a", "-t7z", "-mx=7", "-r", "-spf", zipfile, target], shell=False, cwd=datadir)



def main():
    arg = argparse.ArgumentParser(
        prog        = "nina-zip-ready-data",
        description = "Zip target data in N.I.N.A data directory marked as ready",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-D", "--data-dir", help="N.I.N.A data directory")
    arg.add_argument("-Z", "--zip-dir", help="directory for zip (.7z) files")
    arg.add_argument("-t", "--time-interval", type=int, help="time interval for checking data directory (default 60s)")
    arg.add_argument("-z", "--zip-prog", help="full path of 7-zip.exe (default \"c:\Program Files\7-Zip\7z.exe\")")
    # nargs="+" for min 1 filename argument
    # arg.add_argument("filename", nargs="*", help="filename")
    args = arg.parse_args()

    global OPT_V
    global DATADIR, ZIPDIR, ZIPPROG, TIMER
    OPT_V = args.verbose

    if args.data_dir:
        DATADIR = os.path.abspath(args.data_dir)
    if args.zip_dir:
        ZIPDIR = os.path.abspath(args.zip_dir)
    if args.time_interval:
        TIMER = args.time_interval
    if args.zip_prog:
        ZIPPROG = args.zip_prog

    try:
        while True:
            scan_data_dir(DATADIR, ZIPDIR)
            if OPT_V:
                print("Waiting ... ({:d}s, Ctrl-C to interrupt)".format(TIMER))
            time.sleep(TIMER)
    except:
        print("Terminating ...")



if __name__ == "__main__":
    main()
