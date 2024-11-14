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
# Version 1.6 / 2024-07-15
#       Major refactoring using the new modules, added Overview processing
# Version 1.7 / 2024-11-14
#       Fixed -n --no-wamo-requests

import os
import argparse
import re
import csv

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose          import verbose, warning, error
from mpc.mpcosarchive import Publication
from mpc.mpcwamo      import retrieve_from_wamo
from mpc.mpcdata80    import MPCData80
from ovoutput         import OverviewOutput
from csvoutput        import CSVOutput
from jsonoutput       import JSONOutput



NAME    = "mpc-retrieve-reports"
VERSION = "1.6 / 2024-07-15"
AUTHOR  = "Martin Junius"



class Options:
    """ Global command line options """
    no_wamo     = False     # -n --no-wamo-requests
    mpc1992     = False     # -M --mpc1992-reports
    ades        = False     # -A --ades-reports
    output      = None      # -o --output
    csv         = False     # -C --csv
    overview    = False     # -O --overview
    sort_by_date= False     # -D --sort-by-date



def retrieve_from_directory(root):
    for dir, subdirs, files in os.walk(root):
        verbose("Processing directory", dir)
        for f in files:
            if f.endswith(".txt") or f.endswith(".TXT"):
                # print("f =", f)
                process_file(os.path.join(dir, f))



def process_file(file):
    with open(file, "r") as fh:
        ic(file)
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
            JSONOutput.add_obj(obj)



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

    if not Options.no_wamo:
        wamo = retrieve_from_wamo(ids)
        if wamo:
            mpc1992_obj["_wamo"] = wamo
            # Get publications and add to global list
            for obs in wamo:
                pub = obs["publication"]
                if pub:
                    Publication.add(pub)
                if Options.sort_by_date:
                    OverviewOutput.add(obs["data"]["date_minus12"], obs["objId"], obs["data"]["data"])
                else:
                    OverviewOutput.add(obs["objId"], obs["data"]["date_minus12"], obs["data"]["data"])
        else:
            warning("data from MPC1992 report not found in WAMO, submitted ADES instead?")

    # verbose("JSON =", json.dumps(mpc1992_obj, indent=4))

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

    if not Options.no_wamo:
        wamo = retrieve_from_wamo(ids)
        if wamo:
            ades_obj["_wamo"] = wamo
            # Get publications and add to global list
            for obs in wamo:
                pub = obs["publication"]
                if pub:
                    Publication.add(pub)
                if Options.sort_by_date:
                    OverviewOutput.add(obs["data"]["date_minus12"], obs["objId"], obs["data"]["data"])
                else:
                    OverviewOutput.add(obs["objId"], obs["data"]["date_minus12"], obs["data"]["data"])
        else:
            warning("data from ADES report not found in WAMO, submitted MPC1992 instead?")
       
    # verbose("JSON =", json.dumps(ades_obj, indent=4))

    return ades_obj



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
    arg.add_argument("-C", "--csv", action="store_true", help="use CSV output format (instead of JSON), NOT YET IMPLEMENTED")
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

    if Options.sort_by_date:
        OverviewOutput.set_description1("Total observation dates:  ")
        OverviewOutput.set_description2("Total single observations:")
    else:
        OverviewOutput.set_description1("Total objects:             ")
        OverviewOutput.set_description2("Total single observations: ")

    for dir in args.directory:
        # quick hack: Windows PowerShell adds a stray " to the end of dirname 
        # if it ends with a backslash \ AND contains a space!!!
        # see here https://bugs.python.org/issue39845
        dir = dir.rstrip("\"")
        if os.path.isdir(dir):
            retrieve_from_directory(dir)
        if os.path.isfile(dir):
            process_file(dir)

    if Options.overview:
        if Options.output:
            with open(Options.output, 'w', newline='', encoding="utf-8") as f:
                OverviewOutput.print(f)
                Publication.print(f)
        else:
            OverviewOutput.print()
            Publication.print()

    elif Options.csv:
        CSVOutput.write(Options.output)
    else:
        JSONOutput.write(Options.output)



if __name__ == "__main__":
    main()
