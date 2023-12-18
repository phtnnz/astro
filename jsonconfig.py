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
# Version 0.1 / 2023-12-18
#       First version of JSONConfig module
#       Usage:  from jsonconfig import JSONConfig
#               class MyConfig(JSONConfig)

import sys
import os
import errno
import argparse
import json

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()


global VERSION, AUTHOR, NAME
VERSION = "0.1 / 2023-12-18"
AUTHOR  = "Martin Junius"
NAME    = "JSONConfig"


global CONFIGDIR, CONFIGFILE
CONFIGDIR = "astro-python"
CONFIGFILE = "astro-python-config.json"

class JSCONConfig:
    """ JSONConfig base class """

    def __init__(self, file=None):
        self.obj    = None                      # JSON object
        self.config = self.search_config(file)  # Config file, full path
        self.read_json()


    def search_config(self, file=None):
        # Default
        file = file if file else CONFIGFILE

        # Search config file in current directory, LOCALAPPDATA, APPDATA
        searchpath = []

        path = os.path.curdir
        if os.path.isdir(path):
            searchpath.append(path)

        path = os.path.join(os.path.curdir, CONFIGDIR)
        if os.path.isdir(path):
            searchpath.append(path)

        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            id("environment LOCALAPPDATA not set!")
        path = os.path.join(appdata, CONFIGDIR)
        if os.path.isdir(path):
            searchpath.append(path)

        appdata = os.environ.get('APPDATA')
        if not appdata:
            id("environment APPDATA not set!")
        path = os.path.join(appdata, CONFIGDIR)
        if os.path.isdir(path):
            searchpath.append(path)

        for path in searchpath:
            ic(path)
            file1 = os.path.join(path, file)
            if os.path.isfile(file1):
                ic(file1)
                return file1

        ic("ERROR exit")    
        sys.exit(errno.ENOENT)


    def read_json(self, file=None):
        file = file if file else self.config
        with open(file, 'r') as f:
            self.obj = json.load(f)


    def write_json(self, file=None):
        file = file if file else self.config
        with open(file, 'w') as f:
            json.dump(self.obj, f, indent = 2)


    def get_json(self):
        return self.obj



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test for module",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")

    args = arg.parse_args()

    if args.debug:
        ic.enable()

    config = JSCONConfig()
    print("JSON Config =", json.dumps(config.get_json(), indent=4))


if __name__ == "__main__":
    main()
