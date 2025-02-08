#!/usr/bin/env python

# Copyright 2023-2025 Martin Junius
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
# Version 0.1 / 2024-06-07
#       Retrieve observations from MPC WAMO
# Version 1.0 / 2024-07-17
#       Bumped version number to 1.0
# Version 1.1 / 2025-01-22
#       Use JSON-style WAMO API instead of line-oriented,
#       new functions retrieve_from_wamo_json(),
#       get_wamo_fields(), get_wamo_data(), added typing

import argparse
import re
import time

# The following libs must be installed with pip
import requests
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose       import verbose, warning, error
from mpc.mpcdata80 import MPCData80



VERSION = "1.1 / 2025-01-22"
AUTHOR  = "Martin Junius"
NAME    = "mpcwamo"

# Use WAMO API, see https://data.minorplanetcenter.net/wamo-api/
WAMO_URL = "https://data.minorplanetcenter.net/api/wamo"



def get_wamo_fields() -> list:
    """
    Get fields list for CSV output

    :return: field list
    :rtype: list
    """

    return ["objId", "publication",
            "data80", 
            "permId", "provId", "discovery", 
            "note1", "note2",
            "obs_date", "obs_date_minus12", 
            "ra", "dec", 
            "mag", "band", "catalog",
            "reference", "code" ]


def get_wamo_data(wobj: dict) -> list:
    """
    Get data list from WAMO object for CSV output, corresponding to field list above

    :param wobj: WAMO object
    :type wobj: dict
    :return: data list
    :rtype: list
    """
    # Special handling of mag as a float
    mag = wobj["data"]["mag"]
    if mag:
        mag = float(mag)
    # Replace objId with permId oder provId
    objId = wobj["data"]["permId"] or wobj["data"]["provId"] or wobj["objId"]
    return [ objId, wobj["publication"],
             wobj["data"]["data"],
             wobj["data"]["permId"], wobj["data"]["provId"], wobj["data"]["discovery"],
             wobj["data"]["note1"], wobj["data"]["note2"], 
             wobj["data"]["date"], wobj["data"]["date_minus12"], 
             wobj["data"]["ra"], wobj["data"]["dec"], 
             mag, wobj["data"]["band"], wobj["data"]["catalog"], 
             wobj["data"]["reference"], wobj["data"]["code"]
            ]



def retrieve_from_wamo_json(ids: dict) -> list:
    """
    Retrieve observation data from MPC WAMO service, JSON API

    :param ids: dict with ids to query (using the keys)
    :type ids: dict
    :return: list of parsed WAMO data
    :rtype: list
    """
    if not ids:
        # empty ids dict
        return None

    # Return JSON results
    result = requests.get(WAMO_URL, json=list(ids.keys()))
    observations = result.json()
    # ic(observations)

    wamo = []
    # for line in observations.splitlines():
    for item in observations.get("found"):
        # ic(item, item.keys())
        for k, obs_list in item.items():
            # ic(k, obs_list)
            for obs in obs_list:
                line = obs["status_decoded"]
                ic(k, obs, line)
                if line == "":
                    continue

                ## FIXME: use JSON results, don't parse text lines
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
                        pub = False
                    # Must be handled outside of this function
                    #     pub = "pending"
                    # else:
                    #     Publication.add_publication(pub)

                    data80 = MPCData80(data)

                    wamo.append({"data":          data80.get_obj(),
                                "observationID": id,
                                "objId":         obj,
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
                                    "objId":         data80.get_col(6, 12),    # tracklet ID
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
                    m = re.search(r'(.*) was not found\.$', line)
                    if m:
                        warning(f"not found: {m.group(1)}")

                if not m:
                    warning(f"unknown response: {line}")
                    warning("corresponding observations:")
                    for obs in ids.keys():
                        warning(f"    {obs}")

    # Avoid high load on the MPC server
    time.sleep(1.0)

    return wamo



def retrieve_from_wamo(ids):
    """ Retrieve observation data from minorplanetcenter WAMO (old version) """
    ### WARNING: return text results, doesn't seem to work as of 2025-01-22 ###

    if not ids:
        # empty ids dict
        return None

    # Return text results, doesn't seem to work as of 2025-01-22
    result = requests.get(WAMO_URL, json={'return_type': 'string', 'obs': list(ids.keys())})
    observations = result.text
    ic(observations)

    wamo = []
    for line in observations.splitlines():
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
                pub = False
            # Must be handled outside of this function
            #     pub = "pending"
            # else:
            #     Publication.add_publication(pub)

            data80 = MPCData80(data)

            wamo.append({"data":          data80.get_obj(),
                         "observationID": id,
                         "objId":         obj,
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
                            "objId":         data80.get_col(6, 12),    # tracklet ID
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
            m = re.search(r'(.*) was not found\.$', line)
            if m:
                warning(f"not found: {m.group(1)}")

        if not m:
            warning(f"unknown response: {line}")
            warning("corresponding observations:")
            for obs in ids.keys():
                warning(f"    {obs}")

    # Avoid high load on the MPC server
    time.sleep(1.0)

    return wamo



### Test run as a command line script ###
def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Retrieve observations from MPC WAMO API",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("id", nargs="+",help="observation id")

    args = arg.parse_args()

    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    if args.debug:
        ic.enable()

    ids = { k: "-no obs-" for k in args.id }
    ic(ids)

    wamo = retrieve_from_wamo_json(ids)
    ic(wamo)


if __name__ == "__main__":
    main()
