#!/usr/bin/env python

# Copyright 2024 Martin Junius
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
# Version 0.1 / 2024-12-27
#       Send AAG status to Discord channel

import sys
import argparse
import json

# The following libs must be installed with pip
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error
from discordmsg import config, discord_message, discord_set_channel

VERSION = "0.1 / 2024-12-27"
AUTHOR  = "Martin Junius"
NAME    = "discord-aag"


AAG_JSON = r'\\aagsolo\AAGSolo\aag_json.dat'


# Command line options
class Options:
    aag_json = config.get_obj("aagsolo").get("aag_json") or AAG_JSON     # -A --aag-json



def aag_to_discord():
    verbose(f"reading AAG status {Options.aag_json}")

    obj = None
    msg_list = []
    msg_list.append('AAG Cloudwatcher Solo') 

    try:
        with open(Options.aag_json, 'r') as f:
            obj = json.load(f)
    except OSError as err:
        msg_list.append(f"  Can't access status: {err}")
        
    ic(obj)
    if obj:
        msg_list.append(f'  Conditions: {"SAFE" if obj["safe"] else "UNSAFE"}')
        msg_list.append(f'  Wind: {obj["wind"]}/{obj["gust"]}')
        msg_list.append(f'  Clouds: {obj["clouds"]}')
        msg_list.append(f'  Light: {obj["light"]}')
        msg_list.append(f'  Rain: {obj["rain"]}')

    ic(msg_list)
    message = "\n".join(msg_list)
    verbose(message)

    discord_message(message)



def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Send AAG status to Discord channel",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-A", "--aag-json", help="path to AAG Cloudwatcher Solo status file")
    arg.add_argument("-C", "--channel", help="channel name to match in JSON discord-config")

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info, sys.path, args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    ic(config.config)

    if args.channel:
        discord_set_channel(args.channel)
    if args.aag_json:
        Options.aag_json = args.aag_json

    aag_to_discord()



if __name__ == "__main__":
    main()
