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
# Version 0.0 / 2024-03-24
#       MPC module to retrieve PDF from MPC/MPO/MPS archive

# Web page for MPC archive:
# https://www.minorplanetcenter.net/iau/ECS/MPCArchive/MPCArchive.html
#
# Format
#   [...]
#   <h2>MPC/MPO/MPS Archive</h2>
#   [...]
#   <h2>2024</h2>
#   <ul>
#   <li>2024/03/15
#   <ul>
#   <li><a href="/iau/ECS/MPCArchive/2024/MPS_20240315.pdf"><i>MPS</i> 2145921-2152456</a>
#   </ul>
#   <li>2024/02/29
#   <ul>
#   <li><a href="/iau/ECS/MPCArchive/2024/MPS_20240229.pdf"><i>MPS</i> 2115867-2145920</a>
#   </ul>
#   [...]

import argparse
import re

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error


global VERSION, AUTHOR, NAME
VERSION = "0.0 / 2024-03-24"
AUTHOR  = "Martin Junius"
NAME    = "mpcosarchive"






### Test run as a command line script ###
def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Retrieve PDF from MPC/MPO/MPS archive",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("pub", nargs="+", help="publication id")

    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()



if __name__ == "__main__":
    main()