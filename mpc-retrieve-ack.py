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
# Version 1.1 / 2023-12-06
#       Added -O --overview output, listing all objects and respective observations
# Version 1.2 / 2024-01-06
#       Some clean-up, improved output
# Version 1.3 / 2024-02-02
#       Added -D --sort-by-date option for overview output
# Version 1.4 / 2024-03-20
#       Somewhat refactored, using jsonconfig module
# Version 1.5 / 2024-06-26
#       Refactored, removed all code for reading report txt files, this will be
#       handled in mpc-retrieve-reports
# Version 1.6 / 2024-07-15
#       More refactoring, moved WAMO request to new module mpcwamo, moved Publication
#       class to mpcosarchive, moved ObsOverview to ovoutput, use csvoutput, moved
#       JSONOutput to jsonoutput, fixed output
# Version 1.7 / 2024-07-17
#       Added -m --match, -J --json options
# Version 1.8 / 2024-11-10
#       Fixed -n --no-wamo-requests

import argparse
import imaplib
import re

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose          import verbose, warning, error
from jsonconfig       import JSONConfig, config
from mpc.mpcosarchive import Publication
from mpc.mpcwamo      import retrieve_from_wamo
from ovoutput         import OverviewOutput
from csvoutput        import CSVOutput
from jsonoutput       import JSONOutput


NAME    = "mpc-retrieve-ack"
VERSION = "1.8 / 2024-11-10"
AUTHOR  = "Martin Junius"

CONFIG = "imap-account.json"



class Options:
    """ Global command line options """
    no_wamo     = False     # -n --no-wamo-requests
    list_folder = False     # -l --list-folders-only
    list_msgs   = False     # -L --list-messages-only
    inbox       = "INBOX"   # -F --imap-folder
    msgs_list   = None      # -m --msgs
    output      = None      # -o --output
    csv         = False     # -C --csv
    overview    = False     # -O --overview
    sort_by_date= False     # -D --sort-by-date
    match       = None      # -m --match
    json        = False     # -J --json
    submitted   = False     # -S --submitted


class RetrieveConfig(JSONConfig):
    """ JSON Config for IMAP account """

    def __init__(self, file=None):
        super().__init__(file)

    def get_server(self):
        return self.config["server"]

    def get_account(self):
        return self.config["account"]

    def get_password(self):
        return self.config["password"]

    def get_inbox(self):
        return self.config["inbox"]


# Get config with IMAP account data
config = RetrieveConfig(CONFIG)



def retrieve_from_imap(cf):
    """ Connect to IMAP server and retrieve ACK mails """

    verbose("retrieving mails from IMAP server", cf.get_server())
    server = imaplib.IMAP4_SSL(cf.get_server())
    server.login(cf.get_account(), cf.get_password())

    if Options.list_folder:
        # Print list of mailboxes on server
        print("Folders on IMAP server", cf.get_server())
        code, mailboxes = server.list()
        mblist = [ mailbox.decode().split(' "." ')[1] for mailbox in mailboxes ]
        mblist.sort()
        for mb in mblist:
            print("   ", mb)
        return

    # Select mailbox
    verbose("from folder(s)", Options.inbox)
    if Options.msgs_list:
        verbose("messages", Options.msgs_list)

    for folder in Options.inbox.split(","):
        server.select(folder)
        retrieve_from_folder(server, folder)

    # Cleanup
    server.close()
    server.logout()


