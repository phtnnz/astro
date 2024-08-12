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
# Version 0.0 / 2024-08-12
#       New N.I.N.A Autofocus result analyzer script

import sys
import argparse

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error

VERSION = "0.0 / 2024-08-12"
AUTHOR  = "Martin Junius"
NAME    = "nina-af-analyzer"



# Command line options
class Options:
    name = "abc"        # -n --name
    int  = 99           # -i --int



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "N.I.N.A Autofocus results analyzer",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-m", "--match", help="process files matching profile code MATCH")
    arg.add_argument("dirname", nargs="+", help="directory name (default: LOCALAPPDATA)")
    # nargs="+" for min 1 filename argument

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path, args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    # ... more options ...
    if args.match:
        pass
        # ...
        
    # ... the action starts here ...



if __name__ == "__main__":
    main()