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

# ChangeLog
# Version 0.1 / 2023-06-24
#       Added -n option, read filter name from CSV
# Version 0.2 / 2023-06-26
#       Use new target template "Target NEO v2.json"
#       Use new base template "NEW v4 nautical.json"
#       Works with nautical dusk/dawn time, too, see caveat below
# Version 0.3 / 2023-07-01
#       Added -N option, append number of frames to target name
# Version 0.4 / 2023-07-03
#       New target template "./NINA-Templates-IAS/Base NEO nautical.json"
#       New base template "./NINA-Templates-IAS/Base NEO nautical.json"
#       Removed -l option
# Version 1.0 / 2023-07-04
#       Cleaner handling of SelectedProvider references in completed sequence
#       Process External Script with TARGET
#       General clean-up
# Version 1.1 / 2024-06-28
#       Changes for Remote3, added -3 --remote3 option
# --- nina-create-sequence2 ---
# Version 1.2 / 2024-07-25
#       Use JSONConfig, verbose modules
#       Removed a lot of options (now handled in config)
#       New option -A --debug-print-attr
#       New config setting "container", add target items to this container in target area

# See here https://www.newtonsoft.com/json/help/html/SerializingJSON.htm for the JSON serializing used in N.I.N.A

# Entries in nina-create-sequence.json:
# "<NAME>": {
#     "template":  "<BASE SEQUENCE TEMPLATE>",
#     "target":    "<SINGLE TARGET TEMPLATE>",
#     "container": "<CONTAINER NAME OR EMTYP>",
#     "format":    "<TARGETNAME {x}>",
#     "output":    "<OUTPUT FILENAME {x}>.json"
# }
#
# Format placeholders:
# 0=target, 1=date, 2=seq, 3=number

VERSION = "1.2 / 2024-07-25"
AUTHOR  = "Martin Junius"
NAME    = "nina-create-sequence2"

import sys
import os
import argparse
import json
import csv
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
import copy

# The following libs must be installed with pip
import tzdata
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose          import verbose, warning, error
from jsonconfig       import JSONConfig, config



DEFAULT_FILTER_NAMES = [ "L", "R", "G", "B", "Ha", "OIII", "SII"]


CONFIG = "nina-create-sequence.json"

class SequenceConfig(JSONConfig):
    """ JSON Config for creating NINA sequences """

    def __init__(self, file=None):
        super().__init__(file)

  

config = SequenceConfig(CONFIG)



class Options:
    """ Command line options """
    debug_print_attr = False            # -A --debug-print-attr



class TargetData:
    """ Holds data to update N.I.N.A template """

    def __init__(self, name, target, ra, dec, time, number, exposure, filter="L", binning="2x2"):
        self.name = name
        self.targetname = target
        (self.ra_hh, self.ra_mm, self.ra_ss) = ra.split(":")
        (self.dec_dd, self.dec_mm, self.dec_ss) = dec.split(":")
        (self.time_hh, self.time_mm, self.time_ss) = str(time).split(":")
        self.number = number
        self.exposure = exposure
        self.filter = filter
        self.binning = 0
        if str(binning).startswith("1"):
            self.binning = 1
        if str(binning).startswith("2"):
            self.binning = 2