def retrieve_from_folder(server, folder):
    server.select(folder)

    typ, data = server.search(None, 'ALL')
    for num in data[0].split():
        if Options.msgs_list:
            if not int(num) in Options.msgs_list:
                continue

        typ, data = server.fetch(num, '(RFC822)')
        n = int(num.decode())
        verbose("Folder", folder, "/ message", n)
        msg = data[0][1].decode()
        obj = retrieve_from_msg(folder, n, msg)
        if obj:
            JSONOutput.add_obj(obj)



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

    if Options.match:
        if not Options.match in msg_subject:
            return None
                    
    if Options.list_msgs:
        nstr = "[{:03d}]".format(msg_n)
        print(nstr, msg_date)
        print(" " * len(nstr), msg_subject)
        if Options.csv:
            # CSV output: list of messages in mailbox
            CSVOutput.add_fields([ "Folder", "Message#", "Date", "Subject" ])
            CSVOutput.add_row([msg_folder, msg_n, msg_date.removeprefix("Date: "), msg_subject.removeprefix("Subject: ")])
        return None
    
    verbose(" ", msg_date)
    verbose(" ", msg_subject)
    verbose(" ", msg_ack)
    verbose(" ", msg_submission)
    for id, obs in msg_ids.items():
        verbose(id, ":", obs)
    ack_obj["message"] = msg_n
    ack_obj["date"] = msg_date
    ack_obj["subject"] = msg_subject
    ack_obj["ack"] = msg_ack
    ack_obj["submission"] = msg_submission

    if Options.no_wamo:
        if Options.csv:
            for id, obs in msg_ids.items():
                # CSV output: list of messages in mailbox with id and obs
                CSVOutput.add_fields([ "Folder", "Message#", "Date", "ACK", "id", "obs" ])
                CSVOutput.add_row([ msg_folder, msg_n, msg_date.removeprefix("Date: "), msg_ack, id, obs ])
    else:
        # mpc.mpcwamo module
        wamo = retrieve_from_wamo(msg_ids)
        if wamo:
            # Get publications and add to global list
            for obs in wamo:
                pub = obs["publication"]
                if pub:
                    Publication.add(pub)

            ack_obj["_wamo"].append(wamo)
            if Options.csv:
                for wobj in wamo:
                    # CSV output: list of messages in mailbox with complete WAMO data
                    CSVOutput.add_fields([  "Folder", "Message#", "Date", "ACK", 
                                            "id", "objId", "publication",
                                            "data80", 
                                            "permId", "provId", "discovery", 
                                            "note1", "note2",
                                            "obs_date", "obs_date_minus12", 
                                            "ra", "dec", 
                                            "mag", "band", "catalog",
                                            "reference", "code" ])
                    # Special handling of mag as a float
                    mag = wobj["data"]["mag"]
                    if mag:
                        mag = float(mag)
                    # Replace objId with permId oder provId
                    objId = wobj["data"]["permId"] or wobj["data"]["provId"] or wobj["objID"]
                    ic(mag, objId)
                    CSVOutput.add_row([ msg_folder, msg_n, msg_date.removeprefix("Date: "), msg_ack, 
                                            wobj["observationID"], objId, wobj["publication"],
                                            wobj["data"]["data"],
                                            wobj["data"]["permId"], wobj["data"]["provId"], wobj["data"]["discovery"],
                                            wobj["data"]["note1"], wobj["data"]["note2"], 
                                            wobj["data"]["date"], wobj["data"]["date_minus12"], 
                                            wobj["data"]["ra"], wobj["data"]["dec"], 
                                            mag, wobj["data"]["band"], wobj["data"]["catalog"], 
                                            wobj["data"]["reference"], wobj["data"]["code"]
                                        ])

            if Options.overview:
                # for wobj in wamo:
                for wobj, orig in zip(wamo, msg_ids.values()):
                    text     = wobj["data"]["data"]
                    key_id   = wobj["objID"]
                    key_date = wobj["data"]["date_minus12"]
                    if Options.sort_by_date:
                        OverviewOutput.add(key_date, key_id, text)
                        if Options.submitted:
                            OverviewOutput.add(key_date, key_id, f"{orig}    << submitted (ACK mail)")
                    else:
                        OverviewOutput.add(key_id, key_date, text)
                        if Options.submitted:
                            OverviewOutput.add(key_id, key_date, f"{orig}    << submitted (ACK mail)")
       

    return ack_obj



# Hack from https://stackoverflow.com/questions/6405208/how-to-convert-numeric-string-ranges-to-a-list-in-python
def str_to_list(s):
    return sum(((list(range(*[int(j) + k for k,j in enumerate(i.split('-'))]))
         if '-' in i else [int(i)]) for i in s.split(',')), [])



def main():
    if config.get_inbox():
        Options.inbox = config.get_inbox()

    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Retrieve MPC ACK mails",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-wamo-requests", action="store_true", help="don't request observations from minorplanetcenter.net WAMO")
    arg.add_argument("-l", "--list-folders-only", action="store_true", help="list folders on IMAP server only")
    arg.add_argument("-f", "--imap-folder", help="IMAP folder(s) (comma-separated) to retrieve mails from, default "+Options.inbox)
    arg.add_argument("-L", "--list-messages-only", action="store_true", help="list messages in IMAP folder only")
    arg.add_argument("-m", "--msgs", help="retrieve messages in MSGS range only, e.g. \"1-3,5\", default all")
    arg.add_argument("-M", "--match", help="retrieve messages with subject containing MATCH")
    arg.add_argument("-o", "--output", help="write to OUTPUT file")
    arg.add_argument("-J", "--json", action="store_true", help="use JSON output format")
    arg.add_argument("-C", "--csv", action="store_true", help="use CSV output format")
    arg.add_argument("-O", "--overview", action="store_true", help="create overview of objects and observations")
    arg.add_argument("-S", "--submitted", action="store_true", help="add submitted observation to overview")
    arg.add_argument("-D", "--sort-by-date", action="store_true", help="sort overview by observation date (minus 12h)")
    args = arg.parse_args()

    verbose.set_prog(NAME)
    verbose.enable(args.verbose)
    if args.debug:
        ic.enable()

    Options.no_wamo     = args.no_wamo_requests
    Options.list_folder = args.list_folders_only
    Options.list_msgs   = args.list_messages_only
    if args.imap_folder:
        Options.inbox = args.imap_folder
    if args.msgs:
        Options.msgs_list = str_to_list(args.msgs)
    Options.output      = args.output
    Options.csv         = args.csv
    Options.overview    = args.overview
    Options.sort_by_date= args.sort_by_date
    Options.match       = args.match
    Options.json        = args.json
    Options.submitted   = args.submitted

    if Options.sort_by_date:
        OverviewOutput.set_description1("Total observation dates:  ")
        OverviewOutput.set_description2("Total single observations:")
    else:
        OverviewOutput.set_description1("Total objects:             ")
        OverviewOutput.set_description2("Total single observations: ")

    retrieve_from_imap(config)

    if Options.overview:
        if Options.output:
            with open(Options.output, 'w', newline='', encoding="utf-8") as f:
                OverviewOutput.print(f)
                Publication.print(f)
        else:
            OverviewOutput.print()
            Publication.print()

    elif Options.csv:
        CSVOutput.set_float_format("%.1f")  # for mag
        CSVOutput.write(Options.output)
    elif Options.json:
        JSONOutput.write(Options.output)



if __name__ == "__main__":
    main()
