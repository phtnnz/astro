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
#
## --last mode
# Archive all N.I.N.A exposure data from the previous night, i.e. date=yesterday
# - Search all TARGET*YYYY-MM-DD directories in DATADIR
# - Look for corresponding TARGET-YYYY-MM-DD.7z archive in ZIPDIR
# - If exists, skip
# - If not, run 7z.exe to archive TARGET/YYYY-MM-DD data subdir in DATA to TARGET-YYYY-MM-DD.7z in ZIPDIR
#
## --date mode
# Like --last, but using the specified DATE, can be used together with --subdir, then
# specifies the date added to SUBDIR
#
## --subdir mode
# Like --ready, but search in N.I.N.A datadir / SUBDIR_YYYY-MM-DD 
#
# Adding --ready and --last override the implied behavior of --date and --subdir


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
# Version 1.1 / 2024-08-26
#       Implemented support for rclone
# Version 1.2 / 2024-08-28
#       Added --hostname option to select config settings
#       Removed -D --data-dir, -Z --zip-dir, -T --tmp-dir, -z --zip-prog options
# Version 1.3 / 2024-08-28
#       Added --subdir option: invokes --ready mode, search in data dir/subdir_YYYY-MM-DD,
#       uploads with move/rclone will add subdir_YYYY-MM-DD instead of YYYY/MM to zip dir path
# Version 1.4 / 2024-08-29
#       Added "zip sub" to config file, override of default "%Y/%m" for sub directory
#       under zip dir
# Version 1.5 / 2024-10-05
#       Changed -m (new --mx) Option to directly pass parameter to 7z.exe -mx switch
# Version 1.6 / 2025-01-09
#       Slightly changed options logic for --last, --date, --ready, --subdir
#       When --subdir is specified, upload to ZIPDIR/SUBDIR/ZIPSUB/SUBDIR_DATE
# Version 1.7 / 2025-06-19
#       If archive already exists in tmp dir and not at dest, retry upload

import os
import argparse
import subprocess
import datetime
import platform
import sys
import socket
import time
import shutil

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
VERSION     = "1.7 / 2025-06-19"
AUTHOR      = "Martin Junius"

TIMER   = 60
ZIP_SUB = "%Y/%m"

CONFIG = "nina-zip-config.json"

## Config:
# "<HOSTNAME>": {
#         "##":             "<COMMENT>",
#         "zip program":    "C:/Program Files/7-Zip/7z.exe",
#         "rclone program": "C:/Tools/rclone/rclone.exe",
#         "data dir":        "<SOMEWHERE>/NINA-Data",
#         "tmp dir":         "<SOMEWHERE>/NINA-Tmp",
#         "zip dir":         "<SOMEWHERE>/OneDrive/Upload",
#         "zip sub":         "<STRFTIME_PLACEHOLDERS>"
#         "upload":          "move"
#     },
# or
# "<HOSTNAME>": {
#         "##":             "<COMMENT>",
#         "zip program":    "C:/Program Files/7-Zip/7z.exe",
#         "rclone program": "C:/Tools/rclone/rclone.exe",
#         "data dir":       "<SOMEWHERE>/NINA-Data",
#         "tmp dir":        "<SOMEWHERE>/NINA-Tmp",
#         "zip dir":        "<REMOTENAME>:<BUCKETNAME>",
#         "zip sub":        "<STRFTIME_PLACEHOLDERS>"
#         "upload":         "rclone"
#     },

# Default "zip sub" = "%Y/%m"
#         "upload"  = "move"

class ZipConfig(JSONConfig):
    """JSON config for directories / programs &c."""

    hostname  = socket.gethostname()

    def __init__(self, file=None):
        super().__init__(file)

    def _get_dirs(self):
        # ic(ZipConfig.hostname)
        if ZipConfig.hostname in self.config:
            return self.config[ZipConfig.hostname]
        error(f"no directory config for hostname {ZipConfig.hostname}")

    def data_dir(self):
        """Return N.I.N.A Image file path"""
        dirs = self._get_dirs()
        return dirs.get("data dir")

    def zip_dir(self):
        """Return upload directory for completed 7z archives"""
        dirs = self._get_dirs()
        return dirs.get("zip dir")

    def zip_sub(self):
        """Return sub directory in upload directory for completed 7z archives (strftime placeholder)"""
        dirs = self._get_dirs()
        return dirs.get("zip sub") or ZIP_SUB

    def tmp_dir(self):
        """Return temporary directory for creating 7z archives"""
        dirs = self._get_dirs()
        return dirs.get("tmp dir")

    def zip_prog(self):
        """Full path of 7-zip.exe"""
        dirs = self._get_dirs()
        return dirs.get("zip program")

    def rclone_prog(self):
        """Full path of rclone.exe"""
        dirs = self._get_dirs()
        return dirs.get("rclone program")

    def upload_method(self):
        """Upload method: False=move, True=rclone"""
        dirs = self._get_dirs()
        return (dirs.get("upload") or "") == "rclone"


