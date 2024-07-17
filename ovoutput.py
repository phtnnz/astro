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

# Usage
#       from ovoutput import OverviewOutput
#       OverviewOutput.add(key1, key2, text)
#       OverviewOutput.print(file=stdout)

# ChangeLog
# Version 0.1 / 2024-07-15
#       New module for overview output

import re
import sys

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error


VERSION = "0.1 / 2024-07-15"
AUTHOR  = "Martin Junius"
NAME    = "ovoutput"



# Adapted from https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(*args):
    # This one is a bit tricky when using sorted() with dict.items()
    text, val = args[0]
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


class OverviewOutput:
    """ Sorted overview list for two nested keys: key1 > key2 > text """
    _cache = {}
    _text1 = "Key 1"
    _text2 = "Key 2"

    def set_description1(desc):
        OverviewOutput._text1 = desc

    def set_description2(desc):
        OverviewOutput._text2 = desc


    def add(key1, key2, text):
        if not key1 in OverviewOutput._cache:
            OverviewOutput._cache[key1] = {}
        dict2 = OverviewOutput._cache[key1]
        if not key2 in dict2:
            dict2[key2] = []
        dict2[key2].append(text)


    def print(file=sys.stdout):
        key1_count = 0
        key2_count = 0
        text_count = 0

        for key1, dict2 in sorted(OverviewOutput._cache.items(), key=natural_keys):
            print(key1, file=file)
            key1_count += 1

            for key2, list in sorted(dict2.items(), key=natural_keys):
                print("   ", key2, file=file)
                key2_count += 1
                text_count += len(list)

                for text in list:
                    print("       ", text, file=file)

        print(f"{OverviewOutput._text1} {key1_count}", file=file)
        print(f"{OverviewOutput._text2} {text_count}", file=file)
