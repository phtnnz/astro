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
#   <!-- Body postamble -->

import argparse
import re
import requests

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error


VERSION = "0.0 / 2024-03-24"
AUTHOR  = "Martin Junius"
NAME    = "mpcosarchive"

ARCHIVE_URL = "https://www.minorplanetcenter.net/iau/ECS/MPCArchive/MPCArchive.html"



class MPCOSArchive:
    """ MPC/MPO/MPS archive processing """

    def __init__(self, url = ARCHIVE_URL):
        ic(url)
        self.pub_dict = {}
        self.url_get(url)


    def url_get(self, url = ARCHIVE_URL):
        verbose(f"get {url}")
        m = re.search('^(https+://[A-Za-z0-9_\-.]+)/', url)
        if not m:
            raise ValueError
        self.url = url
        self.server = m.group(1)
        r = requests.get(url)
        ic(r)
        r.raise_for_status()
        self._parse_text(r.text)
        # print(self.pub_dict)


    def search_pub(self, pub):
        verbose(f"search for {pub}")
        m = re.search('([A-Z]+) *(\d+)$', pub)
        if not m:
            raise ValueError
        mpx = m.group(1)
        n   = int(m.group(2))
        ic(mpx, n)
        return self._search_dict(mpx, n)
    

    def _search_dict(self, mpx, n):
        list = self.pub_dict[mpx]
        ##FIXME: more efficient search, list is already sorted, descending
        for item in list:
            lo = item["lo"]
            hi = item["hi"]
            if n >= lo and n <= hi:
                return item


    def _parse_text(self, text):
        in_arc_list = False
        year = "0000"
        date = "0000/00/00"
        for line in text.splitlines():
            m = re.search('^<!-- Main content block -->$', line)
            if m:
                in_arc_list = True
            m = re.search('^<!-- Body postamble -->$', line)
            if m:
                in_arc_list = False

            if in_arc_list:
                # ic(line)
                m = re.search('^<h2>(\d\d\d\d)</h2>$', line)
                if m:
                    year = m.group(1)
                m = re.search('^<li>(\d\d\d\d/\d\d/\d\d)$', line)
                if m:
                    date = m.group(1).replace("/", "-")
                m = re.search('<li><a href="(/iau/.+\.pdf)"><i>([A-Z]+)</i> *(\d+) *- *(\d+)</a>', line)
                if m:
                    pdf = self.server + m.group(1)
                    mpx = m.group(2)
                    lo  = m.group(3)
                    hi  = m.group(4)
                    self._add_pub(mpx, lo, hi, pdf, year, date)
                m = re.search('<li><i>([A-Z]+)</i> *(\d+) *- *(\d+)', line)
                if m:
                    pdf = None
                    mpx = m.group(1)
                    lo  = m.group(2)
                    hi  = m.group(3)
                    self._add_pub(mpx, lo, hi, pdf, year, date)


    def _add_pub(self, mpx, lo, hi, pdf, year, date):
        ic(mpx, lo, hi, pdf, year, date)
        if not mpx in self.pub_dict:
            self.pub_dict[mpx] = []
        list = self.pub_dict[mpx]
        list.append({"lo": int(lo), "hi": int(hi), "pdf": pdf, "year": year, "date": date})

                


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


    arc = MPCOSArchive()

    for arg in args.pub:
        r = arc.search_pub(arg)
        print(r)



if __name__ == "__main__":
    main()