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
# Version 0.2 / 2023-07-09
#       Added process priority setting, -l option

import sys
import os
import argparse
import subprocess
import time
import datetime
import platform
# The following libs must be installed with pip
import psutil


global VERSION, AUTHOR
VERSION = "0.2 / 2023-07-09"
AUTHOR  = "Martin Junius"

global DATADIR, ZIPDIR, ZIPPROG, TIMER
DATADIR = "D:/Users/remote/Documents/NINA-Data"
# use %ONEDRIVE%
ZIPDIR  = "C:/Users/remote/OneDrive/Remote-Upload"
ZIPPROG = "C:/Program Files/7-Zip/7z.exe"
TIMER   = 60



def set_priority():
    system = platform.system()
    if system == 'Windows':
        proc = psutil.Process(os.getpid())
        # Windows priority classes:
        #   ABOVE_NORMAL_PRIORITY_CLASS     = 0x8000
        #   BELOW_NORMAL_PRIORITY_CLASS     = 0x4000
        #   HIGH_PRIORITY_CLASS             = 0x0080
        #   IDLE_PRIORITY_CLASS             = 0x0040
        #   NORMAL_PRIORITY_CLASS           = 0x0020
        #   REALTIME_PRIORITY_CLASS         = 0x0100
        # Order low -> high: [0x0040,0x4000,0x0020,0x8000,0x0080,0x0100]

        # prio = psutil.HIGH_PRIORITY_CLASS
        # prio = psutil.BELOW_NORMAL_PRIORITY_CLASS
        prio = psutil.IDLE_PRIORITY_CLASS           # low priority
        prio0 = proc.nice()
        proc.nice(prio)
        if OPT_V:
            print(proc)
            print("System {}, setting process priority {} -> {}".format(system, prio0, prio))



def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")



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
            print("{} archiving target {}".format(time_now(), target))
            create_zip_archive(target, datadir, zipfile)



def create_zip_archive(target, datadir, zipfile):
    # 7z.exe a -t7z -mx=7 -r -spf zipfile target
    #   a       add files to archive
    #   -t7z    set archive type to 7z
    #   -mx7    set compression level to maximum (5=normal, 7=maximum, 9=ultra)
    #   -r      recurse subdirectories
    #   -spf    use fully qualified file paths
    subprocess.run(args=[ZIPPROG, "a", "-t7z", "-mx7", "-r", "-spf", zipfile, target], shell=False, cwd=datadir)



def main():
    global OPT_V
    global DATADIR, ZIPDIR, ZIPPROG, TIMER

    arg = argparse.ArgumentParser(
        prog        = "nina-zip-ready-data",
        description = "Zip target data in N.I.N.A data directory marked as ready",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-l", "--low-priority", action="store_true", help="set process priority to low")
    arg.add_argument("-D", "--data-dir", help="N.I.N.A data directory (default "+DATADIR+")")
    arg.add_argument("-Z", "--zip-dir", help="directory for zip (.7z) files (default "+ZIPDIR+")")
    arg.add_argument("-t", "--time-interval", type=int, help="time interval for checking data directory (default 60s)")
    arg.add_argument("-z", "--zip-prog", help="full path of 7-zip.exe (default "+ZIPPROG+")")
    # nargs="+" for min 1 filename argument
    # arg.add_argument("filename", nargs="*", help="filename")
    args = arg.parse_args()

    OPT_V = args.verbose

    if args.data_dir:
        DATADIR = args.data_dir
    if args.zip_dir:
        ZIPDIR = args.zip_dir
    if args.time_interval:
        TIMER = args.time_interval
    if args.zip_prog:
        ZIPPROG = args.zip_prog

    DATADIR = os.path.abspath(DATADIR)
    ZIPDIR = os.path.abspath(ZIPDIR)
    ZIPPROG = os.path.abspath(ZIPPROG)

    if OPT_V:
        print("Data directory =", DATADIR)
        print("ZIP directory  =", ZIPDIR)
        print("ZIP program    =", ZIPPROG)
    else:
        print("Waiting for ready data ... (Ctrl-C to interrupt)")


    # Set process priority
    if args.low_priority:
        set_priority()

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
