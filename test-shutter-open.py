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
# Version 0.1 / 2023-06-26
#       First version, test shutter status with Hakos API
# Version 0.2 / 2023-07-01
#       Updated help text
# Version 0.3 / 2023-07-03
#       Commented debug messages

import os
import sys
import argparse
import json
# The following libs must be installed with pip
import requests

global VERSION, AUTHOR
VERSION = "0.3 / 2023-07-03"
AUTHOR  = "Martin Junius"

global CONFIG
CONFIG = "astro-python/hakosroof.json"




class Config:
    """JSON Config"""

    verbose  = False        # -v


    def __init__(self, file=None):
        self.obj = None
        self.file = file


    def read_json(self, file=None):
        file = self.file if not file else file
        with open(file, 'r') as f:
            data = json.load(f)
        self.obj = data


    def write_json(self, file=None):
        file = self.file if not file else file
        with open(file, 'w') as f:
            json.dump(self.obj, f, indent = 2)


    def url(self):
        return self.obj["url"]

    def apikey(self):
        return self.obj["apikey"]




def main():
    arg = argparse.ArgumentParser(
        prog        = "test-shutter-open",
        description = "Test Hakos shutter (roof) status: returns exit code 0, if open, else 1",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")

    args = arg.parse_args()

    Config.verbose = args.verbose

    appdata = os.environ.get('APPDATA')
    if not appdata:
        print(arg.prog, "environment APPDATA not set!")
        sys.exit(1)
    
    appdata = appdata.replace("\\", "/")
    # print(arg.prog+":", "appdata =", appdata)
    config = appdata + "/" + CONFIG
    # print(arg.prog+":", "config =", config)

    cf = Config(config)
    cf.read_json()
    # print(cf.obj)

    url = cf.url() + "/remobs?action=status&key={}".format(cf.apikey())
    # print(url)
    response = requests.get(url)
    print(response)
    status = response.json()
    print(status)

    status_open = False
    if "stext" in status:
        stext = status["stext"]
        print("stext =", stext)
        status_open = stext == "open"
    
    # exit code 0 == OK, if shutter status is "open"
    sys.exit(0 if status_open else 1)




if __name__ == "__main__":
    main()
