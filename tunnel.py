#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from select import select
import signal
import socket
from struct import pack, unpack
import random
from time import time

from pytun import TunTapDevice

from fyuneru import config

from _crypto import Crypto
from _debug import showPacket

parser = argparse.ArgumentParser()
parser.add_argument(\
    "--debug",
    action="store_true",
    default=False
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
parser.add_argument(\
    "PORT",
    metavar="PORT",
    type=int,
    nargs="+"
)

args = parser.parse_args()


MTU = 1500 
UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."
UDP_PORTS = args.PORT

##############################################################################

# ---------- config log/debug functions

def log(x):
    print x
if args.debug:
    def debug(x):
        print x
    log("Debug mode entered.")
else:
    debug = lambda x: None

# ---------- config crypto functions

crypto = Crypto(args.key)
encrypt, decrypt = crypto.encrypt, crypto.decrypt

# ---------- config TUN device

tun = TunTapDevice()
if "client" == args.role:
    log("Running as client.")
    tun.addr = args.client_ip #"10.1.0.2"
    tun.dstaddr = args.server_ip #"10.1.0.1"
else:
    log("Running as server.")
    tun.addr = args.server_ip #"10.1.0.1"
    tun.dstaddr = args.client_ip #"10.1.0.2"
tun.netmask = "255.255.255.0"
tun.mtu = MTU
log(\
    """%s: mtu %d  addr %s  netmask %s  dstaddr %s""" % \
    (tun.name, tun.mtu, tun.addr, tun.netmask, tun.dstaddr)
)
tun.up()
log("%s: up now." % tun.name)

# ---------- open UDP sockets

reads = [tun] # for `select` function
peers = []    # stores peers for each UDP port
receivingTimings = [] # latest time of received packet on one UDP port
sendingTimings = []   # latest time of sent packet on one UDP port

for portNum in UDP_PORTS:
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    newSocket.bind(("127.0.0.1", portNum))
    reads.append(newSocket)
    peers.append(False)
    receivingTimings.append(0)
    sendingTimings.append(0)

log("UDP: open ports %s" % ", ".join([str(i) for i in UDP_PORTS]))

# TODO drop root

##############################################################################

def doExit(signum, frame):
    global reads 
    print "Tunnel: exit now."
    for each in reads:
        each.close()
    exit()
signal.signal(signal.SIGTERM, doExit)

while True:
    readables = select(reads, [], [])[0]
    for each in readables:
        if each == tun:
            
            # ---------- forward packets came from tun0
            
            buf = each.read(65536) # each.read(each.mtu)
            # write to socket who have got a peer
            possible = [x for x in xrange(0, len(peers)) if peers[x] != False]
            if len(possible) == 0:
                continue # drop the packet
            i = possible[random.randrange(0, len(possible))]
            workerSocket = reads[i + 1]
            # pack buf with timestamp
            bufTimestamp = time()
            buf = pack('<d', bufTimestamp) + buf
            sendingTimings[i] = bufTimestamp
            # encrypt and sign buf
            workerSocket.sendto(encrypt(buf), peers[i])
            debug("[%f] %s --> [%d]\n%s\n" % (\
                sendingTimings[i],
                tun.name,
                i,
                showPacket(buf)
            ))

        else:
            
            # ---------- receive packets from internet
            
            i = reads.index(each) - 1
            buf, sender = each.recvfrom(65536)
            if buf.strip() == UDPCONNECTOR_WORD:
                # connection word received, answer
                peers[i] = sender
                each.sendto(UDPCONNECTOR_WORD, sender)
                debug("[%d] <==> %s:%d" % (i, sender[0], sender[1]))
                continue

            # not magic word

            if peers[i] != sender:
                continue
            # decrypt buf
            buf = decrypt(buf)
            if buf == False: # if decryption failed
                debug("[%d] --> %s: Bad packet." % (i, tun.name))
                continue
            # unpack buf with timestamp
            if(len(buf) < 8):
                continue
            bufTimestamp = unpack('<d', buf[:8])
            buf = buf[8:]
            receivingTimings[i] = max(receivingTimings[i], bufTimestamp)
            # send buf to network interface
            tun.write(buf)
            debug("[%f]: [%d] --> %s\n%s\n" % (\
                receivingTimings[i],
                i,
                tun.name,
                showPacket(buf)
            ))