config = ZipConfig(CONFIG)



def time_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def date_minus12h():
    return (datetime.datetime.now() - datetime.timedelta(hours=12)).strftime("%Y-%m-%d")

def date_subdir(date=None):
    if not date:
        date = date_minus12h()
    return datetime.date.fromisoformat(date).strftime(config.zip_sub())



# options
class Options:
    no_action = False                       # -n --no_action
    datadir   = config.data_dir()
    zipdir    = config.zip_dir()
    tmpdir    = config.tmp_dir()
    zipprog   = config.zip_prog()
    rcloneprog= config.rclone_prog()
    upload    = config.upload_method()      # False=move, True=rclone
    zipmx     = 5                           # Compression, 0=none, 1=fastest, 3=fast, 5=normal, 7=max, 9=ultra
    run_ready = False
    run_last  = False
    timer     = TIMER
    date      = date_minus12h()
    subdir    = None                        # --subdir
    zipsub    = date_subdir()



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



def scan_data_dir_ready_mode(datadir, tmpdir, zipdir):
    ready = [f.replace(".ready", "") for f in os.listdir(datadir) if f.endswith(".ready")]
    # print(ready)
    ic(ready)

    for target in ready:
        ic(target)
        # verbose("Target ready:", target)
        arcname = target + ".7z"
        zipfile = os.path.join(tmpdir, arcname)
        if os.path.exists(zipfile):
            # verbose("  Zip file", zipfile, "already exists")
            pass
        elif check_upload(zipdir, arcname):
            # verbose(f"archive {arcname} already uploaded")
            pass
        else:
            verbose(f"target ready: {target}")
            msg = f"{time_now()} archiving target {target}"
            print(msg)
            print("=" * len(msg))
            verbose(f"zip file {zipfile}")
            create_zip_archive(target, datadir, zipfile)
            print("=" * len(msg))
            upload_zip_archive(zipfile, zipdir, arcname)
            print("=" * len(msg))



def scan_data_dir_last_mode(datadir, tmpdir, zipdir, date):
    # TARGET/YYYY-MM-DD directories
    dirs = [d for d in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, d, date))]
    ic(dirs)
    if dirs:
        scan_targets(datadir, tmpdir, zipdir, dirs, date)
    # TARGET-YYYY-MM-DD directories
    dirs = [d.replace("-"+date, "").replace("_"+date, "") 
            for d in os.listdir(datadir) if d.endswith("-"+date) or d.endswith("_"+date)]
    ic(dirs)
    if dirs:
        scan_targets(datadir, tmpdir, zipdir, dirs, date)



def scan_targets(datadir, tmpdir, zipdir, targets, date):
    for target in targets:
        # Ignore targets / directories starting with "_"
        if target.startswith("_"):
            verbose(f"ignoring {target}")
            continue

        arcname = target + "-" + date + ".7z"
        verbose(f"target to archive: {target} -> {arcname}")
        zipfile  = os.path.join(tmpdir, arcname)
        if check_upload(zipdir, arcname):
            verbose(f"archive {arcname} already uploaded")
        else:
            # Archive already exists
            if os.path.exists(zipfile):
                verbose(f"file {zipfile} already exists, retrying upload")
                upload_zip_archive(zipfile, zipdir, arcname)

            # TARGET-YYYY-MM-DD/ directories
            elif os.path.isdir(os.path.join(datadir, target + "-" + date)):
                verbose(f"{time_now()} archiving {target}-{date}")
                create_zip_archive(target + "-" + date, datadir, zipfile)
                upload_zip_archive(zipfile, zipdir, arcname)
            # TARGET_YYYY-MM-DD/ directories
            elif os.path.isdir(os.path.join(datadir, target + "_" + date)):
                verbose(f"{time_now()} archiving {target}_{date}")
                create_zip_archive(target + "_" + date, datadir, zipfile)
                upload_zip_archive(zipfile, zipdir, arcname)
            # TARGET/YYYY-MM-DD/ directories
            elif os.path.isdir(os.path.join(datadir, target, date)):
                verbose(f"{time_now()} archiving {target}/{date}")
                create_zip_archive(os.path.join(target, date), datadir, zipfile)
                upload_zip_archive(zipfile, zipdir, arcname)
            # Unsupported
            else:
                warning(f"no supported directory structure for {target} {date} found!")            



