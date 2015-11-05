#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
from select import select
import signal
import sys
import logging
from logging import info, debug, warning, error, exception, critical
import time

from fyuneru.net.vnet import VirtualNetworkInterface
from fyuneru.util.config import Configuration
from fyuneru.util.debug import showPacket, showIPCReport, configLoggingModule
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

# register answer functions with ipc.onQuery(question, func), providing
# services for IPC client to get its necessary information

def ipcOnQueryInit(argv, answer):
    global config, MODE
    try:
        proxyName = argv["name"]
        proxyConfig = config.getProxyConfig(proxyName)
        answer.title = 'init' 

        answer.uid = config.user[0]
        answer.gid = config.user[1]
        answer.config = proxyConfig
        answer.key = config.key
        answer.mode = MODE
    except Exception,e:
        exception(e)
        error("We cannot answer an init query.")
        return False
    return True
ipc.onQuery('init', ipcOnQueryInit)

# ---------- initialize proxy processes

for proxyName in config.listProxies():
    proxyCommand = config.getProxyInitParameters(proxyName, ipc, args.debug)
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
    for each in reads: each.close()
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


ipcLastReport = time.time() 

while True:
    try:
        now = time.time()

        # ---------- output IPC report

        if now - ipcLastReport > 15.0:
            ipcLastReport = now
            debug(showIPCReport(ipc.report()))
        
        # ---------- deal with I/O things
        
        readables = select(reads, [], [], 5.0)[0]
        for each in readables:
            if each == tun:
                # ---------- forward packets came from tun0
                ipPacket = each.read(65536) # each.read(each.mtu)
                # pack buf with timestamp
                packet = DataPacket()
                packet.data = str(ipPacket) 
                # encrypt and sign buf
                ipc.send(str(packet))
                debug(showPacket(ipPacket))

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
