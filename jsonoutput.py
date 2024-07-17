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

# Usage
#   from jsonoutput import JSONOutput
#   JSONOutput.add_obj(list)
#   JSONOutput.write(file=None)       file=None uses stdout

# ChangeLog
# Version 0.1 / 2024-07-15
#       Global JSON output class


import json
import sys

VERSION = "0.1 / 2024-07-15"
AUTHOR  = "Martin Junius"
NAME    = "jsonoutput"


class JSONOutput:
    _cache = []


    def add_obj(obj):
        JSONOutput._cache.append(obj)


    def _write(f):
        json.dump(JSONOutput._cache, f, indent = 4)


    def write(file=None):
        if file:
            with open(file, 'w', newline='', encoding="utf-8") as f:
                JSONOutput._write(f)
        else:
                JSONOutput._write(sys.stdout)