def create_zip_archive(target, datadir, zipfile):
    # 7z.exe a -t7z -mx=7 -r -spf zipfile target
    #   a       add files to archive
    #   -t7z    set archive type to 7z
    #   -mx5    set compression level to maximum (0=none, 3=fast, 5=normal (default), 7=maximum, 9=ultra)
    #   -r      recurse subdirectories
    #   -spf    use fully qualified file paths
    args7z = [ Options.zipprog, "a", "-t7z", f"-mx{Options.zipmx}", "-r", "-spf", zipfile, target ]
    verbose("run", " ".join(args7z))
    if not Options.no_action:
        subprocess.run(args=args7z, shell=False, cwd=datadir, check=True)



def upload_zip_archive(zipfile, zipdir, arcname):
    verbose(f"upload to {zipdir} (+subdir)")
    if Options.upload:
        upload_rclone(zipfile, zipdir, arcname)
    else:
        upload_move(zipfile, zipdir)



def check_upload(zipdir, arcname):
    if Options.upload:          # rclone
        zipfile = upload_join(zipdir, arcname)
        if not Options.run_ready:
            verbose(f"check upload {zipfile}")
        return check_rclone_lsf(zipfile, arcname)
    else:
        zipfile = upload_join(zipdir, arcname, remote=False)
        if not Options.run_ready:
            verbose(f"check upload {zipfile}")
        return os.path.exists(zipfile)



def upload_move(zipfile, zipdir):
    (total, used, free) = shutil.disk_usage(zipdir)
    ic(total, used, free)
    verbose(f"free disk space {free/1024/1024/1024:.2f} GB")

    zipdir = upload_join(zipdir, remote=False)
    verbose(f"move {zipfile}")
    verbose(f"  -> {zipdir}")
    if not Options.no_action:
        os.makedirs(zipdir, exist_ok=True)
        shutil.move(zipfile, zipdir)



## rclone specific functions
def upload_rclone(zipfile, remote, arcname):
    """Move archive from tmp dir to remote storage, using rclone"""
    remote = upload_join(remote) + "/" + arcname
    # Use moveto to remove local archive after upload
    # args = [ Options.rcloneprog, "copy", zipfile, remote, "-v", "-P" ]
    args = [ Options.rcloneprog, "moveto", zipfile, remote, "-v", "-P" ]
    verbose("run", " ".join(args))
    if not Options.no_action:
        subprocess.run(args=args, shell=False, check=True)



def check_rclone_lsf(remote, arcname):
    """Check if archive exists on remote storage, using rclone lsf"""
    args = [ Options.rcloneprog, "lsf", remote ]
    if not Options.run_ready:
        verbose("run", " ".join(args))
    if not Options.no_action:
        r = subprocess.run(args=args, shell=False, check=True, capture_output=True, text=True)
        ic(r)
        file = r.stdout.strip()
        return file == arcname
    return False



def upload_join(zipdir, arcname="", remote=True):
    """Add ZIPSUB or SUBDIR to bucket dir"""

    ##FIXME: move to options handling
    # Build specialized dest path for --ready mode with --subdir
    if Options.run_ready and Options.subdir:
        # subdir = Options.subdir + "_" + Options.date
        # Upload to ZIPDIR/SUBDIR/ZIPSUB/SUBDIR_YYYY-MM-DD
        subdir = Options.subdir + "/" + Options.zipsub + "/" + Options.subdir+"_"+Options.date
    else:
        subdir = Options.zipsub

    if remote:
        zip = zipdir.replace("\\", "/") + "/" + subdir
        if arcname:
            zip += "/" + arcname
    else:
        subdir = subdir.replace("/", os.path.sep)
        zip = os.path.join(zipdir, subdir)
        if arcname:
            zip = os.path.join(zip, arcname)
    ic(subdir, zip)
    return zip



