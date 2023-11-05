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

# Data formats:
#
# General documentation page
#   https://www.minorplanetcenter.net/iau/MPC_Documentation.html
#
# Packed Provisional and Permanent Designations
#   https://www.minorplanetcenter.net/iau/info/PackedDes.html
#
# Format For Optical Astrometric Observations Of Comets, Minor Planets and Natural Satellites
# (MPC1992 80-column format)
#   https://www.minorplanetcenter.net/iau/info/OpticalObs.html 
#
# Astrometry Data Exchange Standard
# (ADES)
#   https://minorplanetcenter.net/iau/info/IAU2015_ADES.pdf
#
# Catalog Codes
# (Column 72 of observation record in MPECs/WAMO responses)
#   https://www.minorplanetcenter.net/iau/info/CatalogueCodes.html
#
# Explanation of References on Astrometric Observations
# (Column 73-77 of observation record)
#   https://minorplanetcenter.net/iau/info/References.html
#
# See also this github repo
#   https://github.com/IAU-ADES/ADES-Master/tree/master/Python/bin
#
# Other descriptions
#   https://birtwhistle.org.uk/Docs/ADESAstrometryParser/ConversiontoMPC1992format.html


# ChangeLog
# Version 0.1 / 2023-1013
#       Moved Data80 class from mpc-retrieve-ack to here, renamed to MPCData80
#       Can be imported as a module or run as a command line script

import argparse
import re
import json
# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose


global VERSION, AUTHOR, NAME
VERSION = "0.1 / 2023-10-13"
AUTHOR  = "Martin Junius"
NAME    = "mpcdata80"


# MPC Catalog codes - column 72
# Char   Catalogue
mpc_catalog_codes = {
  "a": "USNO-A1.0",
  "b": "USNO-SA1.0",
  "c": "USNO-A2.0",
  "d": "USNO-SA2.0",
  "e": "UCAC-1",
  "f": "Tycho-1",
  "g": "Tycho-2",
  "h": "GSC-1.0",
  "i": "GSC-1.1",
  "j": "GSC-1.2",
  "k": "GSC-2.2",
  "l": "ACT",
  "m": "GSC-ACT",
  "n": "SDSS-DR8",
  "o": "USNO-B1.0",
  "p": "PPM",
  "q": "UCAC-4",
  "r": "UCAC-2",
  "s": "USNO-B2.0",
  "t": "PPMXL",
  "u": "UCAC-3",
  "v": "NOMAD",
  "w": "CMC-14",
  "x": "Hipparcos 2",
  "y": "Hipparcos",
  "z": "GSC (version unspecified)",
  "A": "AC",
  "B": "SAO 1984",
  "C": "SAO",
  "D": "AGK 3",
  "E": "FK4",
  "F": "ACRS",
  "G": "Lick Gaspra Catalogue",
  "H": "Ida93 Catalogue",
  "I": "Perth 70",
  "J": "COSMOS/UKST Southern Sky Catalogue",
  "K": "Yale",
  "L": "2MASS",
  "M": "GSC-2.3",
  "N": "SDSS-DR7",
  "O": "SST-RC1",
  "P": "MPOSC3",
  "Q": "CMC-15",
  "R": "SST-RC4",
  "S": "URAT-1",
  "T": "URAT-2",
  "U": "Gaia-DR1",
  "V": "Gaia-DR2",
  "W": "Gaia-DR3",
  "X": "Gaia-EDR3",
  "Y": "UCAC-5",
  "Z": "ATLAS-2",
  "0": "IHW",
  "1": "PS1-DR1",
  "2": "PS1-DR2",
  "3": "Gaia_Int  ",
  "4": "GZ",
  "5": "USNO-UBAD",
  "6": "Gaia2016",
}



