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
# Version 0.1 / 2024-07-29
#       Module for parsing ra/dec coordinates in various format, not depending on astropy

import argparse
import re

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error


VERSION = "0.1 / 2024-07-29"
AUTHOR  = "Martin Junius"
NAME    = "radec"



class Coord:
    """ Simple coordinate class for storing RA/DEC """

    def __init__(self, ra=None, dec=None):
        if ra and dec:
            ic(ra, dec)
            self.parse_ra_dec(ra, dec)


    def parse_ra_dec(self, ra, dec):
        (self.ra,  self.ra_h,  self.ra_m,  self.ra_s)  = self._parse_string(ra,  type="RA")
        (self.dec, self.dec_d, self.dec_m, self.dec_s) = self._parse_string(dec, type="DEC")
        ic(self.ra, self.ra_h, self.ra_m, self.ra_s, self.dec, self.dec_d, self.dec_m, self.dec_s)


    def _decimal_from_dms(self, d, m, s):
        return d + m/60 + s/3600 if d >= 0 else d - m/60 - s/3600
    
    def _decimal_to_dms(self, v):
        sign = -1 if v < 0 else +1
        va   = abs(v)
        d = int(va)
        m = int((va - d) * 60)
        s = float((va - d - m/60) * 3600)
        return (d*sign, m, s)


    def _parse_string(self, s, type=""):
        # Convert float() &c. to string
        s = str(s)

        if type == "DEC":
            # +/- only allowed in DEC
            regex1 = r'^([+-]?)([0-9]{1,2})[ :d]([0-9]{1,2})[ :m]([0-9.]+)s?$'
            regex2 = r'^([+-]?[0-9]+\.?[0-9]*)$'
        else:
            regex1 = r'^()([0-9]{1,2})[ :h]([0-9]{1,2})[ :m]([0-9.]+)s?$'
            regex2 = r'^([0-9]+\.?[0-9]*)$'
        ic(regex1, regex2)

        m = re.match(regex1, s)
        if m:
            ic(m.groups())
            m1 = int(m.group(1)+ m.group(2))
            m2 = int(m.group(3))
            m3 = float(m.group(4))
            md = self._decimal_from_dms(m1, m2, m3)
            if (type == "RA" and md < 24 and m2 < 60 and m3 < 60 or
                type == "DEC" and md >= -90 and md <= +90 and m2 < 60 and m3 < 60):
                return (md, m1, m2, m3)

        m = re.match(regex2, s)
        if m:
            ic(m.groups())
            md = float(m.group(1))
            (m1, m2, m3) = self._decimal_to_dms(md)
            if (type == "RA" and md < 24 or
                type == "DEC" and md >= -90 and md <= +90):
                return (md, m1, m2, m3)

        raise ValueError(f"illegal {type} coordinate {s}")


    def to_string(self, format="hmsdms"):
        if format == "decimal":
            return f"{self.ra:.7f} {self.dec:.7f}"
        elif format == " ":
            return f"{self.ra_h:02d} {self.ra_m:02d} {self.ra_s:06.3f} {self.dec_d:+02d} {self.dec_m:02d} {self.dec_s:06.3f}"
        elif format == "mpc":
            return f"{self.ra_h:02d} {self.ra_m:02d} {self.ra_s:06.3f}{self.dec_d:+02d} {self.dec_m:02d} {self.dec_s:05.2f}"
        elif format == "mpc1":
            return f"{self.ra_h:02d} {self.ra_m:02d} {self.ra_s:05.2f} {self.dec_d:+02d} {self.dec_m:02d} {self.dec_s:04.1f} "
        else:
            return f"{self.ra_h:02d}h{self.ra_m:02d}m{self.ra_s:06.3f}s {self.dec_d:+02d}d{self.dec_m:02d}m{self.dec_s:06.3f}s"


    def __repr__(self):
        return self.to_string()



### Test run as a command line script ###
def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "RA/DEC parser",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("ra", help="ra")
    arg.add_argument("dec", help="dec")

    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()

    print(f"{args.ra=} {args.dec=}")
    coord1 = Coord(args.ra, args.dec)
    print(f"{coord1 = }\n{coord1.to_string(format="decimal") = }")
    print("Regression with coord1 decimal values ...")
    coord2 = Coord(coord1.ra, coord1.dec)
    print(f"{coord2 = }")
    print(f"{coord2.to_string(format="hmsdms")  = }")
    print(f"{coord2.to_string(format="decimal") = }")
    print(f"{coord2.to_string(format=" ")       = }")
    print(f"{coord2.to_string(format="mpc")     = }")
    print(f"{coord2.to_string(format="mpc1")    = }")

    

if __name__ == "__main__":
    main()
