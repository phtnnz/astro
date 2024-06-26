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
# Version 1.4 / 2024-06-26
#       Copy of mpc-retrieve-ack.py 1.4 for refactoring
# Version 1.5 / 2024-06-26
#       Removed all code for IMAP handling, now solely handled in mpc-retrieve-ack

import sys
import os
import argparse
import json
import re
import time
import csv

# The following libs must be installed with pip
import requests
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose          import verbose, warning, error
from mpc.mpcosarchive import MPCOSArchive
from mpc.mpcdata80    import MPCData80



NAME    = "mpc-retrieve-reports"
VERSION = "1.5 / 2024-06-26"
AUTHOR  = "Martin Junius"

WAMO_URL = "https://www.minorplanetcenter.net/cgi-bin/cgipy/wamo"
MPEC_URL = "https://cgi.minorplanetcenter.net/cgi-bin/displaycirc.cgi"



class Options:
    """ Global command line options """
    no_wamo     = False     # -n --no-wamo-requests
    mpc1992     = False     # -M --mpc1992-reports
    ades        = False     # -A --ades-reports
    output      = None      # -o --output
    csv         = False     # -C --csv
    overview    = False     # -O --overview
    sort_by_date= False     # -D --sort-by-date



class Publication:
    pub_cache = {}

    def add_publication(pub):
            Publication.pub_cache[pub] = True


    def print_publication_list():
        if Publication.pub_cache:
            arc = MPCOSArchive()

            print("\nPublished:")
            for id in Publication.pub_cache.keys():
                m = re.search(r'^MPEC (\d\d\d\d-[A-Z]\d+)', id)
                if m:
                    print(id, ":", retrieve_from_mpc_mpec(m.group(1)))
                else:
                    r = arc.search_pub(id)
                    if r:
                        print(id, ":", r["pdf"])
                    else:
                        print(id, ": unknown")



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


class ObsOverview:
    """ Store all objects with respective list of observatons """
    obj_cache = {}

    def add_obs(key1, key2, obs):
        if not key1 in ObsOverview.obj_cache:
            ObsOverview.obj_cache[key1] = {}
        dict2 = ObsOverview.obj_cache[key1]
        if not key2 in dict2:
            dict2[key2] = []
        dict2[key2].append(obs)


    def print_all():
        key1_count = 0
        key2_count = 0
        obs_count = 0

        for key1, dict2 in sorted(ObsOverview.obj_cache.items(), key=natural_keys):
            print(key1)
            key1_count += 1

            for key2, list in sorted(dict2.items(), key=natural_keys):
                print("   ", key2)
                key2_count += 1
                obs_count += len(list)

                for obs in list:
                    print("       ", obs)

        print()
        if Options.sort_by_date:
            print(f"Total observation dates:   {key1_count}")
            print(f"Total single observations: {obs_count}")
        else:
            print(f"Total objects:             {key1_count}")
            print(f"Total single observations: {obs_count}")

    
    def write_overview(file):
        with open(file, 'w') as f:
            sys.stdout = f
            ObsOverview.print_all()
            Publication.print_publication_list()



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



def retrieve_from_mpc_wamo(ids):
    """ Retrieve observation data from minorplanetcenter WAMO """

    if Options.no_wamo:
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
        ic(line)
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
            verbose("       ", id, ":", data)
            verbose("       ", " " * len(id), ":", obj)
            verbose("       ", " " * len(id), ":", pub)
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
                id = m.group(1)
                pub = "Processing queue " + m.group(2)
                verbose("       ", id, ":", pub)

        if not m:
            m = re.search(r'^(.+) \(([A-Za-z0-9]+)\) is on the (NEOCP/PCCP).$', line)
            if m:
                data = m.group(1)
                id   = m.group(2)
                pub  = m.group(3)
                verbose("       ", id, ":", data)
                verbose("       ", " " * len(id), ":", pub)
                data80 = MPCData80(data)

                wamo.append({"data":          data80.get_obj(),
                            "observationID": id,
                            "objID":         data80.get_col(6, 12),    # tracklet ID
                            "publication":   pub  })

        if not m:
            m = re.search(r'^The obsID \'([A-Za-z0-9]+)\' has been deleted.$', line)
            if m:
                id = m.group(1)
                warning(f"id {id} = observation \"{ids[id]}\" deleted")

        if not m:
            m = re.search(r'^The obsID \'([A-Za-z0-9]+)\' was flagged as a near-duplicate.$', line)
            if m:
                id = m.group(1)
                warning(f"id {id} = observation \"{ids[id]}\" flagged near-duplicate")

        if not m:
            warning("unknown response:", line)
            warning("corresponding observations:", ids)

    # Avoid high load on the MPC server
    time.sleep(0.5)

    return wamo



def retrieve_from_mpc_mpec(id):
    """ Retrieve MPEC from minorplanetcenter """

    # Example
    # curl -v -d "S=M&F=P&N=2023-P25" https://cgi.minorplanetcenter.net/cgi-bin/displaycirc.cgi
    # yields 302 redirect
    # Location: https://www.minorplanetcenter.net/mpec/K23/K23P25.html

    data = { "S": "M",  "F": "P",  "N": id }
    x = requests.post(MPEC_URL, data=data, allow_redirects=False)

    # print(x.headers)
    url = x.headers["Location"]
    ic(id, url)

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
            if Options.mpc1992:
                verbose("Processing MPC1992", file)
                format = "MPC1992"
                obj = process_mpc1992(fh, line1)

        # New ADES (PSV) report format
        elif line1 == "# version=2017":
            if Options.ades:
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
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Retrieve MPC reports",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-n", "--no-wamo-requests", action="store_true", help="don't request observations from minorplanetcenter.net WAMO")
    arg.add_argument("directory", nargs="+", help="read MPC reports from directory/file instead of ACK mails")
    arg.add_argument("-M", "--mpc1992-reports", action="store_true", help="read old MPC 1992 reports")
    arg.add_argument("-A", "--ades-reports", action="store_true", help="read new ADES (PSV format) reports")
    arg.add_argument("-o", "--output", help="write JSON/CSV to OUTPUT file")
    arg.add_argument("-C", "--csv", action="store_true", help="use CSV output format (instead of JSON)")
    arg.add_argument("-O", "--overview", action="store_true", help="create overview of objects and observations")
    arg.add_argument("-D", "--sort-by-date", action="store_true", help="sort overview by observation date (minus 12h)")
    args = arg.parse_args()

    verbose.set_prog(NAME)
    verbose.enable(args.verbose)
    if args.debug:
        ic.enable()

    Options.no_wamo     = args.no_wamo_requests
    Options.mpc1992     = args.mpc1992_reports
    Options.ades        = args.ades_reports
    Options.output      = args.output
    Options.csv         = args.csv
    Options.overview    = args.overview
    Options.sort_by_date= args.sort_by_date

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

    if Options.overview and not Options.output:
        ObsOverview.print_all()
        Publication.print_publication_list()

    if Options.output:
        if Options.overview:
            ObsOverview.write_overview(Options.output)
        elif Options.csv:
            CSVOutput.write_csv(Options.output)
        else:
            JSONOutput.write_json(Options.output)



if __name__ == "__main__":
    main()