class MPCData80:
    def __init__(self, data):
        self.data80 = data


    def get_col(self, col1, col2=0):
        if col2 > 0:
            return self.data80[col1 -1 : col2]
        else:
            return self.data80[col1 - 1]


    def parse_data(self):
        self.obj = {}
        self.obj["data"] = self.data80

        #    Columns     Format   Use
        #     1 -  5       A5     Packed minor planet number
        #     6 - 12       A7     Packed provisional designation, or a temporary designation
        #    13            A1     Discovery asterisk
        #    14            A1     Note 1
        #    15            A1     Note 2
        #    16 - 32              Date of observation
        #    33 - 44              Observed RA (J2000.0)
        #    45 - 56              Observed Decl. (J2000.0)
        #    57 - 65       9X     Must be blank
        #    66 - 71    F5.2,A1   Observed magnitude and band
        #                            (or nuclear/total flag for comets)
        #    72 - 77       X      Must be blank
        #    78 - 80       A3     Observatory code

        packed_id      = self.get_col(1, 12)
        discovery      = self.get_col(13)
        note1          = self.get_col(14)        # C=CCD, B=CMOS, V=Roving Observer, X=replaced
        note2          = self.get_col(15)        # leer, K=stacked, 0=?, 1=?
        date           = self.get_col(16, 32)
        ra             = self.get_col(33, 44)
        dec            = self.get_col(45, 56)
        #blank                       (57, 65)
        mag            = self.get_col(66, 70)
        band           = self.get_col(71)
        cat            = self.get_col(72)        # catalog codes
        packed_ref     = self.get_col(73, 77)    # publication reference
        code           = self.get_col(78, 80)

        ic(self)
        ic(packed_id, discovery, note1, note2, date, ra, dec, mag, band, cat, packed_ref, code)

        (perm_id, prov_id) = MPCData80.unpack_id(packed_id)

        year = date[0:4]                # FIXME: quick hack to get the MPEC year, is this really correct?
        ref = MPCData80.unpack_reference(packed_ref, year)
        ic(perm_id, prov_id, ref)

        self.obj["permId"] = perm_id
        self.obj["provId"] = prov_id
        self.obj["discovery"] = discovery.strip()
        self.obj["note1"] = note1
        self.obj["note2"] = note2
        self.obj["date"] = date         # FIXME: convert to proper date
        self.obj["ra"] = ra
        self.obj["dec"] = dec
        self.obj["mag"] = mag
        self.obj["band"] = band
        self.obj["catalog"] = mpc_catalog_codes[cat] if cat != " " else ""
        self.obj["reference"] = ref if ref != "     " else ""
        self.obj["code"] = code


    def get_json(self, indent=4):
        return json.dumps(self.obj, indent=indent)


    def decode_single(c):
        v = ord(c)
        if v >= ord("0"):
            if v >= ord("A"):
                if v >= ord("a"):
                    return v - ord("a") + 10 + 26
                return v - ord("A") + 10
            return v - ord("0")
        return 0
    
    def decode_base62(s): 
        """ Input s = ~XXXX """
        return ( ( (  MPCData80.decode_single(s[1]) * 62 
                    + MPCData80.decode_single(s[2])      ) * 62 
                    + MPCData80.decode_single(s[3])             ) * 62
                    + MPCData80.decode_single(s[4])                    )


    # Below adapted from https://github.com/IAU-ADES/ADES-Master/blob/master/Python/bin/packUtil.py
    def unpack_reference(packedref, year):
        if packedref[0] == "E":                                     # Temporary MPEC
            packedref = "MPEC " + year + "-" + packedref[1] + str( "{:02d}".format(int(packedref[2:])) )
        elif packedref[0] in '0123456789':                          # MPC case A
            packedref = "MPC  " + str(int(packedref))               #   <5-digit number>
        elif packedref[0] == '@':                                   # MPC case B
            packedref = "MPC  " + str(100000 + int(packedref[1:]))  #   @<4-digit number>
        elif packedref[0] == '#':                                   # MPC case C
            n = 110000 + MPCData80.decode_base62(packedref)         #   ~<4-digit radix 62>
            packedref = "MPC  " + str(n)
        elif packedref[0] in 'abcdefghijklmnopqrstuvwxyz':          # MPS case D
            n = int(packedref[1:]) + 10000*'abcdefghijklmnopqrstuvwxyz'.index(packedref[0])
            packedref = "MPS  " + str(n)                            #   <letter + 4-digit base 10>
        elif packedref[0] == '~':                                   # MPS case E
            n = 260000 + MPCData80.decode_base62(packedref)         #   ~<4-digit radix 62>
            packedref = "MPS  " + str(n)
        # Case F, G not handled
        return packedref
    

    def unpack_id(packed):
        perm_id = ""
        prov_id = ""

        # Minor planet
        m = re.search(r'^(?: {5}|([0-9A-Za-z])(\d{4})|(~[0-9A-Za-z]{4}))' +
        #                         ^(1)         ^(2)    ^(3)
                      r'(?: {7}|([I-K])(\d{2})([A-HJ-Y])([a-zA-Z0-9])(\d)(?:([A-HJ-Z])|0))$', packed)
        #                        ^(4)   ^(5)   ^(6)      ^(7)         ^(8)   ^(9)
        if m:
            ic(m)
            # permId
            if m.group(1) or m.group(3):
                if m.group(1):
                    n = int(m.group(2)) + 10000 * MPCData80.decode_single(m.group(1))
                if m.group(3):
                    n = 620000 + MPCData80.decode_base62(m.group(3))
                if n:
                    perm_id = "(" + str(n) + ")"
            # provId
            if m.group(4):
                y = MPCData80.decode_single(m.group(4)) * 100 + int(m.group(5))
                y = "{0:0d}".format(y)
                n = MPCData80.decode_single(m.group(7)) * 10 + int(m.group(8))
                ns = str(n) if n>0 else ""
                if m.group(9):  # normal asteroid provid
                    prov_id =  y + ' ' + m.group(6) + m.group(9) + ns
                else:           # comet ID -- use A/
                    prov_id =  'A/' + y + ' ' + m.group(6) + ns
    
        # Comets
        m = re.search(r'^(?: {4}|(\d{4}))([APCDXI])' +
        #                         ^(1)    ^(3)
                      r'(?:([0-9A-Za-z])(\d{2})([A-HJ-Y])([a-zA-Z0-9])(\d)(?:0|([A-Z])|([a-z])))$', packed)
        #                   ^(3)         ^(4)   ^(5)      ^(6)         ^(7)     ^(8)    ^(9)
        if m:
            type = m.group(2)
            if m.group(1):
                n = int(m.group(1))
                perm_id = str(n) + type
                # now check for fragments
                if m.group(9):
                    perm_id = perm_id + '-' + m.group(9).upper()
                if m.group(11):
                    frag = (m.group(10) + m.group(11)).strip().upper()
                perm_id = perm_id + '-' + frag

            if m.group(3):
                y = MPCData80.decode_single(m.group(3)) * 100 + int(m.group(4))
                y = "{0:0d}".format(y)
                n = MPCData80.decode_single(m.group(6)) * 10 + int(m.group(7))
                ns = str(n) if n>0 else ""
                extra = ''
                if m.group(8): # m.group(8) changes nothing 
                    extra = m.group(8) # adds order
                frag = ''
                if m.group(9): # fragment letter
                    frag = '-' + m.group(9).upper()

                prov_id =  m.group(2) + '/' + y + ' ' + m.group(5) + extra + ns + frag

        return (perm_id, prov_id)




### Can be run as a command line script ###
def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Parse MPC 80-column data format",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("data80", help="80-column data, use quotes!")

    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()

    data = MPCData80(args.data80)
    data.parse_data()
    print(data.get_json())


if __name__ == "__main__":
    main()
