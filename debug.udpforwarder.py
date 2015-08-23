#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import socket
from select import select
import time

parser = argparse.ArgumentParser()
parser.add_argument('LOCALPORT', type=int)
parser.add_argument('REMOTEADDR', type=str)
parser.add_argument('REMOTEPORT', type=int)
args = parser.parse_args()

LOCALPORT, REMOTEADDR, REMOTEPORT =\
    args.LOCALPORT, args.REMOTEADDR, args.REMOTEPORT
LOCALADDR = "127.0.0.1"

sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

readyLocal, readyRemote = False, False

UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

while not (readyLocal and readyRemote):
    readable, writeable = select([sck], [sck], [])[:2]
    if len(readable) > 0:
        buf, sender = sck.recvfrom(65536)
        if sender == (REMOTEADDR, REMOTEPORT):
            readyRemote = True
        elif sender[1] == LOCALPORT:
            readyLocal = True
    if len(writeable) > 0:
        if not readyLocal:
            print "Trying to connect local port..."
            sck.sendto(UDPCONNECTOR_WORD, (LOCALADDR, LOCALPORT))
        if not readyRemote:
            print "Trying to connect Remote port..."
            sck.sendto(UDPCONNECTOR_WORD, (REMOTEADDR, REMOTEPORT))
        time.sleep(1)

while True:
    buf, sender = sck.recvfrom(65536)
    forwardTo = False
    if sender[0] == REMOTEADDR:
        forwardTo = (LOCALADDR, LOCALPORT)
    elif sender[1] == LOCALPORT:
        forwardTo = (REMOTEADDR, REMOTEPORT)

    if forwardTo:
        sck.sendto(buf, forwardTo)
