#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import json
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description="""
    This is the initator of Fyeneru proxy. Before running, put a `config.json`
    in the same path as this file.
    Requires root priviledge for running this script.
""")
parser.add_argument(\
    "mode",
    metavar="MODE",
    type=str, 
    choices=['s', 'c'],
    help="""
        Either 'c' or 's', respectively for client mode and server mode.
    """
)
args = parser.parse_args()

PATH = os.path.realpath(os.path.dirname(sys.argv[0]))
MODE = args.mode

##############################################################################

config = json.loads(open(os.path.join(PATH, 'config.json'), 'r').read())

KEY = config["core"]["key"]
CLIENT_VIRTUAL_IP = config["core"]["client"]["ip"]
CLIENT_UDP_PORTS = config["core"]["client"]["ports"]
SERVER_VIRTUAL_IP = config["core"]["server"]["ip"]
SERVER_UDP_PORTS = config["core"]["server"]["ports"]