class NINABase:
    """Base class for NINASequence and NINATarget"""

    def __init__(self):
        self.obj = None


    def read_json(self, file):
        with open(file, 'r') as f:
            data = json.load(f)
        self.obj = data


    def write_json(self, file):
        with open(file, 'w') as f:
            json.dump(self.obj, f, indent = 2)


    def traverse(self, func=None, param=None):
        self.traverse_obj(self.obj, ">", 1, func, param)


    def traverse_obj(self, obj, indent, level, func=None, param=None):
        if Options.debug_print_attr:
            print(indent, "KEYS =", ", ".join(obj.keys()))

        if func:
            func(self, obj, indent + ">", param)

        for k, val in obj.items():
            if k=="$id" or k=="$type" or k=="$ref" or k=="Name":
                self.print_attr(obj, k, indent+" >")

            if type(val) is dict:
                """dict"""
                self.traverse_obj(val, indent + " >", level + 1, func, param)
            elif type(val) is str:
                """str"""
            elif type(obj[k]) is list:
                """list"""
                for val1 in val:
                    self.traverse_obj(val1, indent + " >", level + 1, func, param)
            else:
                """rest"""


    def set_prefix(self, prefix):
        self.id_prefix = prefix


    def add_prefix_to_id(self, obj, indent, param=None):
        # change "$id" and "$ref"
        self.__add_prefix(obj, "$id")
        self.__add_prefix(obj, "$ref")


    def __add_prefix(self, obj, key):
        if key in obj:
            # obj[key] = str(self.id_prefix*1000 + int(obj[key]))
            # JSON serializing in NINA uses pure numeric ids, but strings
            # work as well and are collision free
            obj[key] = f"{self.id_prefix:04d}_{int(obj[key]):04d}"


    def process_provider(self, obj, indent, dict):
        # search for Provider {...} and change additional occurences to reference
        self.print_attr(obj, "SelectedProvider", "")
        if "SelectedProvider" in obj.keys():
            prov = obj["SelectedProvider"]
            if "$type" in prov.keys():
                type = prov["$type"]
                id   = prov["$id"]
                if type in dict.keys():
                    # already exists
                    ref = dict[type]
                    obj["SelectedProvider"] = { "$ref": ref }

                else:
                    # 1st occurence, don't touch
                    dict[type] = id
        self.print_attr(obj, "SelectedProvider", "")


    def print_attr(self, obj, name, indent):
        if Options.debug_print_attr:
            if name in obj:
                print(indent, name, "=", obj[name])




class NINATarget(NINABase):
    """Holds data read from N.I.N.A JSON template for target"""

    def __init__(self):
        self.name        = None # template name
        self.targetname  = None # astro target name
        # instance variables created by process_data(), referencing the data objects, used by update_target_data()
        self.target      = None
        self.coord       = None
        self.waitfortime = None
        self.conditions0 = None
        self.filter      = None
        self.exposure    = None
        self.binning     = None
        self.timecondition = None
        self.script_w_target = None
        # instance variables created by process_data(), referencing the inner containers
        # [0] Pre-imaging (slew, AF, WaitForTime)
        # [1] Imaging (exposure loop)
        # [2] Post-imaging (create flag &c.)
        self.container_items = None
        self.container_conditions = None
        self.container_triggers = None

        NINABase.__init__(self)


    def update_target_data(self, data):
        # NEW NAME --> obj["Name"]
        self.obj["Name"] = data.name
        self.name = data.name

        # NEW TARGET --> target["TargetName"]
        self.target["TargetName"] = data.targetname

        # NEW COORD --> coord["..."]
        # Coordinates in WaitForAltitude don't need to be updated, handled automatically by N.I.N.A when loading
        self.coord["RAHours"]   = int(data.ra_hh)
        self.coord["RAMinutes"] = int(data.ra_mm)
        self.coord["RASeconds"] = float(data.ra_ss)
        self.coord["NegativeDec"] = True if int(data.dec_dd) < 0 else False
        self.coord["DecDegrees"] = int(data.dec_dd)
        self.coord["DecMinutes"] = int(data.dec_mm)
        self.coord["DecSeconds"] = float(data.dec_ss)

        # NEW TIME --> waitfortime["..."]
        if self.waitfortime:
            self.waitfortime["Hours"]   = int(data.time_hh)
            self.waitfortime["Minutes"] = int(data.time_mm)
            self.waitfortime["Seconds"] = int(data.time_ss)

        # NEW NUMBER OF EXPOSURES --> conditions0["Iterations"]
        self.conditions0["Iterations"] = int(data.number)

        # NEW FILTER --> filter["_name"]
        self.filter["_name"] = data.filter

        # NEW EXPOSURETIME --> exposure["ExposureTime"]
        self.exposure["ExposureTime"] = float(data.exposure)
        # NEW BINNING --> exposure["Binning"]["X|Y"]
        if data.binning > 0:
            self.exposure["Binning"]["X"] = data.binning
            self.exposure["Binning"]["Y"] = data.binning

        # Update target for External Script
        if self.script_w_target:
            script = self.script_w_target["Script"]
            self.script_w_target["Script"] = script.replace("\"TARGET\"", "\"{}\"".format(data.targetname))



    def process_data(self):
        self.name = self.obj["Name"]
        verbose("NINATarget(process_data):", "name =", self.name)

        self.target = self.obj["Target"]
        self.targetname = self.target["TargetName"]
        self.coord = self.target["InputCoordinates"]

        items = self.obj["Items"]

        self.container_items      = []
        self.container_conditions = []
        self.container_triggers   = []

        for item in items["$values"]:
            type = item["$type"]
            # print("type =", type)
            if "Container.SequentialContainer" in type:
                self.container_items.append(item["Items"]["$values"])
                self.container_conditions.append(item["Conditions"]["$values"])
                self.container_triggers.append(item["Triggers"]["$values"])

        self.__process_container_list()


    def __process_container_list(self):
        for container in self.container_items + self.container_conditions + self.container_triggers:
            for item in container:
                if "WaitForTime" in item["$type"]:
                    self.waitfortime = item

                if "SmartExposure" in item["$type"]:
                    # NEW NUMBER OF EXPOSURES --> conditions0["Iterations"]
                    self.conditions0 = item["Conditions"]["$values"][0]

                    items = item["Items"]
                    for item2 in items["$values"]:
                        if "SwitchFilter" in item2["$type"]:
                            self.filter = item2["Filter"]
                        if "TakeExposure"  in item2["$type"]:
                            self.exposure = item2

                if "TimeCondition" in item["$type"]:
                    self.timecondition = item

                if "ExternalScript" in item["$type"]:
                    self.script_w_target = item


    def add_parent(self, id):
        verbose("NINATarget(add_parent):", "id =", id)

        self.obj["Parent"] = { "$ref": id }


    def set_expanded(self, flag):
        verbose("NINATarget(set_expanded):", "flag =", flag)

        self.obj["IsExpanded"] = flag




