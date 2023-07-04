#!/usr/bin/python

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

# See here https://www.newtonsoft.com/json/help/html/SerializingJSON.htm for the JSON serializing used in N.I.N.A

global VERSION, AUTHOR
VERSION = "1.0 / 2023-07-04"
AUTHOR  = "Martin Junius"


import sys
import argparse
import json
import csv
import datetime
import copy
import ctypes.wintypes


# Windows hack to get path of Documents folder, which might reside on other drives than C:
CSIDL_PERSONAL = 5       # My Documents
SHGFP_TYPE_CURRENT = 0   # Get current, not default value
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)

global DEFAULT_NINA_DIR, DEFAULT_TARGETS_DIR
DEFAULT_NINA_DIR = buf.value.replace("\\", "/") + "/N.I.N.A"
DEFAULT_TARGETS_DIR = DEFAULT_NINA_DIR + "/Targets/tmp"

global DEFAULT_TEMPLATE, DEFAULT_TARGET
DEFAULT_TEMPLATE = "./NINA-Templates-IAS/Base NEO nautical.json"
DEFAULT_TARGET = "./NINA-Templates-IAS/Target NEO.json"

global DEFAULT_FILTER_NAMES
DEFAULT_FILTER_NAMES = [ "L", "R", "G", "B", "Ha", "OIII", "SII"]
# print("N.I.N.A dir =", DEFAULT_NINA_DIR)
# print("N.I.N.A targets dir =", DEFAULT_TARGETS_DIR)



