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
# Explanation of References on Astrometric Observations
# (Column 73-77 of observation record)
#   https://minorplanetcenter.net/iau/info/References.html
#
# See also this github repo
#   https://github.com/IAU-ADES/ADES-Master/tree/master/Python/bin

# ChangeLog
# Version 0.1 / 2023-1013
#       Moved Data80 class from mpc-retrieve-ack to here, renamed to MPCData80
#       Can be imported as a module or run as a command line script

import sys
import os
import argparse
import re
# The following libs must be installed with pip
from icecream import ic

global VERSION, AUTHOR
VERSION = "0.1 / 2023-10-13"
AUTHOR  = "Martin Junius"



class MPCData80:
    def __init__(self, data):
        self.data80 = data


    def parse_data(self):
        self.obj = {}
        self.obj["data80"] = self.data80

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

        packed_id      = self.data80[0:12]
        discovery      = self.data80[12]
        note1          = self.data80[13]        # C=CCD, B=CMOS, V=Roving Observer, X=replaced
        note2          = self.data80[14]        # leer, K=stacked, 0=?, 1=?
        date           = self.data80[15:32]
        ra             = self.data80[32:44]
        dec            = self.data80[44:56]
        #blank         = self.data80[56:65]
        mag            = self.data80[65:70]
        band           = self.data80[70]
        #???           = self.data80[71]
        packed_ref     = self.data80[72:77]     # publication reference
        code           = self.data80[77:80]

        ic(self)
        ic(packed_id, discovery, note1, note2, date, ra, dec, mag, band, packed_ref, code)

        (perm_id, prov_id) = MPCData80.unpack_id(packed_id)
        ref = MPCData80.unpack_reference(packed_ref)
        ic(perm_id, prov_id, ref)



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
    def unpack_reference(packedref):
        if packedref[0] == "E":                                     # Temporary MPEC
            packedref = "MPEC <YEAR>-" + packedref[1] + str( "{:02d}".format(int(packedref[2:])) )
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
        prog        = "mpc-data80",
        description = "Parse MPC 80-column data format",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    # arg.add_argument("-n", "--name", help="example option name")
    # arg.add_argument("-i", "--int", type=int, help="example option int")
    arg.add_argument("data80", help="80-column data, use quotes!")

    args = arg.parse_args()

    global OPT_V
    OPT_V = args.verbose

    data = MPCData80(args.data80)
    data.parse_data()



if __name__ == "__main__":
    main()
