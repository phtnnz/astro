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
#       Simple send a message to discord server
# Version 0.2 / 2024-12-31
#       Clean-up, typing, docstrings, added get_obj

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


VERSION = "0.2 / 2024-12-31"
AUTHOR  = "Martin Junius"
NAME    = "discordmsg"

CHANNEL = "#alerts"
CONFIG  = "discord-config.json"


class DiscordConfig(JSONConfig):
    """ JSON Config for Discord web hooks """

    def __init__(self, file: str=None):
        """
        Create DiscordConfig object

        :param file: JSON config file name, defaults to None
        :type file: str, optional
        """
        super().__init__(file)
        self._channel = CHANNEL
        self._url     = None

    def set_channel(self, channel: str=CHANNEL):
        """
        Set Discord channel retrieving corresponding Webhook URL

        :param channel: channel name, defaults to "#alerts"
        :type channel: str, optional
        """
        if "channels" in self.config:
            channels = self.config["channels"]
            self._channel = channel
            self._url     = channels.get(channel) or error(f"undefined channel {channel}")

    def url(self) -> str:
        """
        Get Webhook URL for selected Channel

        :return: _description_
        :rtype: str
        """
        if not self._url:
            self.set_channel(self._channel)
        return self._url
    
    def get_obj(self, key: str) -> dict:
        """
        Get JSON object for key from config

        :param key name: _description_
        :type key: str
        :return: JSON object as dict or None
        :rtype: dict
        """
        return self.config.get(key)
    
    

config = DiscordConfig(CONFIG)


def discord_set_channel(channel: str=CHANNEL):
    """
    Set Discord channel for messages

    :param channel: channel name, defaults to "#alerts"
    :type channel: str, optional
    """
    config.set_channel(channel)


def discord_message(msg: str):
    """
    Send Discord message to a channel

    :param msg: message, "\n" for line breaks
    :type msg: str
    """
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
        ic(args)
        ic(sys.version_info, sys.path)
    if args.verbose:
        verbose.set_prog(NAME)
        verbose.enable()

    if args.channel:
        discord_set_channel(args.channel)
        
    discord_message("\n".join(args.message))


if __name__ == "__main__":
    main()
