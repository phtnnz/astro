#!/usr/bin/python

# ChangeLog
# Version 0.0 / 2023-07-01
#       Test script

import sys
import os
import argparse

global VERSION, AUTHOR
VERSION = "0.0 / 2023-07-01"
AUTHOR  = "Martin Junius"



def main():
    arg = argparse.ArgumentParser(
        prog        = "test",
        description = "Test python script",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-e", "--exit-code", type=int, help="return exit code, default 0")

    args = arg.parse_args()

    exit_code = args.exit_code if args.exit_code else 0
    print("test: exit code", exit_code)
    sys.exit(args.exit_code)


if __name__ == "__main__":
    main()
