#!/usr/bin/python

import sys, getopt
import argparse

print ("argv=", sys.argv)


def main(argv):
   arg = argparse.ArgumentParser(
      prog        = "template",
      description = "Generic python script template",
      epilog      = "Famous last words")
   arg.add_argument("-v", "--verbose", action="store_true", help="debug messages")
   arg.add_argument("-n", "--name", help="example option name")
   arg.add_argument("-i", "--int", type=int, help="example option int")
   arg.add_argument("dirname", help="directory name")
   arg.add_argument("filename", nargs="*", help="filename")
   
   args = arg.parse_args()
   print("args=%s" % args)
   print("args.name=%s" % args.name)
   print("args.dirname=%s" % args.dirname)
   print("args.filename=%s" % args.filename)

   global OPT_V
   OPT_V = args.verbose

   
   
if __name__ == "__main__":
   main(sys.argv[1:])
