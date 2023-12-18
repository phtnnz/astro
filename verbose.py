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
#               verbose.disable()
#               verbose.set_prog(name)
# Version 0.2 / 2023-12-18
#       Added warning(), error() with abort
#       Usage:  from verbose import verbose, warning, error, set_program_name
#               warning(print-like-args)
#               error(print-like-args)

import argparse
import sys

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()


global VERSION, AUTHOR, NAME
VERSION = "0.1 / 2023-11-04"
AUTHOR  = "Martin Junius"
NAME    = "verbose"



class Verbose:

    def __init__(self, flag=False, prefix=None, abort=False):
        self.enabled = flag
        self.progname = None
        self.prefix = prefix
        self.abort = abort
        self.errno = 1          # exit(1) for generic errors

    def __call__(self, *args):
        if not self.enabled:
            return
        if self.progname:
            print(self.progname + ": ", end="")
        if self.prefix:
            print(self.prefix + ": ", end="")
        print(*args)
        if self.abort:
            self.exit()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def set_prog(self, name):
        self.progname = name

    def set_errno(self, errno):
        self.errno = errno

    def exit(self):
        if self.progname:
            print(self.progname + ": ", end="")
        print(f"exiting ({self.errno})")
        sys.exit(self.errno)


verbose = Verbose()
warning = Verbose(True, "WARNING")
error   = Verbose(True, "ERROR", True)

def set_program_name(name):
    verbose.set_prog(name)
    warning.set_prog(name)
    error.set_prog(name)



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test script for verbose module",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")

    args = arg.parse_args()

    set_program_name(NAME)
    if args.verbose:
        verbose.enable()
    if args.debug:
        ic.enable()

    ic(args)
    verbose("Test", "1", "for", "verbose()")
    verbose("Test", "2", "for more", "verbose()", "with some formatting {:04d}".format(11+12))
    warning("A", "warning", "messages", " --- but no abort here!")
    error.set_errno(99)
    error("Error test", "for Verbose module")

    



if __name__ == "__main__":
    main()
