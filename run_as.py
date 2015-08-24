#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import json
import os
import signal
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

if MODE == 's':
    UDP_PORTS = SERVER_UDP_PORTS
    ROLE = 'server'
else:
    UDP_PORTS = CLIENT_UDP_PORTS
    ROLE = 'client'

# ---------- core command

coreCommand = [\
    'python', 'tunnel.py',
    '--role', ROLE, 
    '--server-ip', SERVER_VIRTUAL_IP,
    '--client-ip', CLIENT_VIRTUAL_IP,
    '--key', KEY,
]
coreCommand += [str(i) for i in UDP_PORTS]

# ---------- proxy commands

proxyCommands = []
proxyConfig = config["proxies"]

if proxyConfig.has_key("websocket"):
    proxyCommandWebsocket = ['node']
    if MODE == 's':
        proxyCommandWebsocket += [
            './proxies/websocket/server.js', 
            str(proxyConfig["websocket"]["server"]["webport"]),
        ]
        proxyCommandWebsocket += \
            [str(i) for i in proxyConfig["websocket"]["server"]["coreports"]]
    else:
        proxyCommandWebsocket += [
            './proxies/websocket/client.js', 
            "%s:%s" % (
                str(proxyConfig["websocket"]["server"]["ip"]),
                str(proxyConfig["websocket"]["server"]["webport"]),
            ),
        ]
        proxyCommandWebsocket += \
            [str(i) for i in proxyConfig["websocket"]["client"]["coreports"]]
    proxyCommands.append(proxyCommandWebsocket)

##############################################################################

processCore = subprocess.Popen(coreCommand)

# ---------- now open proxies

processProxies = []
for cmd in proxyCommands:
    processProxies.append(subprocess.Popen(cmd))

# ---------- deal with exiting and cleaning

def doExit(signum, frame):
    global processCore, processProxies
    print "Exit now."
    processCore.terminate()
    for each in processProxies:
        each.terminate()
    exit()
signal.signal(signal.SIGTERM, doExit)
signal.signal(signal.SIGINT, doExit)

processCore.wait()
doExit(None, None)
