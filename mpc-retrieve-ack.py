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

# Retrieve MPC ACK mails from IMAP mailbox, measurement IDs, measurement data, MPECs etc.

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
# Version 0.0 / 2023-08-07
#       First test version
# Version 0.1 / 2023-08-12
#       First somewhat usable version, retrieves ACK mails and WAMO data
# Version 0.2 / 2023-08-14
#       List MPECs with published measurements separately

import sys
import os
import errno
import argparse
import json
import imaplib
import re
import time
import csv
# The following libs must be installed with pip
import requests
from icecream import ic

global NAME, VERSION, AUTHOR
NAME    = "mpc-retrieve-ack"
VERSION = "0.2 / 2023-08-14"
AUTHOR  = "Martin Junius"

global CONFIG, WAMO_URL, MPEC_URL
CONFIG = "astro-python/imap-account.json"
WAMO_URL = "https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo"
MPEC_URL = "https://cgi.minorplanetcenter.net/cgi-bin/displaycirc.cgi"



class Config:
    """ JSON Config for IMAP account """

    verbose     = False     # -v --verbose
    no_wamo     = False     # -n --no-wamo-requests
    list_folder = False     # -l --list-folders-only
    inbox       = "INBOX"   # -F --imap-foldeer
    msgs_list   = None      # -m --msgs
    mpc1992     = False     # -M --mpc1992-reports
    ades        = False     # -A --ades-reports

    def __init__(self, file=None):
        self.obj = None
        self.file = file

        # get JSON config from %APPDATA%
        appdata = os.environ.get('APPDATA')
        if not appdata:
            print(NAME+":", "environment APPDATA not set!")
            sys.exit(errno.ENOENT)
        self.appdata = appdata.replace("\\", "/")

        ##FIXME: use os.path
        self.config = self.appdata + "/" + (file if file else CONFIG)
        if Config.verbose:
            print(NAME+":", "config file", self.config)
        if not os.path.isfile(self.config):
            print(NAME+":", "config file", self.config, 
                  "doesn't exist, must contain:\n   ",
                  '{ "server": "<FQDN>", "account": "<ACCOUNT>", "password": "<PASSWORD>", "inbox": "<INBOX>" }')
            sys.exit(errno.ENOENT)



    def read_json(self, file=None):
        file = self.config if not file else file
        with open(file, 'r') as f:
            data = json.load(f)
        self.obj = data


    def write_json(self, file=None):
        file = self.config if not file else file
        with open(file, 'w') as f:
            json.dump(self.obj, f, indent = 2)


    def get_server(self):
        return self.obj["server"]

    def get_account(self):
        return self.obj["account"]

    def get_password(self):
        return self.obj["password"]

    def get_inbox(self):
        return self.obj["inbox"]



class MPEC:
    mpec_cache = {}

    def add_publication(pub):
        m = re.search(r'MPEC (\d\d\d\d-[A-Z]\d\d)', pub)
        if m:
            MPEC.mpec_cache[m.group(1)] = True


    def print_mpec_list():
        for id in MPEC.mpec_cache.keys():
            print(id, ":", retrieve_from_mpc_mpec(id))



