#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
from select import select
import signal
import sys
import logging
from logging import info, debug, warning, error, critical

from fyuneru.net.vnet import VirtualNetworkInterface
from fyuneru.util.config import Configuration
from fyuneru.util.crypto import randint
from fyuneru.util.debug import showPacket, configLoggingModule
from fyuneru.util.droproot import dropRoot
from fyuneru.net.protocol import DataPacket, DataPacketException
from fyuneru.ipc.server import InternalSocketServer
from fyuneru.util.procmgr import ProcessManager

##############################################################################

parser = argparse.ArgumentParser()

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

"""
parser.add_argument(\
    "--debug",
    action="store_true",
    default=False
)
parser.add_argument(\
    "--uidname",
    metavar="UID_NAME",
    type=str,
    required=True
)
parser.add_argument(\
    "--gidname",
    metavar="GID_NAME",
    type=str,
    required=True
)
parser.add_argument(\
    "--parent-pid",
    type=int,
    required=True
)
parser.add_argument(\
    "--role",
    metavar="ROLE",
    type=str,
    choices=["server", "client"],
    default="s",
    required=True
)
parser.add_argument(\
    "--server-ip",
    metavar="SERVER_IP",
    type=str,
    required=True
)
parser.add_argument(\
    "--client-ip",
    metavar="CLIENT_IP",
    type=str,
    required=True
)
parser.add_argument(\
    "--key",
    metavar="KEY",
    type=str,
    required=True
)
"""

args = parser.parse_args()


PATH = os.path.realpath(os.path.dirname(sys.argv[0]))
MODE = args.mode

MTU = 1400 

##############################################################################

# ---------- config log/debug functions

configLoggingModule(args.debug)

# ---------- load and parse configuration file

config = Configuration(open(os.path.join(PATH, 'config.json'), 'r').read())
coreConfig = config.getCoreInitParameters(MODE)

# ---------- initialize IPC and ProcessManager

ipc = InternalSocketServer(coreConfig.key)
processes = ProcessManager()

# ---------- config TUN device and start up

if "client" == args.mode:
    info("Running as client.")
else:
    info("Running as server.")
tun = VirtualNetworkInterface(coreConfig.localIP, coreConfig.remoteIP)
tun.netmask = "255.255.255.0"
tun.mtu = MTU

tun.up()
info("%s: up now." % tun.name)

# ----------- prepare info for IPC clients(part of each proxy process)

    # TODO register answer functions with ipc.onQuery(question, func),
    # providing services for IPC client to get its necessary information

# ---------- initialize proxy processes

for proxyName in config.listProxies():
    proxyCommand = config.getProxyInitParameters(proxyName, ipc)
    processes.new(proxyName, proxyCommand)

# ---------- drop root privileges

dropRoot(coreConfig.uid, coreConfig.gid)

##############################################################################

# register exit function, and start IO loop

reads = [ipc, tun] # for `select` function

def doExit(signum, frame):
    global reads, processes 
    info("Exit now.")
    # first close TUN devices
    for reach in reads: each.close()
    # kill processes
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


while True:
    try:
        parentProc.watch()
        
        # ---------- deal with I/O things
        
        readables = select(reads, [], [], 5.0)[0]
        for each in readables:
            if each == tun:
                # ---------- forward packets came from tun0
                buf = each.read(65536) # each.read(each.mtu)
                # pack buf with timestamp
                packet = DataPacket()
                packet.data = buf
                # encrypt and sign buf
                ipc.send(str(packet))
                debug(showPacket(buf))
            if each == ipc:
                # ---------- receive packets from internet
                buf = each.receive()
                if buf == None:
                    # Received buffer being digested by InternalSocket itself,
                    # either some internal mechanism packet, or packet with
                    # wrong destination, or packet decryption failed...
                    continue

                try:
                    packet = DataPacket(buf)
                except DataPacketException, e:
                    # if failed reading the packet
                    debug("[%d] --> %s: Bad packet - %s" % (i, tun.name, e))
                    continue
                
                # send buf to network interface
                tun.write(packet.data)
                debug(showPacket(packet.data))

        # ---------- deal with tunnel delay timings

        ipc.clean()


    except KeyboardInterrupt:
        doExit(None, None)
