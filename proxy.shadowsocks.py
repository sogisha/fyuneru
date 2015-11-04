# -*- coding: utf-8 -*-

import argparse
import os
import sys
from select import select
import socket
import signal
import time
import logging
from logging import info, debug, warning, error

from fyuneru.ipc.client import InternalSocketClient
from fyuneru.util.droproot import dropRoot
from fyuneru.util.procmgr import ProcessManager
from fyuneru.util.debug import configLoggingModule
from fyuneru.ipc.url import IPCServerURL

ENCRYPTION_METHOD = 'aes-256-cfb'

##############################################################################

# ----------- parse arguments

parser = argparse.ArgumentParser()

parser.add_argument("IPC_SERVER_URL", type=str)
parser.add_argument("--debug", action="store_true", default=False)

"""
# drop privilege to ...
parser.add_argument("--uidname", metavar="UID_NAME", type=str, required=True)
parser.add_argument("--gidname", metavar="GID_NAME", type=str, required=True)

# mode for this script to run
parser.add_argument(\
    "--mode",
    type=str,
    choices=["server", "client"],
    required=True
)

# use the binary executable specified
parser.add_argument("--bin", type=str, default="/usr/local/bin/ss-tunnel")
# following -? arguments are for process `sslocal`
parser.add_argument("-k", type=str, help="Encryption key.")
parser.add_argument(\
    "-s",
    type=str
)
parser.add_argument("-p", type=int, help="Server port.")
parser.add_argument("-l", type=int, help="Local UDP tunnel entry port.")
# UDP Ports regarding the core process
parser.add_argument(\
    "FORWARD_TO",
    type=int
)
"""

args = parser.parse_args()

##############################################################################

configLoggingModule(args.debug)

##############################################################################

# use command line to initialize IPC client

ipc = InternalSocketClient(args.IPC_SERVER_URL)

queried = False

def queryFiller(packet):
    global ipc 
    packet.question = 'init'
    packet.arguments = {"name": ipc.name}
    return True

def infoReader(packet):
    global queried
    try:
        title = packet.title
        if title != 'init': return
        queried = True
    except:
        pass
ipc.onInfo(infoReader)

info("Initializing shadowsocks proxy. Waiting for configuration.")
i = 0
while i < 5:
    ipc.doQuery(queryFiller)
    r = select([ipc], [], [], 1.0)[0]
    i += 1
    if len(r) < 1: continue
    ipc.receive()
    if queried: break

if not queried:
    error("Configuration timed out. Exit.")
    ipc.close()
    sys.exit(1)

print "********************************"
ipc.close()
exit()

##############################################################################

dropRoot(args.uidname, args.gidname)

##############################################################################

# start shadowsocks process

procmgr = ProcessManager()

if 'client' == args.mode: # CLIENT mode
    sscmd = [
        args.bin,                                       # shadowsocks-libev
        '-U',                                           # UDP relay only
        '-L', "127.0.0.1:%d" % (args.FORWARD_TO),       # destinating UDP addr
        '-k', args.k,                                   # key
        '-s', args.s,                                   # server host
        '-p', str(args.p),                              # server port
        '-b', "127.0.0.1",                              # local addr
        '-l', str(args.l),                              # local port
        '-m', ENCRYPTION_METHOD,                        # encryption method
    ]
else: # SERVER mode
    sscmd = [
        args.bin,                                       # shadowsocks-libev
        '-U',                                           # UDP relay only
        '-k', args.k,                                   # key
        '-s', args.s,                                   # server host
        '-p', str(args.p),                              # server port
        '-m', ENCRYPTION_METHOD,                        # encryption method
    ]

procmgr.new('shadowsocks', sscmd)
    

##############################################################################

localSocket = InternalSocketClient() 
proxySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if 'server' == args.mode:
    proxySocket.bind(('127.0.0.1', args.FORWARD_TO))
    proxyPeer = None                  # not knowing where to send data back
else:
    proxyPeer = ('127.0.0.1', args.l) # send to local tunnel entrance

##############################################################################

def doExit(signum, frame):
    global localSocket, proxySocket, procmgr
    try:
        localSocket.close()
    except:
        pass
    try:
        proxySocket.close()
    except:
        pass
    try:
        procmgr.killall()
    except:
        pass
    info("Exit now.")
    exit()
signal.signal(signal.SIGTERM, doExit)

##############################################################################

while True:
    try:
        localSocket.heartbeat()

        selected = select([localSocket, proxySocket], [], [], 1.0)
        if len(selected) < 1:
            continue
        readables = selected[0]

        for each in readables:
            if each == localSocket:
                buf = localSocket.receive()
                if None == buf: continue
                if None == proxyPeer: continue
                debug("Received %d bytes, sending to tunnel." % len(buf))
                proxySocket.sendto(buf, proxyPeer)
            
            if each == proxySocket:
                buf, sender = each.recvfrom(65536)
                proxyPeer = sender
                debug("Received %d bytes, sending back to core." % len(buf))
                localSocket.send(buf)

        if localSocket.broken: doExit(None, None)
    except KeyboardInterrupt:
        doExit(None, None)
