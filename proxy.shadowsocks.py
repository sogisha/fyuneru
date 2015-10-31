# -*- coding: utf-8 -*-

import argparse
import os
from select import select
import socket
import signal
import time
import logging
from logging import info, debug, warning, error

from fyuneru.net.intsck import InternalSocketClient
from fyuneru.util.droproot import dropRoot
from fyuneru.util.procmgr import ProcessManager, ParentProcessWatcher

ENCRYPTION_METHOD = 'aes-256-cfb'

##############################################################################

# ----------- parse arguments

parser = argparse.ArgumentParser()

# parent pid
parser.add_argument("--parent-pid", type=int, required=True)

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

# socket name
parser.add_argument(\
    "--socket",
    type=str,
    required=True
)

# use the binary executable specified
parser.add_argument("--bin", type=str, default="/usr/local/bin/ss-tunnel")
# following -? arguments are for process `sslocal`
parser.add_argument("-k", type=str, help="Encryption key.")
parser.add_argument(\
    "-s",
    type=str,
    help="""
        Server address. Must be real address when running in SERVER mode, can
        be an address of another tunnel's entry when running in CLIENT mode.
    """)
parser.add_argument("-p", type=int, help="Server port.")
parser.add_argument("-l", type=int, help="Local UDP tunnel entry port.")
# UDP Ports regarding the core process
parser.add_argument(\
    "FORWARD_TO",
    type=int,
    help="""
        UDP tunnel exit port on server. Client's port will be forwarded to
        this one.""")

args = parser.parse_args()

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

localSocket = InternalSocketClient(args.socket) 
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

# start parent process watcher

parentProc = ParentProcessWatcher(args.parent_pid, doExit)

##############################################################################

while True:
    try:
        parentProc.watch()
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
    except KeyboardInterrupt:
        doExit(None, None)