class Data80:
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

        packed_perm_id = self.data80[0:5]
        packed_prov_id = self.data80[5:12]
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
        ic(packed_perm_id, packed_prov_id, discovery, note1, note2, date, ra, dec, mag, band, packed_ref, code)

        ref = Data80.unpack_reference(packed_ref)
        ic(ref)



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
        """Input s = ~XXXX """
        return ( ( (  Data80.decode_single(s[1]) * 62 
                    + Data80.decode_single(s[2])      ) * 62 
                    + Data80.decode_single(s[3])             ) * 62
                    + Data80.decode_single(s[4])                    )


    # Adapted from https://github.com/IAU-ADES/ADES-Master/blob/master/Python/bin/packUtil.py
    def unpack_reference(packedref):
        if packedref[0] == "E":                                     # Temporary MPEC
            packedref = "<YEAR>-" + packedref[1] + str(int(packedref[2:]))
        elif packedref[0] in '0123456789':                          # MPC case A
            packedref = "MPC  " + str(int(packedref))               #   <5-digit number>
        elif packedref[0] == '@':                                   # MPC case B
            packedref = "MPC  " + str(100000 + int(packedref[1:]))  #   @<4-digit number>
        elif packedref[0] == '#':                                   # MPC case C
            n = 110000 + Data80.decode_base62(packedref)            #   ~<4-digit radix 62>
            packedref = "MPC  " + str(n)
        elif packedref[0] in 'abcdefghijklmnopqrstuvwxyz':          # MPS case D
            n = int(packedref[1:]) + 10000*'abcdefghijklmnopqrstuvwxyz'.index(packedref[0])
            packedref = "MPS  " + str(n)                            #   <letter + 4-digit base 10>
        elif packedref[0] == '~':                                   # MPS case E
            n = 260000 + Data80.decode_base62(packedref)            #   ~<4-digit radix 62>
            packedref = "MPS  " + str(n)
        # Case F, G not handled
        return packedref



def retrieve_from_imap(cf):
    """ Connect to IMAP server and retrieve ACK mails """

    if Config.verbose:
        print(NAME+":", "retrieving mails from IMAP server", cf.get_server())
    server = imaplib.IMAP4_SSL(cf.get_server())
    server.login(cf.get_account(), cf.get_password())

    if Config.list_folder:
        # Print list of mailboxes on server
        print(NAME+":", "folders on IMAP server", cf.get_server())
        code, mailboxes = server.list()
        for mailbox in mailboxes:
            print("   ", mailbox.decode().split(' "." ')[1])
        return

    # Select mailbox
    if Config.verbose:
        print(NAME+":", "from inbox", Config.inbox)
        if Config.msgs_list:
            print(NAME+":", "messages", Config.msgs_list)
    server.select(Config.inbox)

    typ, data = server.search(None, 'ALL')
    for num in data[0].split():
        if Config.msgs_list:
            if not int(num) in Config.msgs_list:
                continue

        typ, data = server.fetch(num, '(RFC822)')
        print("Message", num.decode("utf-8"))
        msg = data[0][1].decode()
        ack1 = False
        sub1 = False
        ids1 = False
        msg_date = "-no Date header-"
        msg_ack = "-no ACK reference-"
        msg_submission = "-no submission id-"
        msg_ids = {}
        for line in msg.splitlines():
            if ack1:
                ack1 = False
                msg_ack = line.strip()
            if sub1:
                sub1 = False
                msg_submission = line.strip()
            if ids1:
                m = re.search(r'^(.+) -> ([A-Za-z0-9]+)$', line)
                if m:    
                    msg_ids[m.group(2)] = m.group(1)
            if line.startswith("Date: "):
                msg_date = line
            if line.startswith("The submission with the ACK line:"):
                ack1 = True
            if line.startswith("The following submission ID has been assigned to these observations:"):
                sub1 = True
            if line.startswith("(IDs are NOT assigned to observations already submitted):"):
                ids1 = True
        
        print("   ", msg_date)
        print("   ", msg_ack)
        print("   ", msg_submission)
        if Config.verbose:
            for id, obs in msg_ids.items():
                print("       ", id, ":", obs)

        retrieve_from_mpc_wamo(msg_ids)

    # Cleanup
    server.close()
    server.logout()



