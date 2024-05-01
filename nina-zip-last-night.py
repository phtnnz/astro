#!/usr/bin/env python

# Copyright 2023 Martin Junius
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Archive all N.I.N.A exposure data from the previous night, i.e. date=yesterday
# - Search all TARGET/YYYY-MM-DD directories in DATADIR
# - Look for corresponding TARGET-YYYY-MM-DD.7z archive in ZIPDIR
# - If exists, skip
# - If not, run 7z.exe to archive TARGET/YYYY-MM-DD data subdir in DATA to TARGET-YYYY-MM-DD.7z in ZIPDIR

# ChangeLog
# Version 0.1 / 2023-07-26
#       First version, copy of nina-zip-ready-data
# Version 0.2 / 2024-05-01
#       Support TARGET-YYYY-MM-DD/ directory names

import os
import argparse
import subprocess
import datetime
import platform
import re
# The following libs must be installed with pip
import psutil
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose import verbose, warning, error



NAME    = "nina-zip-last-night"
VERSION = "0.2 / 2024-05-01"
AUTHOR  = "Martin Junius"



# options
class Options:
    no_action = False                                       # -n --no_action
    datadir   = "D:/Users/remote/Documents/NINA-Data"
    # FIXME: use %ONEDRIVE%
    zipdir   = "C:/Users/remote/OneDrive/Remote-Upload"
    zipprog  = "C:/Program Files/7-Zip/7z.exe"
    timer    = 60



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
        verbose(f"{proc}")
        verbose(f"system {system}, setting process priority {prio0} -> {prio}")



def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def date_yesterday():
    return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")



def scan_data_dir(datadir, zipdir, date=None):
    # TARGET/YYYY-MM-DD directories
    dirs = [d for d in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, d, date))]
    ic(dirs)
    if dirs:
        scan_targets(datadir, zipdir, dirs, date)
    # TARGET-YYYY-MM-DD directories
    dirs = [d.replace("-" + date, "") for d in os.listdir(datadir) if d.endswith(date)]
    ic(dirs)
    if dirs:
        scan_targets(datadir, zipdir, dirs, date)



def scan_targets(datadir, zipdir, targets, date):
    for target in targets:
        verbose("Target to archive:", target)
        zipfile1 = os.path.join(zipdir, target + ".7z")
        zipfile  = os.path.join(zipdir, target + "-" + date + ".7z")
        if os.path.exists(zipfile1):
            verbose("7z file", zipfile1, "already exists")
        elif os.path.exists(zipfile):
            verbose("7z file", zipfile, "already exists")
        else:
            verbose("7z file", zipfile, "to be created ...")
            # TARGET-YYYY-MM-DD/ directories
            if os.path.isdir(os.path.join(datadir, target + "-" + date)):
                verbose(f"{time_now()} archiving {target}/{date}")
                create_zip_archive(target + "-" + date, datadir, zipfile)
            # TARGET/YYYY-MM-DD/ directories
            elif os.path.isdir(os.path.join(datadir, target, date)):
                verbose(f"{time_now()} archiving {target}-{date}")
                create_zip_archive(os.path.join(target, date), datadir, zipfile)
            # Unsupported
            else:
                warning(f"No supported directory structure for {target} {date} found!")            



def create_zip_archive(target, datadir, zipfile):
    # 7z.exe a -t7z -mx=7 -r -spf zipfile target
    #   a       add files to archive
    #   -t7z    set archive type to 7z
    #   -mx7    set compression level to maximum (5=normal, 7=maximum, 9=ultra)
    #   -r      recurse subdirectories
    #   -spf    use fully qualified file paths
    args7z = [ Options.zipprog, "a", "-t7z", "-mx7", "-r", "-spf", zipfile, target ]
    verbose("run", " ".join(args7z))
    if not Options.no_action:
        subprocess.run(args=args7z, shell=False, cwd=datadir)



def main():

    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Zip target data in N.I.N.A data directory from last night",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-action", action="store_true", help="dry run")
    arg.add_argument("-l", "--low-priority", action="store_true", help="set process priority to low")
    arg.add_argument("--date", help="archive target/DATE, default last night "+date_yesterday())
    arg.add_argument("-t", "--targets", help="archive TARGET[,TARGET] only")
    arg.add_argument("-D", "--data-dir", help="N.I.N.A data directory (default "+Options.datadir+")")
    arg.add_argument("-Z", "--zip-dir", help="directory for zip (.7z) files (default "+Options.zipdir+")")
    arg.add_argument("-z", "--zip-prog", help="full path of 7-zip.exe (default "+Options.zipprog+")")
    # nargs="+" for min 1 filename argument
    # arg.add_argument("filename", nargs="*", help="filename")
    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()

    Options.no_action = args.no_action

    if args.data_dir:
        Options.datadir = args.data_dir
    if args.zip_dir:
        Options.zipdir  = args.zip_dir
    if args.zip_prog:
        Options.zipprog = args.zip_prog

    Options.datadir = os.path.abspath(Options.datadir)
    Options.zipdir  = os.path.abspath(Options.zipdir)
    Options.zipprog = os.path.abspath(Options.zipprog)

    date = args.date if args.date else date_yesterday()
    verbose("Data directory =", Options.datadir)
    verbose("ZIP directory  =", Options.zipdir)
    verbose("ZIP program    =", Options.zipprog)
    verbose("Date           =", date)

    # Set process priority
    if args.low_priority:
        set_priority()

    if args.targets:
        targets = args.targets.split(",")
        scan_targets(Options.datadir, Options.zipdir, targets, date)
    else:
        scan_data_dir(Options.datadir, Options.zipdir, date)



if __name__ == "__main__":
    main()
