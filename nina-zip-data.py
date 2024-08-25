#!/usr/bin/env python

# Copyright 2023-2024 Martin Junius
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

## --ready mode
# Automatically archive N.I.N.A exposure when a target sequence has been completed,
# relying on the .ready flags created by nina-flag-ready.bat run as an External Script
# from within N.I.N.A
# - Search TARGET.ready files in DATADIR
# - Look for corresponding TARGET.7z archive in ZIPDIR
# - If exists, skip
# - If not, run 7z.exe to archive TARGET data subdir in DATA to TARGET.7z in ZIPDIR
# - Loop continuously

## --last mode
# Archive all N.I.N.A exposure data from the previous night, i.e. date=yesterday
# - Search all TARGET*YYYY-MM-DD directories in DATADIR
# - Look for corresponding TARGET-YYYY-MM-DD.7z archive in ZIPDIR
# - If exists, skip
# - If not, run 7z.exe to archive TARGET/YYYY-MM-DD data subdir in DATA to TARGET-YYYY-MM-DD.7z in ZIPDIR

## --date mode
# Like --last, but using the specified DATE

# ChangeLog
# Version 0.1 / 2023-07-08
#       First version of script
# Version 0.2 / 2023-07-09
#       Added process priority setting, -l option
# Version 0.3 / 2024-07-12
#       Refactored, reusing nina-zip-last-night.py code, same JSON config
# Version 0.4 / 2024-08-25
#       Copy of nina-zip-ready-data, will combine nina-zip-last-night and nina-zip-ready-data
# Version 1.0 / 2024-08-25
#       Combined version, integrating nina-zip-last-night functionality (Options --last / --date)

import os
import argparse
import subprocess
import datetime
import platform
import sys
import socket
import time

# The following libs must be installed with pip
import psutil
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose import verbose, warning, error
from jsonconfig import JSONConfig



NAME        = "nina-zip-data"
DESCRIPTION = "Zip (7z) N.I.N.A data and upload"
VERSION     = "0.4 / 2024-08-25"
AUTHOR      = "Martin Junius"

TIMER   = 60

CONFIG = "nina-zip-config.json"

class ZipConfig(JSONConfig):
    """ JSON Config for data / zip directory """

    def __init__(self, file=None):
        super().__init__(file)

    def _get_dirs(self):
        hostname = socket.gethostname()
        ic(hostname)
        if hostname in self.config:
            return self.config[hostname]
        error(f"no directory config for hostname {hostname}")

    def data_dir(self):
        dirs = self._get_dirs()
        return dirs["data dir"]

    def zip_dir(self):
        dirs = self._get_dirs()
        return dirs["zip dir"]

    def tmp_dir(self):
        dirs = self._get_dirs()
        return dirs["tmp dir"]

    def zip_prog(self):
        dirs = self._get_dirs()
        return dirs["zip program"]


config = ZipConfig(CONFIG)



def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def date_yesterday():
    return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")



# options
class Options:
    no_action = False                                       # -n --no_action
    datadir   = config.data_dir()
    zipdir    = config.zip_dir()
    tmpdir    = config.tmp_dir()
    zipprog   = config.zip_prog()
    zipmx     = 5                                            # normal compression, -m --max => 7 = max compression
    run_ready = False
    run_last  = False
    timer     = TIMER
    date      = date_yesterday()



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



def scan_data_dir_ready_mode(datadir, zipdir):
    ready = [f.replace(".ready", "") for f in os.listdir(datadir) if f.endswith(".ready")]
    # print(ready)

    for target in ready:
        # verbose("Target ready:", target)
        zipfile = os.path.join(zipdir, target + ".7z")
        if os.path.exists(zipfile):
            # verbose("  Zip file", zipfile, "already exists")
            pass
        else:
            verbose(f"target ready: {target}")
            msg = f"{time_now()} archiving target {target}"
            print(msg)
            print("=" * len(msg))
            verbose(f"zip file {zipfile}")
            create_zip_archive(target, datadir, zipfile)
            print("=" * len(msg))



def scan_data_dir_last_mode(datadir, zipdir, date=None):
    # TARGET/YYYY-MM-DD directories
    dirs = [d for d in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, d, date))]
    ic(dirs)
    if dirs:
        scan_targets(datadir, zipdir, dirs, date)
    # TARGET-YYYY-MM-DD directories
    dirs = [d.replace("-" + date, "").replace("_" + date, "") for d in os.listdir(datadir) if d.endswith(date)]
    ic(dirs)
    if dirs:
        scan_targets(datadir, zipdir, dirs, date)



