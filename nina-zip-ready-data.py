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
# Version 0.3 / 2024-07-12
#       Refactored, reusing nina-zip-last-night.py code, same JSON config

##FIXME: combine nina-zip-last-night and nina-zip-ready-data, lots of duplicated code

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



NAME    = "nina-zip-ready-data"
VERSION = "0.3 / 2024-07-12"
AUTHOR  = "Martin Junius"

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

    def zip_prog(self):
        dirs = self._get_dirs()
        return dirs["zip program"]


config = ZipConfig(CONFIG)



# options
class Options:
    no_action = False                                       # -n --no_action
    datadir   = config.data_dir()
    zipdir    = config.zip_dir()
    zipprog   = config.zip_prog()
    zipmx     = 5                                            # normal compression, -m --max => 7 = max compression



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



def scan_data_dir(datadir, zipdir):
    ready = [f.replace(".ready", "") for f in os.listdir(datadir) if f.endswith(".ready")]
    # print(ready)

    for target in ready:
        verbose("Target ready:", target)
        zipfile = os.path.join(zipdir, target + ".7z")
        if os.path.exists(zipfile):
            verbose("  Zip file", zipfile, "already exists")
        else:
            verbose("  Zip file", zipfile, "must be created")
            print("{} archiving target {}".format(time_now(), target))
            create_zip_archive(target, datadir, zipfile)



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



def main():
    global TIMER

    arg = argparse.ArgumentParser(
        prog        = "nina-zip-ready-data",
        description = "Zip target data in N.I.N.A data directory marked as ready",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-action", action="store_true", help="dry run")
    arg.add_argument("-l", "--low-priority", action="store_true", help="set process priority to low")
    arg.add_argument("-D", "--data-dir", help="N.I.N.A data directory (default "+Options.datadir+")")
    arg.add_argument("-Z", "--zip-dir", help="directory for zip (.7z) files (default "+Options.zipdir+")")
    arg.add_argument("-t", "--time-interval", type=int, help="time interval for checking data directory (default 60s)")
    arg.add_argument("-z", "--zip-prog", help="full path of 7-zip.exe (default "+Options.zipprog+")")
    arg.add_argument("-m", "--zip_max", action="store_true", help="7-zip max compression -mx7")
    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()
        ic(sys.version_info)

    Options.no_action = args.no_action

    if args.data_dir:
        Options.datadir = args.data_dir
    if args.zip_dir:
        Options.zipdir  = args.zip_dir
    if args.zip_prog:
        Options.zipprog = args.zip_prog
    if args.zip_max:
        Options.zipmx   = 7

    Options.datadir = os.path.abspath(Options.datadir)
    Options.zipdir  = os.path.abspath(Options.zipdir)
    Options.zipprog = os.path.abspath(Options.zipprog)

    verbose("Data directory =", Options.datadir)
    verbose("ZIP directory  =", Options.zipdir)
    verbose("ZIP program    =", Options.zipprog)

    print("Waiting for ready data ... (Ctrl-C to interrupt)")

    # Set process priority
    if args.low_priority:
        set_priority()

    try:
        while True:
            scan_data_dir(Options.datadir, Options.zipdir)
            # if verbose.enabled:
            #     print("Waiting ... ({:d}s, Ctrl-C to interrupt)".format(TIMER))
            time.sleep(TIMER)
    except:
        print("Terminating ...")



if __name__ == "__main__":
    main()
