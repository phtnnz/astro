#!/usr/bin/env python

# Copyright 2023-2026 Martin Junius
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
# Version 1.2 / 2024-12-20
#       Added test for locked status, new options -C / --closed, -L / --locked,
#       --unlocked, -D / --discord, send error messages via Discord
# Version 1.3 / 2026-03-17
#       Use new jsonconfig module, added --startup option

NAME    = "test-hakos-roof"
VERSION = "1.3 / 2026-03-17"
AUTHOR  = "Martin Junius"

import sys
import argparse
# The following libs must be installed with pip
import requests
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose    import verbose, warning, error
from jsonconfig import JSONConfig, config
from discordmsg import discord_message

CONFIG  = "hakosroof.json"
TIMEOUT = 20                # seconds timeout for requests.get()



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test Hakos roof (shutter) status: returns exit code 0, if test ok, else 1",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-P", "--parked", action="store_true", help="test for \"parked\" status")
    arg.add_argument("-U", "--unparked", action="store_true", help="test for \"unparked\" status")
    arg.add_argument("-O", "--open", action="store_true", help="test for \"open\" status (default)")
    arg.add_argument("-C", "--closed", action="store_true", help="test for \"closed\" status")
    arg.add_argument("-L", "--locked", action="store_true", help="test for \"locked\" status")
    arg.add_argument("--unlocked", action="store_true", help="test for \"unlocked\" status")
    arg.add_argument("--startup", action="store_true", help="test for safe startup status (unlocked, parked)")
    arg.add_argument("-D", "--discord", action="store_true", help="send status message to Discord")

    args = arg.parse_args()

    verbose.set_prog(NAME)
    verbose.enable(args.verbose)
    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path, args)

    cf = JSONConfig(CONFIG)

    url = f"{cf.url}/remobs?action=status&key={cf.apikey}"
    ic(url)

    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        ic(e)
        error(f"{e.args[0]}")

    ic(response)
    status = response.json()
    ic(status)

    status_locked = False
    # status: {'lock': True, ...
    if "lock" in status:
        status_locked = status["lock"]
        ic(status_locked)
        verbose(f"status locked={status_locked}")

    status_open = False
    # stext values: "open", "closed", "closing", "opening", "error"
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

    # exit code 1 == ERROR
    exit_code = 1
    if args.parked:
        # exit code 0 == OK, if telescope status is "parked"
        if status_parked:
            exit_code = 0
    elif args.unparked:
        # exit code 0 == OK, if telescope status is "unparked"
        if not status_parked:
            exit_code = 0
    elif args.locked:
        # exit code 0 = OK, if roofs are "locked"
        if status_locked:
            exit_code = 0
    elif args.unlocked:
        # exit code 0 = OK, if roofs are "unlocked"
        if not status_locked:
            exit_code = 0
        elif args.discord:
            discord_message("Hakos roofs are locked!")
    elif args.startup:
        # exit code 0 = OK, if "unlocked" and "parked"
        if not status_locked and status_parked:
            exit_code = 0
    elif args.closed:
        # exit code 0 = OK, if shutter status is "closed"
        if not status_open:
            exit_code = 0
    else: # default, --open
        # exit code 0 == OK, if shutter status is "open"
        if status_open:
            exit_code = 0
    
    verbose(f'exit={exit_code} ({"not " if exit_code else ""}ok)')
    if exit_code and args.discord:
        discord_message(f"Hakos roof: status \"open={status_open}, parked={status_parked}, locked={status_locked}\" not expected, terminating sequence")
    sys.exit(exit_code)



if __name__ == "__main__":
    main()