def run_ready():
    datadir = Options.datadir
    if Options.subdir:
        datadir = os.path.join(datadir, Options.subdir + "_" + Options.date)
    if not os.path.isdir(datadir):
        # If subdir doesn't exist, create it, NINA will create it only with the 1st frame
        warning(f"directory {datadir} doesn't exist, creating it")
        os.makedirs(datadir)
    
    verbose(f"scanning directory {datadir}")
    try:
        print("Waiting for ready data ... (Ctrl-C to interrupt)")
        while True:
            scan_data_dir_ready_mode(datadir, Options.tmpdir, Options.zipdir)
            # if verbose.enabled:
            #     print("Waiting ... ({:d}s, Ctrl-C to interrupt)".format(TIMER))
            time.sleep(Options.timer)
    except KeyboardInterrupt:
        print("Terminating ...")



def run_last(targetlist=None):
    datadir = Options.datadir
    if Options.subdir:
        datadir = os.path.join(datadir, Options.subdir)
    verbose(f"scanning directory {datadir}")

    if targetlist:
        targets = targetlist.split(",")
        scan_targets(datadir, Options.tmpdir, Options.zipdir, targets, Options.date)
    else:
        scan_data_dir_last_mode(datadir, Options.tmpdir, Options.zipdir, Options.date)



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = DESCRIPTION,
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-action", action="store_true", help="dry run")
    arg.add_argument("-l", "--low-priority", action="store_true", help="set process priority to low")

    arg.add_argument("--ready", action="store_true", help="run in TARGET.ready mode")
    arg.add_argument("--last", action="store_true", help=f"run in last night mode ({Options.date})")
    arg.add_argument("--date", help="run in archive data from DATE mode")

    arg.add_argument("--subdir", help="search SUBDIR_YYYY-MM-DD in data dir for ready targets (--ready)")
    arg.add_argument("--targets", help="archive TARGET[,TARGET] only (--last / --date)")
    arg.add_argument("--hostname", help=f"load settings for HOSTNAME (default {ZipConfig.hostname})")
    arg.add_argument("-t", "--time-interval", type=int, help=f"time interval for checking data directory (default {TIMER}s)")
    arg.add_argument("-m", "--mx", type=int, help=f"7-Zip compression setting -mx (default {Options.zipmx}), 0=none, 1=fastest, 3=fast, 5=normal, 7=max, 9=ultra")
    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
        config.info()
    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path)

    Options.no_action = args.no_action

    if args.hostname:
        ZipConfig.hostname = args.hostname
        # Re-initialize Options
        Options.datadir   = config.data_dir()
        Options.zipdir    = config.zip_dir()
        Options.zipsub    = date_subdir(Options.date)
        Options.tmpdir    = config.tmp_dir()
        Options.zipprog   = config.zip_prog()
        Options.rcloneprog= config.rclone_prog()
        Options.upload    = config.upload_method()

    if args.mx:
        Options.zipmx   = args.mx
    if args.time_interval:
        Options.timer   = args.time_interval
    if args.date:
        Options.date      = args.date
        Options.zipsub    = date_subdir(args.date)
        Options.run_last  = True
        Options.run_ready = False
    if args.subdir:
        Options.subdir    = args.subdir
        Options.run_last  = False
        Options.run_ready = True
    if args.ready:
        Options.run_ready = True
        Options.run_last  = False
    if args.last:
        Options.run_ready = False
        Options.run_last  = True

    Options.datadir = os.path.abspath(Options.datadir)
    Options.tmpdir  = os.path.abspath(Options.tmpdir)
    if not Options.upload:
        Options.zipdir  = os.path.abspath(Options.zipdir)
    Options.zipprog = os.path.abspath(Options.zipprog)
    Options.rcloneprog = os.path.abspath(Options.rcloneprog)

    verbose(f"Data directory = {Options.datadir}")
    verbose(f"Dest directory = {Options.zipdir}")
    verbose(f"Dest subdir    = {Options.zipsub}")
    verbose(f"Tmp directory  = {Options.tmpdir}")
    verbose(f"7z program     = {Options.zipprog}")
    verbose(f"rclone program = {Options.rcloneprog}")
    verbose(f"Use rclone     = {Options.upload}")
    verbose(f"Date minus 12h = {Options.date}")
    verbose(f"Subdir         = {Options.subdir}")

    # Set process priority
    if args.low_priority:
        set_priority()

    if Options.run_ready:
        # --ready mode
        run_ready()
    elif Options.run_last:
        # --last / --date mode
        run_last(args.targets)
    else:
        error("must specify mode, one of --ready / --last / --date")



if __name__ == "__main__":
    main()