def scan_targets(datadir, zipdir, targets, date):
    for target in targets:
        verbose("target to archive:", target)
        zipfile1 = os.path.join(zipdir, target + ".7z")
        zipfile  = os.path.join(zipdir, target + "-" + date + ".7z")
        if os.path.exists(zipfile1):
            verbose(f"7z file {zipfile1} already exists")
        elif os.path.exists(zipfile):
            verbose(f"7z file {zipfile} already exists")
        else:
            # TARGET-YYYY-MM-DD/ directories
            if os.path.isdir(os.path.join(datadir, target + "-" + date)):
                verbose(f"{time_now()} archiving {target}-{date}")
                create_zip_archive(target + "-" + date, datadir, zipfile)
            # TARGET_YYYY-MM-DD/ directories
            elif os.path.isdir(os.path.join(datadir, target + "_" + date)):
                verbose(f"{time_now()} archiving {target}_{date}")
                create_zip_archive(target + "_" + date, datadir, zipfile)
            # TARGET/YYYY-MM-DD/ directories
            elif os.path.isdir(os.path.join(datadir, target, date)):
                verbose(f"{time_now()} archiving {target}/{date}")
                create_zip_archive(os.path.join(target, date), datadir, zipfile)
            # Unsupported
            else:
                warning(f"no supported directory structure for {target} {date} found!")            



def create_zip_archive(target, datadir, zipfile):
    # 7z.exe a -t7z -mx=7 -r -spf zipfile target
    #   a       add files to archive
    #   -t7z    set archive type to 7z
    #   -mx7    set compression level to maximum (5=normal, 7=maximum, 9=ultra)
    #   -r      recurse subdirectories
    #   -spf    use fully qualified file paths
    args7z = [ Options.zipprog, "a", "-t7z", f"-mx{Options.zipmx}", "-r", "-spf", zipfile, target ]
    verbose("run", " ".join(args7z))
    if not Options.no_action:
        subprocess.run(args=args7z, shell=False, cwd=datadir)



def run_ready():
    try:
        while True:
            scan_data_dir_ready_mode(Options.datadir, Options.zipdir)
            # if verbose.enabled:
            #     print("Waiting ... ({:d}s, Ctrl-C to interrupt)".format(TIMER))
            time.sleep(Options.timer)
    except KeyboardInterrupt:
        print("Terminating ...")



def run_last(targetlist=None):
    if targetlist:
        targets = targetlist.split(",")
        scan_targets(Options.datadir, Options.zipdir, targets, Options.date)
    else:
        scan_data_dir_last_mode(Options.datadir, Options.zipdir, Options.date)



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = DESCRIPTION,
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-action", action="store_true", help="dry run")
    arg.add_argument("-l", "--low-priority", action="store_true", help="set process priority to low")

    arg.add_argument("-D", "--data-dir", help=f"N.I.N.A data directory (default {Options.datadir})")
    arg.add_argument("-Z", "--zip-dir", help=f"directory for zip (.7z) files (default {Options.zipdir})")
    arg.add_argument("-T", "--tmp-dir", help=f"temp directory for zip (.7z) files (default {Options.tmpdir})")
    arg.add_argument("--ready", action="store_true", help="run in TARGET.ready mode")
    arg.add_argument("-t", "--time-interval", type=int, help="time interval for checking data directory (default 60s)")
    arg.add_argument("--last", action="store_true", help=f"run in last night mode ({Options.date})")
    arg.add_argument("--date", help="run in archive data from DATE mode")
    arg.add_argument("--targets", help="archive TARGET[,TARGET] only (--last / --date)")
    arg.add_argument("-z", "--zip-prog", help="full path of 7-zip.exe (default "+Options.zipprog+")")
    arg.add_argument("-m", "--zip_max", action="store_true", help="7-zip max compression -mx7")
    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path)

    Options.no_action = args.no_action

    if args.data_dir:
        Options.datadir = args.data_dir
    if args.zip_dir:
        Options.zipdir  = args.zip_dir
    if args.tmp_dir:
        Options.tmpdir  = args.tmp_dir
    if args.zip_prog:
        Options.zipprog = args.zip_prog
    if args.zip_max:
        Options.zipmx   = 7
    if args.time_interval:
        Options.timer   = args.time_interval
    Options.run_ready = args.ready
    Options.run_last  = args.last
    if args.date:
        Options.date = args.date
        Options.run_last = True

    Options.datadir = os.path.abspath(Options.datadir)
    Options.zipdir  = os.path.abspath(Options.zipdir)
    Options.tmpdir  = os.path.abspath(Options.tmpdir)
    Options.zipprog = os.path.abspath(Options.zipprog)

    verbose(f"Data directory = {Options.datadir}")
    verbose(f"ZIP directory  = {Options.zipdir}")
    verbose(f"Tmp directory  = {Options.tmpdir}")
    verbose(f"ZIP program    = {Options.zipprog}")
    verbose(f"Date           = {Options.date}")

    # Set process priority
    if args.low_priority:
        set_priority()

    if Options.run_ready:
        # --ready mode
        print("Waiting for ready data ... (Ctrl-C to interrupt)")
        run_ready()
    elif Options.run_last:
        # --last / --date mode
        run_last(args.targets)
    else:
        error("must specify mode, one of --ready / --last / --date")



if __name__ == "__main__":
    main()
