#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import json
import logging
from logging import info, debug, warning, error, critical
import os
import signal
import subprocess
import sys

from fyuneru.procmgr import ProcessManager 
from fyuneru.config import Configuration
from fyuneru.droproot import dropRoot


logging.basicConfig(level=logging.INFO)



parser = argparse.ArgumentParser(description="""
    This is the initator of Fyeneru proxy. Before running, put a `config.json`
    in the same path as this file.
    Requires root priviledge for running this script.
""")
parser.add_argument(\
    "--debug",
    action="store_true",
    default=False,
    help = "Print debug info, e.g. packet data."
)
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

config = Configuration(open(os.path.join(PATH, 'config.json'), 'r').read())

coreCommand = config.getCoreCommand(\
    MODE,
    config.user,
    debug=bool(args.debug)
)

proxyCommands = {} 
for proxyName in config.listProxies():
    proxyCommands[proxyName] = \
        config.getProxyConfig(proxyName).getInitCommand(MODE)

##############################################################################

processes = ProcessManager()

def doExit(signum, frame):
    global processes 
    t = 1.0 # second(s) waiting for exit
    try:
        processes.killall(t)
        info("Exiting. Wait %f seconds for child processes to exit." % t)
    except Exception,e:
        error("Exiting, error: %s" % e)
    info("Good bye.")
    sys.exit()
signal.signal(signal.SIGTERM, doExit)
signal.signal(signal.SIGINT, doExit)

try:

    # ---------- start core

    info("Start core process...")
    debug(" ".join(coreCommand))
    processes.new('core', coreCommand)

    # ---------- start proxies

    info("Starting proxy process...")
    processProxies = []
    for proxyName in proxyCommands:
        proxyCommand = proxyCommands[proxyName]
        debug(" ".join(proxyCommand))
        processes.new(proxyName, proxyCommand)

    # ---------- drop root

    dropRoot(*config.user)

    # ---------- wait for the core process

    processes.wait('core')

except KeyboardInterrupt:
    doExit(None, None)

except Exception,e:
    print e
    pass

finally:
    doExit(None, None)
