#!/usr/bin/env python 
# -*- coding: utf-8 -*-

import argparse
import json
import os
import signal
import subprocess
import sys

from fyuneru.procmgr import ProcessManager 
from fyuneru.config import Configuration


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

coreCommand = config.getCoreCommand(MODE, debug=bool(args.debug))

proxyCommands = []
for proxyName in config.listProxies():
    proxyCommands.append(config.getProxyConfig(proxyName).getInitCommand(MODE))

##############################################################################

processes = ProcessManager()

try:
    # ---------- start core
    
    print "Start core process..."
    print " ".join(coreCommand)
    processes.new('core', coreCommand)

    # ---------- start proxies

    print "Starting proxy process..."
    processProxies = []
    for cmd in proxyCommands:
        print " ".join(cmd)
        processProxies.append(subprocess.Popen(cmd))

    # ---------- deal with exiting and cleaning

    def doExit(signum, frame):
        global processCore, processProxies
        print "Exit now."
        try:
            processCore.terminate()
        except:
            pass
        for each in processProxies:
            try:
                each.terminate()
            except:
                pass
        exit()
    signal.signal(signal.SIGTERM, doExit)
    signal.signal(signal.SIGINT, doExit)

    # ---------- wait for the core process

    processCore.wait()

except Exception,e:
    print e
    pass

finally:
    doExit(None, None)
