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

# ChangeLog
# Version 0.1 / 2023-07-07
#       Added to repository asto

global VERSION, AUTHOR
VERSION = "0.1 / 2023-07-07"
AUTHOR  = "Martin Junius"


import os, sys
import argparse
import re


FILTER = ["L", "R", "G", "B", "Ha", "OIII", "SII"]



def main(argv):
   arg = argparse.ArgumentParser(
      prog        = "astro-countsubs",
      description = "Traverse directory and count N.I.N.A subs",
      epilog      = "Version: " + VERSION + " / " + AUTHOR)
   arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
   arg.add_argument("-x", "--exclude", help="exclude filter, e.g. Ha,SII")
   arg.add_argument("-f", "--filter", help="filter list, e.g. L,R,G.B")
   arg.add_argument("dirname", help="directory name")
   
   args  = arg.parse_args()
#   print(args)

   global OPT_V
   global FILTER
   
   OPT_V = args.verbose

   if args.exclude:
      exclude = args.exclude.split(",")
      filter1 = [x for x in FILTER if x not in exclude]
      if OPT_V and filter1: print("filter =", filter1)
      FILTER  = filter1

   if args.filter:
      FILTER  = args.filter.split(",")

   if OPT_V: print("filter =", FILTER)

   # quick hack: Windows PowerShell adds a stray " to the end of dirname if it ends with a backslash \ AND contains a space!!!
   # see here https://bugs.python.org/issue39845
   walk_the_dir(args.dirname.rstrip("\""))



def walk_the_dir(dir):
   rootDir = dir.replace("\\", "/")
   exposures = {}

   for dirName, subdirList, fileList in os.walk(rootDir):
      if OPT_V: print('Found directory: %s' % dirName)
      # Test for Astro dir ...
      m = re.search(r'[\\/](\d\d\d\d-\d\d-\d\d)[\\/]LIGHT$', dirName)
      if m:
         date = m.group(1);
         exposures[date] = {}
         
         for f in FILTER:
            exposures[date][f] = {}
            
            for fname in fileList:
               # Test for proper sub name ...
               match = re.search(r'_(' + f + r')_(\d+)\.00s_', fname)
               if not match:
                  match = re.search(r'_(' + f + r')_.+_(\d+)\.00s_', fname)
               if match:
                  if OPT_V: print('\t%s' % fname)
                  time = match.group(2)
                  if OPT_V: print(date, f, time)

                  if time in exposures[date][f]:
                     exposures[date][f][time] += 1
                  else:
                     exposures[date][f][time] = 1

   print_filter_list(exposures)



def print_filter_list(exp):
   total = {}
   
   for f in FILTER:
      total[f] = {}
      
   for date in exp.keys():
      print(date)

      print("  ", end="")
      for f in exp[date].keys():
         if exp[date][f]:
            print(f + ": ", end="")

            for time in exp[date][f].keys():
               n = exp[date][f][time]
               time = int(time)
               print("%dx %ds   " % (n, time), end="")

               if time in total[f]:
                  total[f][time] += n
               else:
                  total[f][time] = n
      print("")

   print("Total")
   print("  ", end="")
   for f in total.keys():
      if total[f]:
         print(f + ": ", end="")
         for time in total[f].keys():
               n = total[f][time]
               time = int(time)
               print("%dx %ds   " % (n, time), end="")
   print("")

   total1 = 0
   print("  ", end="")
   for f in total.keys():
      if total[f]:
         print(f + ": ", end="")
         for time in total[f].keys():
               n = total[f][time]
               time = int(time)
               total1 += n * time
               print("%ds   " % (n * time), end="")
   print("")

   hours = int(total1 / 3600)
   mins  = int((total1 - hours*3600) / 60)
   print("  %ds / %dh%d" % (total1, hours, mins))
   
   
   
   
if __name__ == "__main__":
   main(sys.argv[1:])