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
# Version 0.1 / 2023-07-07
#       Added to repository asto
# Version 0.2 / 2023-10-10
#       Allow VdS-style filename, new exposure time option
# Version 0.3 / 2023-12-18
#       Refactored, output for Astrobin CSV
# Version 0.4 / 2024-02-08
#       Get settings from JSON config, -D --extra-data option removed,
#       output calibration data also for text output
# Version 0.5 / 2024-06-18
#       New option --calibration-set to select calibration data set from JSON config
#       New option -d --debug
#       Support OBJECT_YYYY-MM-DD subdirs

import os
import argparse
import re
import csv

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()

# Local modules
from verbose import verbose, error
from jsonconfig import JSONConfig, config


VERSION = "0.5 / 2024-06-18"
AUTHOR  = "Martin Junius"
NAME    = "astro-countsubs"


global FILTER, EXPOSURE
FILTER = ["L", "R", "G", "B", "Ha", "OIII", "SII"]
EXPOSURE = None

# ASTROBIN_FIELDS = [ "date", "filter", "number", "duration", "binning", "gain", "sensorCooling", "fNumber", 
#                    "darks", "flats", "flatDarks", "bias", "bortle", "meanSqm", "meanFwhm", "temperature"  ]
ASTROBIN_FIELDS = [ "date", "filter", "number", "duration", "binning", "gain", "sensorCooling", "fNumber", 
                   "darks", "flats", "flatDarks", "bias", "bortle"  ]



KEY_FILTER_SETS = "filter sets"
KEY_CALIBRATION_SETS = "calibration sets"
KEY_SETTINGS = "settings"


# Read config with filter sets and calibration frames
class AstroConfig(JSONConfig):
    def __init__(self, file=None):
        super().__init__(file)


    def get_filter_id(self, filter_set, filter):
        obj = self.get_json()
        if KEY_FILTER_SETS in obj:
            sets = obj[KEY_FILTER_SETS]
            if filter_set in sets:
                return sets[filter_set][filter]
            else:
                error(f"unknown filter set \"{filter_set}\"")
        else:
            error(f"no key \"{KEY_FILTER_SETS}\" in config")


    def get_calibration(self, calibration_set, mastertype, param="*"):
        obj = self.get_json()
        if KEY_CALIBRATION_SETS in obj:
            sets = obj[KEY_CALIBRATION_SETS]
            if calibration_set in sets:
                cal = sets[calibration_set]
                if mastertype in cal:
                    return cal[mastertype][param]
                else:
                    ##FIXME: warning()
                    verbose(f"unknown mastertype \"{mastertype}\"")
                    return ""
            else:
                error(f"unknown calibration set \"{calibration_set}\"")
        else:
            error(f"no key \"{KEY_CALIBRATION_SETS}\" in config")


    def get_calibration1(self, calibration_set, mastertype):
        """ get first item from mastertype dict """
        obj = self.get_json()
        if KEY_CALIBRATION_SETS in obj:
            sets = obj[KEY_CALIBRATION_SETS]
            if calibration_set in sets:
                cal = sets[calibration_set]
                if mastertype in cal:
                    kw = cal[mastertype]
                    for param, n in kw.items():
                        return (param, n)
                else:
                    return (False, False)
            else:
                error(f"unknown calibration set \"{calibration_set}\"")
        else:
            error(f"no key \"{KEY_CALIBRATION_SETS}\" in config")


    def get_settings(self, calibration_set):
        obj = self.get_json()
        if not KEY_CALIBRATION_SETS in obj:
            error(f"no key \"{KEY_CALIBRATION_SETS}\" in config")
        sets = obj[KEY_CALIBRATION_SETS]
        if calibration_set in sets:
            cal = sets[calibration_set]
        if not KEY_SETTINGS in cal:
            error(f"no key \"{KEY_SETTINGS}\" in config")

        return cal[KEY_SETTINGS]


    def get_setting(self, calibration_set, key):
        settings = self.get_settings(calibration_set)
        if key in settings:
            return settings[key]
        else:
            return ""