def retrieve_from_mpc_wamo(ids):
    """ Retrieve observation data from minorplanetcenter WAMO """

    if Config.no_wamo:
        return
    if not ids:
        # empty ids dict
        return

    # Example
    # curl -v -d "obs=LdY91I230000FGdd010000001" https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo

    data = { "obs": "\r\n".join(ids.keys())}
    x = requests.post(WAMO_URL, data=data)

    wamo = []
    for line in x.text.splitlines():
        if Config.verbose:
            print("WAMO>", line)
        if line == "":
            continue

        m = re.search(r'^(.+) \(([A-Za-z0-9]+)\) has been identified as (.+) and published in (.+)\.$', line)
        if not m:
            m = re.search(r'^(.+) \(([A-Za-z0-9]+)\) has been identified as (.+), (publication is pending).$', line)
        if m:    
            data = m.group(1)
            id   = m.group(2)
            obj  = m.group(3)
            pub  = m.group(4)
            print("       ", id, ":", data)
            print("       ", " " * len(id), ":", obj)
            print("       ", " " * len(id), ":", pub)
            MPEC.add_publication(pub)

            data80 = Data80(data)
            data80.parse_data()

            wamo.append({"data":          data, 
                         "observationID": id,
                         "objID":         obj,
                         "publication":   pub  })
        else:
            print("unknown>", line)

    # Avoid high load on the MPC server
    time.sleep(0.5)

    return wamo



def retrieve_from_mpc_mpec(id):
    """ Retrieve MPEC from minorplanetcenter """

    # Example
    # curl -v -d "S=M&F=P&N=2023-P25" https://cgi.minorplanetcenter.net/cgi-bin/displaycirc.cgi
    # yields 302 redirect
    # Location: https://www.minorplanetcenter.net/mpec/K23/K23P25.html

    if Config.verbose:
        print(NAME+":", "retrieving MPEC", id)
    data = { "S": "M",  "F": "P",  "N": id }
    x = requests.post(MPEC_URL, data=data, allow_redirects=False)

    # print(x.headers)
    url = x.headers["Location"]
    if Config.verbose:
        print(NAME+":", "MPEC", id, "URL =", url)

    return url



def retrieve_from_directory(root):
    for dir, subdirs, files in os.walk(root):
        print("Processing directory", dir)
        for f in files:
            if f.endswith(".txt") or f.endswith(".TXT"):
                # print("f =", f)
                process_file(os.path.join(dir, f))


def process_file(file):
    with open(file, "r") as fh:
        line1 = fh.readline().strip()
        # print("line1 =", line1)

        # Old MPC 1992 report format
        if line1.startswith("COD "):
            if Config.mpc1992:
                if Config.verbose: print("Processing MPC1992", file)
                process_mpc1992(fh, line1)

        # New ADES (PSV) report format
        elif line1 == "# version=2017":
            if Config.ades:
                if Config.verbose: print("Processing ADES", file)
                process_ades(fh, line1)

        else:
            if Config.verbose: print("Not processing", file)



def process_mpc1992(fh, line1):
    mpc1992_obj = {}
    mpc1992_obj["_observations"] = []
    ids = {}

    line = line1
    while line:
        # meta data header
        m = re.match(r'^([A-Z0-9]{3}) (.+)$', line)
        if m:
            print(m.groups())
            (m1, m2) = m.groups()
            # requires Python >= 3.10!
            match m1:
                case "COD":
                    mpc1992_obj["observatory"] = {"mpcCode": m2}
                case "CON":
                    mpc1992_obj["submitter"] = {"name": m2}
                case "OBS":
                    mpc1992_obj["observers"] = {"name": m2}
                case "MEA":
                    mpc1992_obj["measurers"] = {"name": m2}
                case "TEL":
                    mpc1992_obj["telescope"] = {"description": m2}      ##FIXME: split as in ADES report
                case "NUM":
                    mpc1992_obj["_number"] = int(m2)
                case "ACK":
                    mpc1992_obj["_ack_line"] = m2
                case "AC2":
                    mpc1992_obj["_ac2_line"] = m2

        # data lines
        else:
            mpc1992_obj["_observations"].append({"data": line})
            ids[line] = True

        line = fh.readline().rstrip()
        if line.startswith("----- end"):
            break

    wamo = retrieve_from_mpc_wamo(ids)
    if wamo:
        mpc1992_obj["_wamo"] = wamo
    
    # print(mpc1992_obj)
    if Config.verbose:
        print(json.dumps(mpc1992_obj, indent=4))



