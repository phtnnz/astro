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

# ChangeLog
# Version 0.0 / 2023-08-07
#       First test version
# Version 0.1 / 2023-08-12
#       First somewhat usable version, retrieves ACK mails and WAMO data
# Version 0.2 / 2023-08-14
#       List MPECs with published measurements separately
# Version 1.0 / 2023-12-02
#       Bumped version to 1.0 as most functions are there, 
#       new --csv option generating CSV output from ACK mails (and WAMO)

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
# Disable debugging
ic.disable()

# Local modules
from verbose import verbose, error
from mpcdata80 import MPCData80


global NAME, VERSION, AUTHOR
NAME    = "mpc-retrieve-ack"
VERSION = "1.0 / 2023-12-02"
AUTHOR  = "Martin Junius"

global CONFIG, WAMO_URL, MPEC_URL
CONFIG = "astro-python/imap-account.json"
WAMO_URL = "https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo"
MPEC_URL = "https://cgi.minorplanetcenter.net/cgi-bin/displaycirc.cgi"



class Config:
    """ JSON Config for IMAP account """

    no_wamo     = False     # -n --no-wamo-requests
    list_folder = False     # -l --list-folders-only
    list_msgs   = False     # -L --list-messages-only
    inbox       = "INBOX"   # -F --imap-folder
    msgs_list   = None      # -m --msgs
    mpc1992     = False     # -M --mpc1992-reports
    ades        = False     # -A --ades-reports
    output      = None      # -o --output
    csv         = False     # -C --csv

    def __init__(self, file=None):
        self.obj = None
        self.file = file

        # get JSON config from %APPDATA%
        appdata = os.environ.get('APPDATA')
        if not appdata:
            error("environment APPDATA not set!")
            sys.exit(errno.ENOENT)
        self.appdata = appdata.replace("\\", "/")

        ##FIXME: use os.path
        self.config = self.appdata + "/" + (file if file else CONFIG)
        verbose("config file", self.config)
        if not os.path.isfile(self.config):
            error("config file", self.config, 
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



class Publication:
    mpec_cache = {}

    def add_publication(pub):
            Publication.mpec_cache[pub] = True


    def print_publication_list():
        for id in Publication.mpec_cache.keys():
            m = re.search(r'^MPEC (\d\d\d\d-[A-Z]\d+)', id)
            if m:
                print(id, ":", retrieve_from_mpc_mpec(m.group(1)))
            else:
                print(id)



class ObsOverview:
    """ Store all objects with respective list of observatons """
    # obj_cache[object] = [ obs1, obs2, obs3, ... ]
    obj_cache = {}

    def add_obs(obj, obs):
        if ObsOverview.obj_cache[obj]:
            ObsOverview.obj_cache[obj].append(obs)
        else:
            ObsOverview.obj_cache[obj] = [ obs ]


    def print_all():
        for obj, list in ObsOverview.obj_cache.items():
            print(obj)
            for obs in list:
                print("   ", obs)



class JSONOutput:
    obj_cache = []

    def add_json_obj(obj):
        JSONOutput.obj_cache.append(obj)

    def write_json(file):
        with open(file, 'w') as f:
            json.dump(JSONOutput.obj_cache, f, indent = 4)


class CSVOutput:
    obj_cache = []
    fields = None

    def add_csv_obj(obj):
        CSVOutput.obj_cache.append(obj)

    def add_csv_fields(fields):
        CSVOutput.fields = fields

    def write_csv(file):
        with open(file, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel", delimiter=";", quoting=csv.QUOTE_ALL)
            if CSVOutput.fields:
                writer.writerow(CSVOutput.fields)
            writer.writerows(CSVOutput.obj_cache)



def retrieve_from_imap(cf):
    """ Connect to IMAP server and retrieve ACK mails """

    verbose("retrieving mails from IMAP server", cf.get_server())
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
    verbose("from folder(s)", Config.inbox)
    if Config.msgs_list:
        verbose("messages", Config.msgs_list)

    for folder in Config.inbox.split(","):
        server.select(folder)
        retrieve_from_folder(server, folder)

    # typ, data = server.search(None, 'ALL')
    # for num in data[0].split():
    #     if Config.msgs_list:
    #         if not int(num) in Config.msgs_list:
    #             continue

    #     typ, data = server.fetch(num, '(RFC822)')
    #     n = int(num.decode())
    #     # print("Message", num.decode("utf-8"))
    #     print("Message", n)
    #     msg = data[0][1].decode()
    #     obj = retrieve_from_msg(n, msg)
    #     if obj:
    #         JSONOutput.add_json_obj(obj)

    # Cleanup
    server.close()
    server.logout()


def retrieve_from_folder(server, folder):
    server.select(folder)

    typ, data = server.search(None, 'ALL')
    for num in data[0].split():
        if Config.msgs_list:
            if not int(num) in Config.msgs_list:
                continue

        typ, data = server.fetch(num, '(RFC822)')
        n = int(num.decode())
        print("Folder", folder, "/ message", n)
        msg = data[0][1].decode()
        obj = retrieve_from_msg(folder, n, msg)
        if obj:
            JSONOutput.add_json_obj(obj)



def retrieve_from_msg(msg_folder, msg_n, msg):
    ack_obj = {}
    ack_obj["_wamo"] = []

    ack1 = False
    sub1 = False
    ids1 = False
    msg_subject = "-no Subject header-"
    msg_date = "-no Date header-"
    msg_ack = "-no ACK reference-"
    msg_submission = "-no submission id-"
    msg_ids = {}

    # New code using iter, a bit tricky though. ;-)
    # Requires Python 3.8+
    line_iter = iter(msg.splitlines())
    while (line := next(line_iter, None)) != None:
        if line.startswith("Date: "):
            msg_date = line
        if line.startswith("Subject: "):
            msg_subject = line
            line = next(line_iter, None)
            if line[0].isspace():
                msg_subject = msg_subject + " " + line.lstrip()
                continue
        if line.startswith("The submission with the ACK line:"):
            line = next(line_iter)
            msg_ack = line.strip()
            continue
        if line.startswith("The following submission ID has been assigned to these observations:"):
            line = next(line_iter)
            msg_submission = line.strip()
            continue
        if line.startswith("(IDs are NOT assigned to observations already submitted):"):
            while (line := next(line_iter, None)) != None:
                m = re.search(r'^(.+) -> ([A-Za-z0-9]+)$', line)
                if m:    
                    msg_ids[m.group(2)] = m.group(1)

    if Config.list_msgs:
        print(" ", msg_date)
        print(" ", msg_subject)
        if Config.csv:
            # CSV output: list of messages in mailbox
            CSVOutput.add_csv_fields([ "Folder", "Message#", "Date", "Subject" ])
            CSVOutput.add_csv_obj([msg_folder, msg_n, msg_date.removeprefix("Date: "), msg_subject.removeprefix("Subject: ")])
        return None
    
    print(" ", msg_date)
    print(" ", msg_subject)
    print(" ", msg_ack)
    print(" ", msg_submission)
    for id, obs in msg_ids.items():
        verbose(id, ":", obs)
    ack_obj["message"] = msg_n
    ack_obj["date"] = msg_date
    ack_obj["subject"] = msg_subject
    ack_obj["ack"] = msg_ack
    ack_obj["submission"] = msg_submission

    wamo = retrieve_from_mpc_wamo(msg_ids)
    if wamo:
        ack_obj["_wamo"].append(wamo)
        if Config.csv:
            for wobj in wamo:
                # CSV output: list of messages in mailbox with complete WAMO data
                CSVOutput.add_csv_fields([ "Folder", "Message#", "Date", "ACK", "id", "objId", "publication",
                                           "obs80", "permId", "provId", "discovery", "note1", "note2",
                                           "obs_date", "ra", "dec", "mag", "band", "catalog",
                                           "reference", "code" ])
                CSVOutput.add_csv_obj([ msg_folder, msg_n, msg_date.removeprefix("Date: "), msg_ack, 
                                        wobj["observationID"], wobj["objID"], wobj["publication"],
                                        wobj["data"]["data"],
                                        wobj["data"]["permId"], wobj["data"]["provId"], wobj["data"]["discovery"],
                                        wobj["data"]["note1"], wobj["data"]["note2"], 
                                        wobj["data"]["date"], wobj["data"]["ra"], wobj["data"]["dec"], 
                                        wobj["data"]["mag"], wobj["data"]["band"], wobj["data"]["catalog"], 
                                        wobj["data"]["reference"], wobj["data"]["code"]
                                       ])
    else:
        if Config.csv:
            for id, obs in msg_ids.items():
                # CSV output: list of messages in mailbox with id and obs
                CSVOutput.add_csv_fields([ "Folder", "Message#", "Date", "ACK", "id", "obs" ])
                CSVOutput.add_csv_obj([ msg_folder, msg_n, msg_date.removeprefix("Date: "), msg_ack, id, obs ])
    verbose("JSON =", json.dumps(ack_obj, indent=4))

    return ack_obj



def retrieve_from_mpc_wamo(ids):
    """ Retrieve observation data from minorplanetcenter WAMO """

    if Config.no_wamo:
        return None
    if not ids:
        # empty ids dict
        return None

    # Example
    # curl -v -d "obs=LdY91I230000FGdd010000001" https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo

    ##FIXME: use API
    data = { "obs": "\r\n".join(ids.keys())}
    x = requests.post(WAMO_URL, data=data)

    wamo = []
    for line in x.text.splitlines():
        ic("WAMO>", line)
        if line == "":
            continue

        m = re.search(r'^(.+) \(([A-Za-z0-9]+)\) has been identified as (.+) and published in (.+)\.$', line)
        pending = False
        if not m:
            m = re.search(r'^(.+) \(([A-Za-z0-9]+)\) has been identified as (.+), (publication is pending).$', line)
            pending = True
        if m:    
            data = m.group(1)
            id   = m.group(2)
            obj  = m.group(3)
            pub  = m.group(4)
            print("       ", id, ":", data)
            print("       ", " " * len(id), ":", obj)
            print("       ", " " * len(id), ":", pub)
            if pending:
                pub = "pending"
            else:
                Publication.add_publication(pub)

            data80 = MPCData80(data)

            wamo.append({"data":          data80.get_obj(),
                         "observationID": id,
                         "objID":         obj,
                         "publication":   pub  })

        if not m:
            m = re.search(r'The obsID \'(.+)\' is in the \'(.+)\' processing queue.$', line)
            if m:
                id   = m.group(1)
                pub  = "Processing queue " + m.group(2)
                print("       ", id, ":", pub)

        if not m:
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

    verbose("retrieving MPEC", id)
    data = { "S": "M",  "F": "P",  "N": id }
    x = requests.post(MPEC_URL, data=data, allow_redirects=False)

    # print(x.headers)
    url = x.headers["Location"]
    verbose("MPEC", id, "URL =", url)

    return url



def retrieve_from_directory(root):
    for dir, subdirs, files in os.walk(root):
        verbose("Processing directory", dir)
        for f in files:
            if f.endswith(".txt") or f.endswith(".TXT"):
                # print("f =", f)
                process_file(os.path.join(dir, f))



def process_file(file):
    with open(file, "r") as fh:
        line1 = fh.readline().strip()
        obj = None

        # Old MPC 1992 report format
        if line1.startswith("COD "):
            if Config.mpc1992:
                verbose("Processing MPC1992", file)
                format = "MPC1992"
                obj = process_mpc1992(fh, line1)

        # New ADES (PSV) report format
        elif line1 == "# version=2017":
            if Config.ades:
                verbose("Processing ADES", file)
                format = "ADES"
                obj = process_ades(fh, line1)

        else:
            verbose("Not processing", file)

        if obj:
            obj["_file"] = file.replace("\\", "/")
            obj["_format"] = format
            JSONOutput.add_json_obj(obj)



def process_mpc1992(fh, line1):
    mpc1992_obj = {}
    mpc1992_obj["_observations"] = []
    ids = {}

    line = line1
    while line:
        # meta data header
        m = re.match(r'^([A-Z0-9]{3}) (.+)$', line)
        if m:
            ic(m.groups())
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
                    ## ADES
                    # # telescope
                    # ! design reflector
                    # ! aperture 0.25
                    # ! fRatio 4.5
                    # ! detector CMO
                    ## MPC1992
                    # TEL 0.25-m f/4.5 reflector + CMO
                    # sometimes f/X is missing
                    ic(m2)
                    mtel = re.match(r'^([0-9.]+)-m f/([0-9.]+) (.+) \+ (.+)$', m2)
                    if not mtel:
                        mtel = re.match(r'^([0-9.]+)-m ()(.+) \+ (.+)$', m2)
                    if mtel:
                        ic(mtel.groups())
                        mpc1992_obj["telescope"] = {"aperture": mtel.group(1), 
                                                    "fRatio":   mtel.group(2),
                                                    "design":   mtel.group(3), 
                                                    "detector": mtel.group(4)}
                    else:
                        mpc1992_obj["telescope"] = {"_description": m2}      ##FIXME: split as in ADES report
                case "NUM":
                    mpc1992_obj["_number"] = int(m2)
                case "ACK":
                    mpc1992_obj["_ack_line"] = m2
                case "AC2":
                    mpc1992_obj["_ac2_line"] = m2
                case "COM":
                    mpc1992_obj["_comment"] = m2
                case "NET":
                    mpc1992_obj["_catalog"] = m2

        # data lines
        else:
            data = MPCData80(line)
            mpc1992_obj["_observations"].append(data.get_obj())
            ids[line] = True

        line = fh.readline().rstrip()
        if line.startswith("----- end"):
            break

    wamo = retrieve_from_mpc_wamo(ids)
    if wamo:
        mpc1992_obj["_wamo"] = wamo
    verbose("JSON =", json.dumps(mpc1992_obj, indent=4))

    return mpc1992_obj



def dict_remove_ws(dict):
    """ Remove white space for dict keys and values """
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
            ic(m.groups())
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
                row1 = dict_remove_ws(row)
                ic(row1)
                ades_obj["_observations"].append(row1)
            break

    # Get trackIds and mpcCode to query WAMO
    ids = {}
    for trk in ades_obj["_observations"]:
        ids[trk["trkSub"] + " " + trk["stn"]] = True
    ades_obj["_ids"] = ids
    wamo = retrieve_from_mpc_wamo(ids)
    if wamo:
        ades_obj["_wamo"] = wamo
    verbose("JSON =", json.dumps(ades_obj, indent=4))

    return ades_obj



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
        prog        = NAME,
        description = "Retrieve MPC ACK data",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-wamo-requests", action="store_true", help="don't request observations from minorplanetcenter.net WAMO")
    arg.add_argument("-l", "--list-folders-only", action="store_true", help="list folders on IMAP server only")
    arg.add_argument("-f", "--imap-folder", help="IMAP folder(s) (comma-separated) to retrieve mails from, default "+Config.inbox)
    arg.add_argument("-L", "--list-messages-only", action="store_true", help="list messages in IMAP folder only")
    arg.add_argument("-m", "--msgs", help="retrieve messages in MSGS range only, e.g. \"1-3,5\", default all")
    arg.add_argument("directory", nargs="*", help="read MPC reports from directory/file instead of ACK mails")
    arg.add_argument("-M", "--mpc1992-reports", action="store_true", help="read old MPC 1992 reports")
    arg.add_argument("-A", "--ades-reports", action="store_true", help="read new ADES (PSV format) reports")
    arg.add_argument("-o", "--output", help="write JSON to OUTPUT file")
    arg.add_argument("-C", "--csv", action="store_true", help="use CSV output format (instead of JSON)")
    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        error.set_prog(NAME + ": ERROR")
        verbose.enable()
    if args.debug:
        ic.enable()

    Config.no_wamo     = args.no_wamo_requests
    Config.list_folder = args.list_folders_only
    Config.list_msgs   = args.list_messages_only
    if args.imap_folder:
        Config.inbox = args.imap_folder
    if args.msgs:
        Config.msgs_list = str_to_list(args.msgs)
    Config.mpc1992     = args.mpc1992_reports
    Config.ades        = args.ades_reports
    Config.output      = args.output
    Config.csv         = args.csv

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

    print("\nPublished:")
    Publication.print_publication_list()

    if Config.output:
        if Config.csv:
            CSVOutput.write_csv(Config.output)
        else:
            JSONOutput.write_json(Config.output)



if __name__ == "__main__":
    main()
