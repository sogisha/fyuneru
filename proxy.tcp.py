# -*- coding: utf-8 -*-

"""
UDP over TCP proxy for Fyuneru.
"""

import argparse
import os
from select import select
import socket
import signal
import time
import logging
from logging import info, debug, warning, error

from fyuneru.ipc.client import InternalSocketClient
from fyuneru.util.droproot import dropRoot
from fyuneru.util.debug import configLoggingModule

##############################################################################

# ----------- parse arguments

parser = argparse.ArgumentParser()

# if enable debug mode
parser.add_argument("--debug", action="store_true", default=False)

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

args = parser.parse_args()

##############################################################################

configLoggingModule(args.debug)

##############################################################################

dropRoot(args.uidname, args.gidname)

##############################################################################

class Datagram2Stream:

    __buffer = ""
    
    def put(self, datagram):
        self.__buffer += datagram.encode('base64').strip() + '\n'

    def get(self, size=32768):
        ret = self.__buffer[:size]
        self.__buffer = self.__buffer[size:]
        return ret

class Stream2Datagram:

    __buffer = ""

    def put(self, buf):
        self.__buffer += buf

    def get(self):
        n = self.__buffer.find('\n')
        if n < 0: return None
        self.__buffer = self.__buffer[n:].strip()
        try:
            ret = self.__buffer[:n].strip().decode('base64')
            return ret
        except:
            return None
    

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