class NINASequence(NINABase):
    """Holds data read from N.I.N.A JSON sequence"""

    def __init__(self):
        self.name         = None # template name
        # instance variables created by process_data(), referencing the data objects, used by update_target_data()
        self.start_list   = None
        self.targets_list = None
        self.end_list     = None
        self.start_id     = None
        self.targets_id   = None
        self.end_id       = None

        # This dictionary holds the ids of the various time SelectedProvider{}, to be replaced with reference
        # on further occurences
        self.provider_dict = {}

        NINABase.__init__(self)


    def process_data(self):
        self.name = self.obj["Name"]
        verbose("NINASequence(process_data):", "name =", self.name)

        items = self.obj["Items"]["$values"]
        self.area_list = items
        for item in items:
            for k in item.keys():
                if k=="$id" or k=="$type" or k=="$ref" or k=="Name":
                    self.print_attr(item, k, ">")

        self.start_list   = self.area_list[0]["Items"]["$values"]
        self.targets_list = self.area_list[1]["Items"]["$values"]
        self.end_list     = self.area_list[2]["Items"]["$values"]
        self.start_id     = self.area_list[0]["$id"]
        self.targets_id   = self.area_list[1]["$id"]
        self.end_id       = self.area_list[2]["$id"]
        if ic.enabled:
            ic(self.start_id, self.start_list)
            ic(self.targets_id, self.targets_list)
            ic(self.end_id, self.end_list)


    def search_container(self, container):
        """ Search for named container in target area (targets_list) """
        if container:
            verbose("NINASequence(search_container):", "name =", container)
            for item in self.targets_list:
                type = item["$type"]
                name = item["Name"]
                if "Container.SequentialContainer" in type and name==container:
                    self.targets_list = item["Items"]["$values"]
                    self.targets_id   = item["$id"]
                    if ic.enabled:
                        ic("NEW in container")
                        ic(self.targets_id, self.targets_list)                    
                    break
                


    def append_target(self, target):
        verbose("NINASequence(append_target):", "name =", target.name)

        self.targets_list.append(target.obj)


    def process_csv(self, target_tmpl, file, target_format):
        # tz_NA = timezone(timedelta(hours=2, minutes=0))
        tz_NA = ZoneInfo("Africa/Windhoek")

        with open(file, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Object"]=="Azelfafage" or row["RA"]=="":
                    continue

                seq = int(row["#"])
                # target must not contain [/:]
                target = row["Object"].replace("/", "").replace(":", "").replace("\"", "")
                time_utc = datetime.fromisoformat(row["Observation date"].replace(" ", "-") + "T" + 
                                                           row["Time UT"] + ":00+00:00")
                # Python 3.9 doesn't like the "Z" timezone declaration, thus +00:00
                # convert to Namibian time zone = UTC+2
                time_NA  = time_utc.astimezone(tz_NA)
                ra  = row["RAm"].replace(" ", ":").replace("+", "")
                dec = row["DECm"].replace(" ", ":").replace("+", "")
                # use RA/DEC if RAm/DECm are empty
                if ra=="":
                    ra  = row["RA"].replace(" ", ":").replace("+", "")
                if dec=="":
                    dec = row["Dec."].replace(" ", ":").replace("+", "")
                exp = float(row["Exposure time"])
                number = int(row["No images"])
                filter = "L"
                if "filter" in row.keys():
                    filter = row["filter"]
                    for fn in DEFAULT_FILTER_NAMES:
                        if filter.startswith(fn):
                            filter = fn
                            break

                # format target name for templates
                target.replace("/", "").replace(":", "")

                # 0=target, 1=date, 2=seq, 3=number
                # formatted_target = "{1} {2:03d} {0} (n{3:03d})".format(target, time_NA.date(), seq, number)
                # (from config)
                formatted_target = target_format.format(target, time_NA.date(), seq, number)
                ic(target, formatted_target)

                # Replace target with formatted target, as NINA currently only support $$TARGETNAME$$
                # in filename templates under Options > Imaging
                target = formatted_target

                print("NINASequence(process_csv):", "#{:03d} target={} RA={} DEC={}".format(seq, target, ra, dec))
                print("NINASequence(process_csv):", "     UT={} / local {} {}".format(time_utc, time_NA.date(), time_NA.time()))
                print("NINASequence(process_csv):", "     {:d}x{:.1f}s filter={}".format(number, exp, filter))

                # default for filter and binning
                data = TargetData(formatted_target, target, ra, dec, time_NA.time(), number, exp, filter)

                # create deep copy of target object, update with data read from CSV
                target_new = copy.deepcopy(target_tmpl)
                target_new.update_target_data(data)

                ### append to main sequence targets
                # the following changes are necessary to append target_new to the list of the target area
                target_new.set_prefix(seq)
                target_new.traverse(NINABase.add_prefix_to_id)
                # add parent ref to target object
                target_new.add_parent(self.targets_id)
                # collapse view
                target_new.set_expanded(False)
                self.append_target(target_new)

        # update all SelectedProvider {...} with references
        self.traverse(NINABase.process_provider, self.provider_dict)




def main(argv):
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Create/populate multiple N.I.N.A target templates/complete sequence with data from NEO Planner CSV",
        epilog      = "Version: " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-A", "--debug-print-attr", action="store_true", help="extra debug output")
    arg.add_argument("-D", "--destination-dir", help="output dir for created sequence")
    arg.add_argument("-o", "--output", help="output .json file")
    arg.add_argument("-n", "--no-output", action="store_true", help="dry run, don't create output files")
    arg.add_argument("-S", "--setting", help="use template/target SETTING from config")
    arg.add_argument("filename", nargs="+", help="CSV target data list")
   
    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()

    Options.debug_print_attr = args.debug_print_attr

    if args.setting:
        if not args.setting in config.get_keys():
            error(f"setting {args.setting} not in config")
        setting = config.get(args.setting)
    else:
        error(f"must supply a setting with --setting, valid:",
              ", ".join([k for k in config.get_keys() if not k.startswith("#")]))
    ic(args.setting, setting)

    target_template = setting["target"]
    verbose("processing target template", target_template)
    sequence_template = setting["template"]
    verbose("processing sequence template", sequence_template)
    target_format = setting["format"]
    verbose("target format (0=target, 1=date, 2=seq, 3=number)", target_format)
    output_format = setting["output"]
    verbose("output format (1=date)", output_format)
    container = setting["container"]
    verbose(f"add target items to container '{container}', empty=target area")

    if args.destination_dir:
        destination_dir = args.destination_dir
    else:
        destination_dir = os.path.join(config.get_documents_path(), "N.I.N.A")
    verbose("destination directory", destination_dir)
    if args.output:
        output = args.output
    else:
        output = output_format.format("", str(date.today()))
    verbose("output file", output)

    target = NINATarget()
    target.read_json(target_template)
    target.process_data()

    sequence = NINASequence()
    sequence.read_json(sequence_template)
    sequence.process_data()
    sequence.search_container(container)

    for f in args.filename:
        verbose("processing CSV file", f)
        sequence.process_csv(target, f, target_format)

    output_path = os.path.join(destination_dir, output)
    if not args.no_output:
        verbose("writing JSON sequence", output_path)
        sequence.write_json(output_path)


   
if __name__ == "__main__":
   main(sys.argv[1:])