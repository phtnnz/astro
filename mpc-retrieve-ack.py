#!/usr/bin/python

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

# See https://www.minorplanetcenter.net/iau/info/PackedDes.html for a description of
# the "packed" designations of minor planets

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
# The following libs must be installed with pip
import requests

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
        msg_ids = {}
        for line in msg.splitlines():
            if ack1:
                ack1 = False
                msg_ack = line.strip()
            if sub1:
                sub1 = False
                msg_submission = line.strip()
            if ids1:
                m = re.search(r'^(.+)  -> ([A-Za-z0-9]+)$', line)
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

        if not Config.no_wamo:
            retrieve_from_mpc_wamo(msg_ids)

    # Cleanup
    server.close()
    server.logout()



def retrieve_from_mpc_wamo(ids):
    """ Retrieve observation data from minorplanetcenter WAMO """

    # Example
    # curl -v -d "obs=LdY91I230000FGdd010000001" https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo

    data = { "obs": "\r\n".join(ids.keys())}
    x = requests.post(WAMO_URL, data=data)

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
        else:
            print("unknown>", line)

    # Avoid high load on the MPC server
    time.sleep(0.5)



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
                print("f =", f)
                process_file(os.path.join(dir, f))



def process_file(file):
    with open(file, "r") as fh:
        line1 = fh.readline().strip()
        print("line1 =", line1)

        # Old MPC 1992 report format
        if line1.startswith("COD ") and Config.mpc1992:
            if Config.verbose: print("Processing MPC1992", file)
            process_mpc1992(fh, line1)

        # New ADES (PSV) report format
        elif line1 == "# version=2017" and Config.ades:
            if Config.verbose: print("Processing ADES", file)
            process_ades(fh, line1)

        else:
            if Config.verbose: print("Not processing", file)



def process_mpc1992(fh, line1):
    pass



def process_ades(fh, line1):
    pass



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
    arg.add_argument("directory", nargs="*", help="read MPC reports from directory instead of ACK mails")
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
            retrieve_from_directory(dir)
    else:
        retrieve_from_imap(cf)

    print("\nPublished in the following MPECs")
    MPEC.print_mpec_list()



if __name__ == "__main__":
    main()
