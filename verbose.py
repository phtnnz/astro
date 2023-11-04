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
# Version 0.1 / 2023-11-04
#       First version of verbose module
#       Usage:  from verbose import verbose
#               verbose(print-like-args)
#               verbose.enable()
#               verbose.disabled()
#               verbose.set_name(name)

import argparse
# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()


global VERSION, AUTHOR, NAME
VERSION = "0.0 / 2023-11-04"
AUTHOR  = "Martin Junius"
NAME    = "verbose"



class Verbose:

    def __init__(self):
        self.enabled = False
        self.progname = None

    def __call__(self, *args):
        if not self.enabled:
            return
        ic("Verbose.__call__", args)
        if self.progname:
            print(self.progname + ": ", end="")
        print(*args)

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def set_prog(self, name):
        self.progname = name


verbose = Verbose()



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test script for verbose module",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")

    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()

    ic(args)
    verbose("Test", "1", "for", "verbose()")
    verbose("Test", "2", "for more", "verbose()", "with some formatting {:04d}".format(11+12))

    



if __name__ == "__main__":
    main()
