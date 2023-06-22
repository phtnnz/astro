#!/usr/bin/python

import sys, getopt
import argparse
import json
import csv
import datetime



class NINATemplate:
    """Holds data read from N.I.N.A JSON template for target"""

    def __init__(self):
        self.obj = None


    def read_json(self, file):
        with open(file, 'r') as f:
            data = json.load(f)
        self.process_data(data)


    def write_json(self, file):
        with open(file, 'w') as f:
            json.dump(self.obj, f, indent = 2)


    def print_attr(self, obj, name, indent):
        if name in obj:
            print(indent, name, "=", obj[name])


    def print_items(self, obj, indent, level):
        if "Items" in obj:
            if OPT_L>0 and level > OPT_L:
                print(indent, "Container with items [...]")
                return

            print("\n" + indent, "Container with items")
            items = obj["Items"]
            self.print_keys(items, indent)
#            self.print_attr(items, "$id", indent+" >")
#            self.print_attr(items, "$type", indent+" >")
            self.print_attr(items, "Name", indent+" >")

            for i, o in enumerate(items["$values"]):
                if OPT_L>0 and level >= OPT_L:
                    print(indent + " > Item", i, "[...]")
                else:
                    print("\n" + indent+" > Item", i)
                    self.print_obj(o, indent+" > >", level+1)


    def print_parent(self, obj, indent):
        pass

    
    def print_keys(self, obj, indent):
#        print(indent, "KEYS =", ", ".join(obj.keys()))
        print(indent, "KEYS:", end="")
        for k, val in obj.items():
            if type(val) is dict:
                print(" {}={{...}}".format(k), end="")
            elif type(val) is str:
                print(" {}=\"{}\"".format(k, val), end="")
            elif type(val) is list:
                print(" {}=[...]".format(k), end="")
            else:
                print(" {}={}".format(k, val), end="")
        print("")
        

    def print_obj(self, obj, indent, level):
        if OPT_L>0 and level > OPT_L:
            return

        self.print_keys(obj, indent)
#        self.print_attr(obj, "$id", indent)
#        self.print_attr(obj, "$type", indent)
        self.print_attr(obj, "Name", indent)
        self.print_items(obj, indent, level+1)
        self.print_parent(obj, indent)


    def process_data(self, obj):
        self.obj = obj

        self.print_obj(obj, ">", 1)
        return
    
        # NEW NAME --> obj["Name"]
        self.name = self.obj["Name"]
        print("NINATargetTemplate(process_data):", "name =", self.name)

        self.target = self.obj["Target"]
        self.process_target()
        
        items = self.obj["Items"]
#        print_container(self.items, ">")

        for i in items["$values"]:
#      print("type =", item1["$type"])
            if "Name" in i:
#         print("  name =", item1["Name"])
                if i["Name"].startswith("CONTAINER START"):
                    self.start = i["Items"]
                if i["Name"].startswith("CONTAINER IMAGING"):
                    self.imaging = i["Items"]
        self.process_start()
        self.process_imaging()


    def process_target(self):
        # NEW TARGET --> target["TargetName"]
        self.targetname = self.target["TargetName"]
        print("NINATargetTemplate(process_target):", "targetname =", self.targetname)
        self.coord      = self.target["InputCoordinates"]

        # NEW COORD --> coord["..."]
        ra_hh = self.coord["RAHours"]
        ra_mm = self.coord["RAMinutes"]
        ra_ss = self.coord["RASeconds"]
        #dec_neg = self.coord["NegativeDec"]
        dec_dd = self.coord["DecDegrees"]
        dec_mm = self.coord["DecMinutes"]
        dec_ss = self.coord["DecSeconds"]

        ra  = "{:02d}:{:02d}:{:04.1f}".format(ra_hh, ra_mm, ra_ss)
        dec = "{:02d}:{:02d}:{:04.1f}".format(dec_dd, dec_mm, dec_ss)
        print("NINATargetTemplate(process_target):", "RA =", ra, ", DEC =", dec)


    def process_start(self):
        for i in self.start["$values"]:
#      print(indent, "type =", i["$type"])
            if "WaitForTime" in i["$type"]:
                # NEW TIME --> waitfortime["..."]
                self.waitfortime = i
                time_hh = i["Hours"]
                time_mm = i["Minutes"]
                time_ss = i["Seconds"]
                time = "{:02}:{:02}:{:02}".format(time_hh, time_mm, time_ss)
                print("NINATargetTemplate(process_start):", "WaitForTime =", time)


    def process_imaging(self):
        for i in self.imaging["$values"]:
#      print(indent, "type =", i["$type"])
            if "SmartExposure" in i["$type"]:
                # NEW NUMBER OF EXPOSURES --> conditions0["Iterations"]
                self.conditions0 = i["Conditions"]["$values"][0]
                print("NINATargetTemplate(process_imaging):", "number =", self.conditions0["Iterations"])

                items = i["Items"]
                for i2 in items["$values"]:
                    if "SwitchFilter" in i2["$type"]:
                        # NEW FILTER --> filter["_name"]
                        self.filter = i2["Filter"]
                        print("NINATargetTemplate(process_imaging):", "filter =", self.filter["_name"])
                    if "TakeExposure"  in i2["$type"]:
                        # NEW EXPOSURETIME --> exposure["ExposureTime"]
                        # NEW BINNING --> exposure["Binning"]["X|Y"]
                        self.exposure = i2
                        binning  = "{}x{}".format(i2["Binning"]["X"], i2["Binning"]["X"])
                        print("NINATargetTemplate(process_imaging):", "exposure =", self.exposure["ExposureTime"], ", binning =", binning)




def main(argv):
    arg = argparse.ArgumentParser(
        prog        = "nina-json-analyzer",
        description = "Analyze/print/debug N.I.N.A JSON templates",
        epilog      = "")
    arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
    arg.add_argument("-l", "--level", type=int, help="limit recursion depth")
    arg.add_argument("filename", nargs="+", help="JSON file")
   
    args = arg.parse_args()
#    print(args)

    global OPT_V
    OPT_V = args.verbose
    global OPT_L
    OPT_L = args.level if args.level else 0

    nina = NINATemplate()

    for f in args.filename:
        print(arg.prog+":", "processing JSON file", f)
        nina.read_json(f)

   
   
if __name__ == "__main__":
   main(sys.argv[1:])