class TargetData:
    """Holds data to update N.I.N.A template"""

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

    verbose  = False        # -v
    targets_only = False    # -t
    prefix_target = False   # -p
    no_output = False       # -n
    add_number = False      # -N


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
        if NINABase.verbose:
            print(indent, "KEYS =", ", ".join(obj.keys()))

        if func:
            func(self, obj, indent + ">", param)

        for k, val in obj.items():
            if k=="$id" or k=="$type" or k=="$ref" or k=="Name":
                if NINABase.verbose:
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
            obj[key] = str(self.id_prefix*1000 + int(obj[key]))


    def process_provider(self, obj, indent, dict):
        # search for Provider {...} and changed additional occurences to reference
        if NINABase.verbose:
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
                    # 1st time occurence, don't touch
                    dict[type] = id
        if NINABase.verbose:
            self.print_attr(obj, "SelectedProvider", "")


    def print_attr(self, obj, name, indent):
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
        # instance variables created by process_data(), referencing the inner containers
        # [0] Preparation (Slew, AF, WaitForTime)
        # [1] Exposure loop
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


    def process_data(self):
        self.name = self.obj["Name"]
        if NINABase.verbose:
            print("NINATarget(process_data):", "name =", self.name)

        self.target = self.obj["Target"]
        self.__process_target()
        
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
        # self.__process_container_0()
        # self.__process_container_1()
        self.__process_container_list()


    def __process_target(self):
        # NEW TARGET --> target["TargetName"]
        self.targetname = self.target["TargetName"]
        self.coord      = self.target["InputCoordinates"]

        ra_hh = self.coord["RAHours"]
        ra_mm = self.coord["RAMinutes"]
        ra_ss = self.coord["RASeconds"]
        #dec_neg = self.coord["NegativeDec"]
        dec_dd = self.coord["DecDegrees"]
        dec_mm = self.coord["DecMinutes"]
        dec_ss = self.coord["DecSeconds"]


    def __process_container_list(self):
        for container in self.container_items + self.container_conditions + self.container_triggers:
            for item in container:
                print(item)
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


    def add_parent(self, id):
        if NINABase.verbose:
            print("NINATarget(add_parent):", "id =", id)

        self.obj["Parent"] = { "$ref": id }


    def set_expanded(self, flag):
        if NINABase.verbose:
            print("NINATarget(set_expanded):", "flag =", flag)

        self.obj["IsExpanded"] = flag


    def get_waitfortime_provider(self):
        return self.waitfortime["SelectedProvider"]["$id"]
    
    def set_waitfortime_provider(self, id):
        if NINABase.verbose:
            print("NINATarget(set_waitfortime_provider):", "id =", id)
        self.waitfortime["SelectedProvider"] = { "$ref": id }


    def get_timecondition_provider(self):
        return self.timecondition["SelectedProvider"]["$id"]
    
    def set_timecondition_provider(self, id):
        if NINABase.verbose:
            print("NINATarget(set_timecondition_provider):", "id =", id)
        self.timecondition["SelectedProvider"] = { "$ref": id }




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

        self.provider_dict = {}

        NINABase.__init__(self)


    def process_data(self):
        self.name = self.obj["Name"]
        if NINABase.verbose:
            print("NINASequence(process_data):", "name =", self.name)

        items = self.obj["Items"]["$values"]
        self.area_list = items
        if NINABase.verbose:
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
        if NINABase.verbose:
            print("id =", self.start_id, "start =", self.start_list)
            print("id =", self.targets_id, "targets =", self.targets_list)
            print("id =", self.end_id, "end =", self.end_list)


    def append_target(self, target):
        if NINABase.verbose:
            print("NINASequence(append_target):", "name =", target.name)

        self.targets_list.append(target.obj)


    def process_csv(self, target_tmpl, file, destdir):
        tz_NA = datetime.timezone(datetime.timedelta(hours=2, minutes=0))
        waitfortime_provider = None
        timecondition_provider = None

        with open(file, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Object"]=="Azelfafage" or row["RA"]=="":
                    continue

                seq = int(row["#"])
                target = row["Object"]
                time_utc = datetime.datetime.fromisoformat(row["Observation date"].replace(" ", "-") + "T" + 
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

                name = "{} {:03d} {}".format(time_NA.date(), seq, target).replace("/", "").replace(":", "")
                # 
                if NINABase.add_number:
                    name += " (n{:03d})".format(number)
                # use target sequence titel as the target name (FITS header!), too
                if NINABase.prefix_target:
                    target = name

                print("NINASequence(process_csv):", "#{:03d} target={} RA={} DEC={}".format(seq, target, ra, dec))
                print("NINASequence(process_csv):", "     UT={} / local {} {}".format(time_utc, time_NA.date(), time_NA.time()))
                print("NINASequence(process_csv):", "     {:d}x{:.1f}s filter={}".format(number, exp, filter))

                # default for filter and binning
                data = TargetData(name, target, ra, dec, time_NA.time(), number, exp, filter)

                # create deep copy of target object, update with data read from CSV
                target_new = copy.deepcopy(target_tmpl)
                target_new.update_target_data(data)

                ### write separate targets
                if NINABase.targets_only:
                    output_path = destdir + "/" + name + ".json"
                    if not NINABase.no_output:
                        print("NINASequence(process_csv):", "writing JSON target", output_path)
                        target_new.write_json(output_path)

                ### append to main sequence targets
                else:
                    # the following changes are necessary to append target_new to the list of the target area
                    target_new.set_prefix(seq)
                    target_new.traverse(NINABase.add_prefix_to_id)
                    # add parent ref to target object
                    target_new.add_parent(self.targets_id)
                    # collapse view
                    target_new.set_expanded(False)
                    # update SelectedProvider references
                    # if waitfortime_provider:
                    #     target_new.set_waitfortime_provider(waitfortime_provider)
                    # else:
                    #     waitfortime_provider = target_new.get_waitfortime_provider()
                    # if timecondition_provider:
                    #     target_new.set_timecondition_provider(timecondition_provider)
                    # else:
                    #     timecondition_provider = target_new.get_timecondition_provider()

                    self.append_target(target_new)

                ##DELETE ME##
                ##break
        # Process Provider {...}
        print("processing SelectedProvider{...}")
        self.traverse(NINABase.process_provider, self.provider_dict)


def main(argv):
    arg = argparse.ArgumentParser(
        prog        = "nina-create-sequence",
        description = "Create/populate multiple N.I.N.A target templates/complete sequence with data from NEO Planner CSV",
        epilog      = "Version: " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-T", "--target-template", help="base N.I.N.A target template .json file")
    arg.add_argument("-S", "--sequence-template", help="base N.I.N.A sequence .json file")
    arg.add_argument("-D", "--destination-dir", help="output dir for created targets/sequence")
    arg.add_argument("-o", "--output", help="output .json file, default NEO-YYYY-MM-DD")
    arg.add_argument("-t", "--targets-only", action="store_true", help="create separate targets only")
    arg.add_argument("-p", "--prefix-target", action="store_true", help="prefix all target names with YYYY-MM-DD NNN")
    arg.add_argument("-n", "--no-output", action="store_true", help="dry run, don't create output files")
    arg.add_argument("-N", "--add-number", action="store_true", help="add number of frames (nNNN) to target name")
    arg.add_argument("filename", nargs="+", help="CSV target data list")
   
    args = arg.parse_args()

    NINABase.verbose = args.verbose
    NINABase.targets_only = args.targets_only
    NINABase.prefix_target = args.prefix_target
    NINABase.no_output = args.no_output
    NINABase.add_number = args.add_number

    if args.target_template:
        target_template = args.target_template
    else:
        target_template = DEFAULT_TARGET
    print(arg.prog+":", "processing target template", target_template)
    if args.sequence_template:
        sequence_template = args.sequence_template
    else:
        sequence_template = DEFAULT_TEMPLATE
    print(arg.prog+":", "processing sequence template", sequence_template)
    if args.destination_dir:
        destination_dir = args.destination_dir
    else:
        destination_dir = DEFAULT_TARGETS_DIR if NINABase.targets_only else DEFAULT_NINA_DIR
    print(arg.prog+":", "destination directory", destination_dir)
    if args.output:
        output = args.output
    else:
        output = "NEO-" + str(datetime.date.today()) + ".json"
    print(arg.prog+":", "output file", output)

    target = NINATarget()
    target.read_json(target_template)
    target.process_data()

    sequence = NINASequence()
    sequence.read_json(sequence_template)
    sequence.process_data()


    for f in args.filename:
        print(arg.prog+":", "processing CSV file", f)
        sequence.process_csv(target, f, destination_dir)

    if not NINABase.targets_only:
        output_path = destination_dir + "/" + output
        if not NINABase.no_output:
            print(arg.prog+":", "writing JSON sequence", output_path)
            sequence.write_json(output_path)


   
   
if __name__ == "__main__":
   main(sys.argv[1:])
