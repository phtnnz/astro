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
# Version 0.2 / 2024-01-23
#       Rewritten for multiple config files, global config object
#
#       Usage:  from jsonconfig import config
#               from jsonconfig import JSONConfig
#               class MyConfig(JSONConfig)
# Version 0.3 / 2024-06-19
#       Search also in .config

import os
import argparse
import json

# The following libs must be installed with pip
from icecream import ic
# Disable debugging

# Local modules
from verbose import verbose



VERSION = "0.3 / 2024-06-19"
AUTHOR  = "Martin Junius"
NAME    = "JSONConfig"


CONFIG     = ".config"
CONFIGDIR  = "astro-python"
CONFIGFILE = "astro-python-config.json"

#ic.enable()
ic(CONFIGDIR, CONFIGFILE)

class JSONConfig:
    """ JSONConfig base class """

    def __init__(self, file):
        ic("config init", file)
        self.config = {}
        self.read_config(file)


    def read_config(self, file):
        ic(file)
        file1 = self.search_config(file)
        if(file1):
            json  = self.read_json(file1)
            # Merge with existing config
            self.config = self.config | json


    def search_config(self, file):
        # If full path use as is
        if os.path.isfile(file):
            return file
        
        # Search config file in current directory, LOCALAPPDATA, APPDATA
        searchpath = []

        path = os.path.curdir
        if os.path.isdir(path):
            searchpath.append(path)

        path = os.path.join(os.path.curdir, CONFIG)
        if os.path.isdir(path):
            searchpath.append(path)

        path = os.path.join(os.path.curdir, CONFIGDIR)
        if os.path.isdir(path):
            searchpath.append(path)

        path = os.path.join(os.path.curdir, CONFIG, CONFIGDIR)
        if os.path.isdir(path):
            searchpath.append(path)

        appdata = os.environ.get('LOCALAPPDATA')
        if appdata:
            path = os.path.join(appdata, CONFIGDIR)
            if os.path.isdir(path):
                searchpath.append(path)
        else:
            ic("environment LOCALAPPDATA not set!")

        appdata = os.environ.get('APPDATA')
        if appdata:
            path = os.path.join(appdata, CONFIGDIR)
            if os.path.isdir(path):
                searchpath.append(path)
        else:
            ic("environment APPDATA not set!")

        for path in searchpath:
            ic(path)
            file1 = os.path.join(path, file)
            if os.path.isfile(file1):
                ic(file1)
                return file1

        verbose(f'config file {file} not found')    
        return None


    def read_json(self, file):
        with open(file, 'r') as f:
            return json.load(f)


    def write_json(self, file):
        with open(file, 'w') as f:
            json.dump(self.config, f, indent = 2)


    def get(self, key):
        return self.config[key] if key in self.config else None


    def get_keys(self):
        return self.config.keys()


    def get_json(self):
        # For backwards compatibility
        return self.config



# Global config object
config = JSONConfig(CONFIGFILE)



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test for module",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-c", "--config", help="read CONFIG file")

    args = arg.parse_args()

    verbose.set_prog(NAME)
    if args.verbose:
        verbose.enable()
    if args.debug:
        ic.enable()
    if args.config:
        config.read_config(args.config)

    print("JSON config keys =", ", ".join(config.get_keys()))



if __name__ == "__main__":
    main()