def dict_remove_ws(dict):
    return {k.strip():v.strip() for k, v in dict.items()}


def process_ades(fh, line1):
    ades_obj = {}

    # Read report txt file
    key1 = None
    key2 = None
    while True:
        pos = fh.tell()
        line = fh.readline()
        if not line:
            break

        # meta data header
        m = re.match(r'^(#|!) (\w+) ?(.+)?$', line.strip())
        if m:
            print(m.groups())
            (m1, m2, m3) = m.groups()
            if m1 == "#":
                key1 =  m2
                ades_obj[key1] ={}
            if m1 == "!":
                key2 = m2
                ades_obj[key1][key2] = m3

        # PSV from this line on
        else:
            fh.seek(pos)
            ades_obj["_observations"] = []
            reader = csv.DictReader(fh, delimiter='|', quoting=csv.QUOTE_NONE)
            for row in reader:
                print(dict_remove_ws(row))
                ades_obj["_observations"].append(dict_remove_ws(row))

            break

    # Get trackIds and mpcCode to query WAMO
    ids = {}
    for trk in ades_obj["_observations"]:
        ids[trk["trkSub"] + " " + trk["stn"]] = True
    ades_obj["_ids"] = ids
    wamo = retrieve_from_mpc_wamo(ids)
    if wamo:
        ades_obj["_wamo"] = wamo

    print(ades_obj)



# Hack from https://stackoverflow.com/questions/6405208/how-to-convert-numeric-string-ranges-to-a-list-in-python
def str_to_list(s):
    return sum(((list(range(*[int(j) + k for k,j in enumerate(i.split('-'))]))
         if '-' in i else [int(i)]) for i in s.split(',')), [])



def main():
    cf = Config()
    cf.read_json()

    if cf.get_inbox():
        Config.inbox = cf.get_inbox()

    arg = argparse.ArgumentParser(
        prog        = "mpc-retrieve-ack",
        description = "Retrieve MPC ACK data",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-n", "--no-wamo-requests", action="store_true", help="don't request observations from minorplanetcenter.net WAMO")
    arg.add_argument("-l", "--list-folders-only", action="store_true", help="list folders on IMAP server only")
    arg.add_argument("-f", "--imap-folder", help="IMAP folder to retrieve mails, default "+Config.inbox)
    arg.add_argument("-m", "--msgs", help="retrieve messages in MSGS range only, e.g. \"1-3,5\", default all")
    arg.add_argument("directory", nargs="*", help="read MPC reports from directory/file instead of ACK mails")
    arg.add_argument("-M", "--mpc1992-reports", action="store_true", help="read old MPC 1992 reports")
    arg.add_argument("-A", "--ades-reports", action="store_true", help="read new ADES (PSV format) reports")
    args = arg.parse_args()

    Config.verbose     = args.verbose
    Config.no_wamo     = args.no_wamo_requests
    Config.list_folder = args.list_folders_only
    if args.imap_folder:
        Config.inbox = args.imap_folder
    if args.msgs:
        Config.msgs_list = str_to_list(args.msgs)
    Config.mpc1992     = args.mpc1992_reports
    Config.ades        = args.ades_reports

    if args.directory:
        for dir in args.directory:
            # quick hack: Windows PowerShell adds a stray " to the end of dirname 
            # if it ends with a backslash \ AND contains a space!!!
            # see here https://bugs.python.org/issue39845
            dir = dir.rstrip("\"")
            if os.path.isdir(dir):
                retrieve_from_directory(dir)
            if os.path.isfile(dir):
                process_file(dir)
    else:
        retrieve_from_imap(cf)

    print("\nPublished in the following MPECs")
    MPEC.print_mpec_list()



if __name__ == "__main__":
    main()
