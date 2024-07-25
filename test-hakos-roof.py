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

# ChangeLog
# Version 1.0 / 2024-06-20
#       Refactored version of test-shutter-open.py
# Version 1.1 / 2024-07-17
#       Added -U --unparked option

import sys
import argparse
# The following libs must be installed with pip
import requests
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose          import verbose, warning, error
from jsonconfig       import JSONConfig, config

NAME    = "test-hakos-roof"
VERSION = "1.1 / 2024-07-17"
AUTHOR  = "Martin Junius"

CONFIG = "hakosroof.json"



class RoofConfig(JSONConfig):
    """ JSON Config for Hakos roof API """

    def __init__(self, file=None):
        super().__init__(file)

    def url(self):
        return self.config["url"]

    def apikey(self):
        return self.config["apikey"]




def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test Hakos roof (shutter) status: returns exit code 0, if ok (open/parked/unparked), else 1",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-P", "--parked", action="store_true", help="test for \"parked\" status")
    arg.add_argument("-U", "--unparked", action="store_true", help="test for \"unparked\" status")
    arg.add_argument("-O", "--open", action="store_true", help="test for \"open\" status (default)")

    args = arg.parse_args()

    verbose.set_prog(NAME)
    verbose.enable(args.verbose)
    if args.debug:
        ic.enable()

    cf = RoofConfig(CONFIG)

    url = cf.url() + "/remobs?action=status&key={}".format(cf.apikey())
    ic(url)
    response = requests.get(url)
    ic(response)
    status = response.json()
    ic(status)

    status_open = False
    if "stext" in status:
        stext = status["stext"]
        status_open = stext == "open"
        ic(stext, status_open)
        verbose(f"status open={status_open}")

    status_parked = False
    # 'stat': 'i,152,512,776,319,774,1,0,0,1' -- last number is 0=parked, 1=not parked
    #          0 1   2   3   4   5   6 7 8 9
    if "stat" in status:
        stat = status["stat"]
        list = stat.split(",")
        status_parked = int(list[9]) == 0
        ic(stat, status_parked)
        verbose(f"status parked={status_parked}")

    if "pos" in status:
        pos = status["pos"]
        ic(pos)
        verbose(f"pos={pos}")

    if not args.parked and not args.open:
        args.open = True

    # exit code 1 == ERROR
    exit_code = 1
    if args.open:
        # exit code 0 == OK, if shutter status is "open"
        if status_open:
            exit_code = 0
    if args.parked:
        # exit code 0 == OK, if telescope status is "parked"
        if status_parked:
            exit_code = 0
    if args.unparked:
        # exit code 0 == OK, if telescope status is "unparked"
        if not status_parked:
            exit_code = 0
    
    verbose(f'exit={exit_code} ({"not " if exit_code else ""}ok)')
    sys.exit(exit_code)



if __name__ == "__main__":
    main()
