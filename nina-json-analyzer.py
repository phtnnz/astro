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
        self.obj = data


    def write_json(self, file):
        with open(file, 'w') as f:
            json.dump(self.obj, f, indent = 2)


    def print_attr(self, obj, name, indent):
        if name in obj:
            print(indent, name, "=", obj[name])


    def print_list(self, obj, key, indent, level):
        if key in obj:
            if OPT_L>0 and level > OPT_L:
                print(indent, "Container with ", key, "[...]")
                return

            print("\n" + indent, "Container with", key)
            items = obj[key]
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
        self.print_list(obj, "Items", indent, level+1)
        self.print_list(obj, "Triggers", indent, level+1)
        self.print_list(obj, "Conditions", indent, level+1)
        self.print_parent(obj, indent)


    def process_data(self):
        self.print_obj(self.obj, ">", 1)




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
        nina.process_data()

   
   
if __name__ == "__main__":
   main(sys.argv[1:])
