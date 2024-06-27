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
# Version 0.0 / 2024-06-27
#       Simple send a message to discord server

import sys
import argparse

# The following libs must be installed with pip
import requests
from icecream import ic
# Disable debugging
ic.disable()
# Local modules
from verbose import verbose, warning, error
from jsonconfig import JSONConfig


VERSION = "0.0 / 2024-06-27"
AUTHOR  = "Martin Junius"
NAME    = "discordmsg"

CHANNEL = "#alerts"
CONFIG  = "discord-config.json"


class DiscordConfig(JSONConfig):
    """ JSON Config for Discord web hooks """

    channel = CHANNEL
    url     = None

    def __init__(self, file=None):
        super().__init__(file)
        self._channel = CHANNEL
        self._url     = None

    def set_channel(self, channel=CHANNEL):
        if "channels" in self.config:
            channels = self.config["channels"]
            self._channel = channel
            self._url     = channels[channel]

    def url(self):
        if not self._url:
            self.set_channel(self._channel)
        return self._url
        
    

config = DiscordConfig(CONFIG)


def discord_set_channel(channel):
    config.set_channel(channel)


def discord_message(msg):
    ic(config)
    url = config.url()
    data = { "content": msg }
    ic(url, data)
    response = requests.post(url, json=data)
    ic(response.status_code)




### Test run as a command line script ###
def main():
    arg = argparse.ArgumentParser(
        prog        = NAME,
        description = "Test sending message to Discord channel",
        epilog      = "Version " + VERSION + " / " + AUTHOR)
    arg.add_argument("-v", "--verbose", action="store_true", help="verbose messages")
    arg.add_argument("-d", "--debug", action="store_true", help="more debug messages")
    arg.add_argument("-C", "--channel", help="channel name to match in JSON config")
    arg.add_argument("message", nargs="+", help="message")

    args = arg.parse_args()

    if args.debug:
        ic.enable()
        ic(sys.version_info)
        ic(args)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()
    # ... more options ...
    if args.channel:
        discord_set_channel(args.channel)
        
    # ... the action starts here ...
    discord_message(" ".join(args.message))


if __name__ == "__main__":
    main()
