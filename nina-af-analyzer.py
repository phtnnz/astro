#!/usr/bin/env python

# Copyright 2024 Martin Junius
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

# ChangeLog
# Version 0.1 / 2024-08-12
#       New N.I.N.A Autofocus result analyzer script

import sys
import argparse
import os
import json
from datetime import datetime

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error
from csvoutput import CSVOutput

VERSION = "0.1 / 2024-08-12"
AUTHOR  = "Martin Junius"
NAME    = "nina-af-analyzer"



# Command line options
class Options:
    """Command line options"""
    csv: bool = False       # -C --csv
    output: str = None      # -o --output



class AFJSON:
    """NINA JSON AutoFocus results"""

    def __init__(self, file: str):
        self.obj = self.read_json(file)

    def read_json(self, file: str):
        with open(file, 'r') as f:
            return json.load(f)

    def get(self, key):
        return self.obj.get(key)

    def get_keys(self):
        return self.obj.keys()

    def get_datetime(self):
        ts = self.get("Timestamp")
        return datetime.fromisoformat(ts)

    def get_position(self):
        focus_point = self.get("CalculatedFocusPoint")
        return focus_point.get("Position")
    
    def get_hfr(self):
        focus_point = self.get("CalculatedFocusPoint")
        return focus_point.get("Value")



def get_nina_appdata():
    appdata = os.environ.get('LOCALAPPDATA')
    if appdata:
        path = os.path.join(appdata, "NINA", "AutoFocus")
        ic(appdata, path)
        if os.path.isdir(path):
            return path
        else:
            error(f"no such directory {path}")
    else:
        error("environment LOCALAPPDATA not set!")



def process_dir(dir: str, match: str):
    verbose(f"processing directory {dir}")
    if not match:
        match = ""
    verbose(f"processing directory {dir}, AF results matching {match}")
    files = [f for f in os.listdir(dir) if f.endswith(".json") and match in f]

    for file1 in files:
        file = os.path.join(dir, file1)
        if os.path.exists(file):
            process_file(file)



def process_file(file: str):
    # verbose(f"processing file {file}")
    af = AFJSON(file)
    ic(af.get_keys())
    
    dt  = af.get_datetime().strftime("%Y-%m-%d %H:%M:%S")
    pos = af.get_position()
    hfr = af.get_hfr()
    ic(dt, pos, hfr)
    if Options.csv:
        CSVOutput.add_row([dt, int(pos), hfr])
    else:
        verbose(f"{dt}: {pos=:.0f} {hfr=:.2f}")




def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "N.I.N.A Autofocus results analyzer",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-m", "--match", help="process files matching profile code MATCH")
    arg.add_argument("-o", "--output", help="write CSV to OUTPUT file")
    arg.add_argument("-C", "--csv", action="store_true", help="use CSV output format")

    arg.add_argument("dirname", nargs="*", help="directory name (default: LOCALAPPDATA)")

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path, args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    # ... more options ...
    Options.csv = args.csv
    Options.output = args.output
        
    # ... the action starts here ...
    if Options.csv:
        CSVOutput.add_fields(["Date Time", "Positiion", "HFR"])
    if args.dirname:
        for dir in args.dirname:
            process_dir(dir, args.match)
    else:
        dir = get_nina_appdata()
        process_dir(dir, args.match)
    if Options.csv:
        CSVOutput.write(Options.output)



if __name__ == "__main__":
    main()