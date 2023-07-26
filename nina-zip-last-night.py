#!/usr/bin/python

# Archive all N.I.N.A exposure data from the previous night, i.e. date=yesterday
# - Search all TARGET/YYYY-MM-DD directories in DATADIR
# - Look for corresponding TARGET-YYYY-MM-DD.7z archive in ZIPDIR
# - If exists, skip
# - If not, run 7z.exe to archive TARGET/YYYY-MM-DD data subdir in DATA to TARGET-YYYY-MM-DD.7z in ZIPDIR

# ChangeLog
# Version 0.1 / 2023-07-26
#       First version, copy of nina-zip-ready-data

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
VERSION = "0.1 / 2023-07-26"
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

def date_yesterday():
    return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def scan_data_dir(datadir, zipdir, date=None):
    if not date:
        date = date_yesterday()
    if OPT_V:
        print("Starting at", time_now(), "search date =", date)

    dirs = [d for d in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, d, date))]
    print(dirs)

    for target in dirs:
        if OPT_V:
            print("Target to archive:", target)
        zipfile = os.path.join(zipdir, target + "-" + date + ".7z")
        if os.path.exists(zipfile):
            if OPT_V:
                print("  Zip file", zipfile, "already exists")
        else:
            if OPT_V:
                print("  Zip file", zipfile, "must be created")
            print("{} archiving target {}/{}".format(time_now(), target, date))
            create_zip_archive(os.path.join(target, date), datadir, zipfile)



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
        prog        = "nina-zip-last-night",
        description = "Zip target data in N.I.N.A data directory from last night",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-l", "--low-priority", action="store_true", help="set process priority to low")
    arg.add_argument("-D", "--data-dir", help="N.I.N.A data directory (default "+DATADIR+")")
    arg.add_argument("-Z", "--zip-dir", help="directory for zip (.7z) files (default "+ZIPDIR+")")
    arg.add_argument("-z", "--zip-prog", help="full path of 7-zip.exe (default "+ZIPPROG+")")
    # nargs="+" for min 1 filename argument
    # arg.add_argument("filename", nargs="*", help="filename")
    args = arg.parse_args()

    OPT_V = args.verbose

    if args.data_dir:
        DATADIR = args.data_dir
    if args.zip_dir:
        ZIPDIR = args.zip_dir
    if args.zip_prog:
        ZIPPROG = args.zip_prog

    DATADIR = os.path.abspath(DATADIR)
    ZIPDIR = os.path.abspath(ZIPDIR)
    ZIPPROG = os.path.abspath(ZIPPROG)

    if OPT_V:
        print("Data directory =", DATADIR)
        print("ZIP directory  =", ZIPDIR)
        print("ZIP program    =", ZIPPROG)

    # Set process priority
    if args.low_priority:
        set_priority()

    scan_data_dir(DATADIR, ZIPDIR)



if __name__ == "__main__":
    main()
