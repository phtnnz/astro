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

# ChangeLog
# Version 0.0 / 2023-08-07
#       First test version

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
VERSION = "0.0 / 2023-08-07"
AUTHOR  = "Martin Junius"

global CONFIG, WAMO_URL
CONFIG = "astro-python/imap-account.json"
WAMO_URL = "https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo"



class Config:
    """ JSON Config for IMAP account """

    verbose  = False        # -v --verbose
    inbox    = "INBOX"      # -F --imap-foldeer


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



def retrieve_from_imap(cf):
    """ Connect to IMAP server and retrieve ACK mails """

    if Config.verbose:
        print(NAME+":", "retrieving mails from IMAP server", cf.get_server())
    server = imaplib.IMAP4_SSL(cf.get_server())
    server.login(cf.get_account(), cf.get_password())

    # Print list of mailboxes on server
    code, mailboxes = server.list()
    for mailbox in mailboxes:
        print(mailbox.decode("utf-8"))

    # Select mailbox
    if Config.verbose:
        print(NAME+":", "from inbox", Config.inbox)
    server.select(Config.inbox)

    typ, data = server.search(None, 'ALL')
    for num in data[0].split():
        typ, data = server.fetch(num, '(RFC822)')
        print("Message", num.decode("utf-8"))
        msg = data[0][1].decode("utf-8")
        ack1 = False
        ids1 = False
        msg_ids = []
        for line in msg.splitlines():
            if ack1:
                ack1 = False
                msg_ack = line.strip()
            if ids1:
                m = re.search(r'-> ([A-Za-z0-9]+)$', line)
                if m:    
                    msg_ids.append(m.group(1))
            if line.startswith("Date: "):
                msg_date = line
            if line.startswith("The submission with the ACK line:"):
                ack1 = True
            if line.startswith("(IDs are NOT assigned to observations already submitted):"):
                ids1 = True
        
        if Config.verbose:
            print("   ", msg_date)
            print("    ", end="")
            print(msg_ack)
            print("    ", end="")
            print("\n    ".join(msg_ids))

        retrieve_from_mpc_wamo(msg_ids)

    # Cleanup
    server.close()
    server.logout()



def retrieve_from_mpc_wamo(ids):
    """ Retrieve observation data from minorplanetcenter WAMO """

    # Example
    # curl -v -d "obs=LdY91I230000FGdd010000001" https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo

    data = { "obs": "\r\n".join(ids)}
    x = requests.post(WAMO_URL, data=data)

    print(x.text)

    # Avoid high load on the MPC server
    time.sleep(0.5)



def main():
    arg = argparse.ArgumentParser(
        prog        = "mpc-retrieve-ack",
        description = "Retrieve MPC ACK data",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-f", "--imap-folder", help="IMAP folder to retrieve mails, default "+Config.inbox)
    args = arg.parse_args()

    Config.verbose = args.verbose

    cf = Config()
    cf.read_json()

    if cf.get_inbox():
        Config.inbox = cf.get_inbox()
    if args.imap_folder:
        Config.inbox = args.imap_folder
    

    retrieve_from_imap(cf)
    # retrieve_from_mpc_wamo(["LdY91I230000FGdd010000001"])



if __name__ == "__main__":
    main()