# Get config with filter sets and calibration frames
config = AstroConfig("astro-countsubs-config.json")


# CSV output
class CSVOutput:
    enabled = False
    output = None
    filter_set = None
    calibration_set = None

    obj_cache = []
    fields = ASTROBIN_FIELDS

    def append_csv(obj):
        CSVOutput.obj_cache.append(obj)

    def set_csv_fields(fields):
        CSVOutput.fields = fields

    def write_csv(file):
        with open(file, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            if CSVOutput.fields:
                writer.writerow(CSVOutput.fields)
            writer.writerows(CSVOutput.obj_cache)



def walk_the_dir(dir):
    exposures = {}

    if not os.path.isdir(dir):
        error(f"no such directory {dir}")

    for dirName, subdirList, fileList in os.walk(dir):
        verbose('Found directory: %s' % dirName)
        # Test for Astro dir ...
        m = re.search(r'[\\/](\d\d\d\d-\d\d-\d\d)[\\/]LIGHT$', dirName)
        if not m:
            m = re.search(r'[\\/](\d\d\d\d-\d\d-\d\d)$', dirName)
        if not m:
            m = re.search(r'[\\/].+_(\d\d\d\d-\d\d-\d\d)$', dirName)
        if m:
            date = m.group(1)
            verbose("  Date:", date)
            exposures[date] = {}
            
            for f in FILTER:
                exposures[date][f] = {}
            
                for fname in fileList:
                    # Test for proper sub name ...
                    match = re.search(r'_(' + f + r')_(\d+)\.00s_', fname)
                    if not match:
                        match = re.search(r'_(' + f + r')_.+_(\d+)\.00s_', fname)
                    if not match:
                        # VdS "Piehler" style
                        match = re.search(r'_(' + f + r')_()\d{4}-\d{2}-\d{2}', fname)
                    if not match:
                        # OSC old naming without filter
                        # eg LIGHT_NGC 6744_2024-06-04_01-30-36__-10.00__G120_O30_300.00s_0000.fits
                        if f == FILTER[0]:
                            match = re.search(r'_()_.+_(\d+)\.00s_', fname)
                    if match:
                        verbose("\t" + fname)
                        time = match.group(2) if match.group(2) else EXPOSURE
                        verbose("\t" + date, f, time)
                        if not time:
                            error(f"time is none or zero for file {fname}")

                        if time in exposures[date][f]:
                            exposures[date][f][time] += 1
                        else:
                            exposures[date][f][time] = 1

    if CSVOutput.enabled:
        csv_list(exposures)
    else:
        print_filter_list(exposures)



def print_filter_list(exp):
    calibration_set = CSVOutput.calibration_set

    total = {}
    darks = {}
    flats = {}
    bias = config.get_calibration(calibration_set, "masterbias")
    (secs, darkflats) = config.get_calibration1(calibration_set, "masterdarkflat")

    for f in FILTER:
        total[f] = {}
        
    for date in exp.keys():
        print(date)

        for f in exp[date].keys():
            if exp[date][f]:
                print(f"   {f}:", end="")

            for time in exp[date][f].keys():
                n = exp[date][f][time]
                time = int(time)
                print(f" {n}x {time}s", end="")

                darks[str(time)+"s"] = config.get_calibration(calibration_set, "masterdark", str(time)+"s")
                flats[f] = config.get_calibration(calibration_set, "masterflat", f)

                if time in total[f]:
                    total[f][time] += n
                else:
                    total[f][time] = n
        print("")

    print("Total")
    for f in total.keys():
        if total[f]:
            print(f"   {f}:", end="")
            for time in total[f].keys():
                n = total[f][time]
                time = int(time) 
                print(f" {n}x {time}s", end="")
    print()

    total1 = 0
    for f in total.keys():
        if total[f]:
            print(f"   {f}:", end="")
            for time in total[f].keys():
                n = total[f][time]
                time = int(time)
                total1 += n * time
                print(f" {n*time}s", end="")
    print()

    hours = int(total1 / 3600)
    mins  = int((total1 - hours*3600) / 60)
    print(f"   {total1}s / {hours:d}h{mins:02d}")

    print("Darks")
    for t, n in darks.items():
        print(f"   {n}x {t}", end="")
    print()
    print("Flats")
    for f, n in flats.items():
        print(f"   {f}: {n}x", end="")
    print()
    if bias:
        print(f"Bias\n   {bias}x")
    if darkflats:
        print(f"Darkflats\n   {darkflats}x {secs}")
    print("Settings")
    for key in ("mode", "gain", "offset", "cooling"):
        print(f"   {key}: {extra(key)}", end="")
    print()
   


def extra(key):
    return config.get_setting(CSVOutput.calibration_set, key)


def csv_list(exp):
    filter_set = CSVOutput.filter_set
    calibration_set = CSVOutput.calibration_set

    # CSV format as required by the Astrobin upload
    # For documentation see https://welcome.astrobin.com/importing-acquisitions-from-csv/
    #
    # Fields:
    # "date", "filter", "number", "duration", "binning", "gain", "sensorCooling", "fNumber", 
    # "darks", "flats", "flatDarks", "bias", "bortle", "meanSqm", "meanFwhm", "temperature"
    #
    # Not all fields must be present, BUT FIELDS MUST NOT BE EMPTY

    for date in exp.keys():
        for f in exp[date].keys():
            for time in exp[date][f].keys():
                n = exp[date][f][time]
                time = int(time)
                filter = config.get_filter_id(filter_set, f)
                darks = config.get_calibration(calibration_set, "masterdark", str(time)+"s")
                flats = config.get_calibration(calibration_set, "masterflat", f)
                # flatdarks = config.get_calibration("masterflatdark", f)
                bias = config.get_calibration(calibration_set, "masterbias")
                # fields = [  date, filter, n, time, 
                #             extra("binning"), extra("gain"), extra("cooling"), extra("fnumber"),
                #             darks, flats, 0, bias,
                #             extra("bortle"), extra("sqm"), extra("fwhm"), extra("temperature") ]
                fields = [  date, filter, n, time, 
                            extra("binning"), extra("gain"), extra("cooling"), extra("fnumber"),
                            darks, flats, 0, bias,
                            extra("bortle") ]
                verbose(",".join(map(str, fields)))
                CSVOutput.append_csv(fields)

    if CSVOutput.output:
        CSVOutput.write_csv(CSVOutput.output)

   
   
def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Traverse directory and count N.I.N.A subs",
        epilog      = "Version: " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-x", "--exclude", help="exclude filter, e.g. Ha,SII")
    arg.add_argument("-f", "--filter", help="filter list, e.g. L,R,G.B")
    arg.add_argument("-t", "--exposure-time", help="exposure time (sec) if not present in filename")
    arg.add_argument("-C", "--csv", action="store_true", help="output CSV list")
    arg.add_argument("-o", "--output", help="write to file OUTPUT")
    arg.add_argument("-F", "--filter-set", help="name of filter set for Astrobin CSV (see config)")
    arg.add_argument("--calibration-set", help="name of calibration set")
    arg.add_argument("dirname", help="directory name")

    args  = arg.parse_args()

    verbose.set_prog(NAME)
    if args.verbose:
        verbose.enable()
    if args.debug:
        ic.enable()

    global FILTER, EXPOSURE
    EXPOSURE = args.exposure_time

    if args.exclude:
        exclude = args.exclude.split(",")
        filter1 = [x for x in FILTER if x not in exclude]
        FILTER  = filter1

    if args.filter:
        FILTER  = args.filter.split(",")

    verbose("filter =", FILTER)

    CSVOutput.enabled = args.csv
    CSVOutput.output  = args.output
    CSVOutput.filter_set = args.filter_set
    CSVOutput.calibration_set = args.calibration_set

    # quick hack: Windows PowerShell adds a stray " to the end of dirname if it ends with a backslash \ AND contains a space!!!
    # see here https://bugs.python.org/issue39845
    walk_the_dir(args.dirname.rstrip("\""))



if __name__ == "__main__":
    main()