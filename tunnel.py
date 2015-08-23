#!/usr/bin/env python
# -*- coding: utf-8 -*-
from select import select
import socket
import argparse
import random

from pytun import TunTapDevice

from _config import config
from _crypto import encrypt, decrypt

def log(x):
    print x
if config["DEBUG"]:
    def debug(x):
        print x
else:
    debug = lambda x: None


parser = argparse.ArgumentParser()
parser.add_argument(\
    "role",
    metavar="ROLE",
    type=str,
    choices=["s", "c"],
    default="s"
)
args = parser.parse_args()
tun = TunTapDevice()

MTU = 1000 
UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

##############################################################################

UDP_PORT_BASE = None

if "c" == args.role:
    tun.addr = "10.1.0.2"
    tun.dstaddr = "10.1.0.1"
    UDP_PORT_BASE = config["CLIENT_UDP_BASE"]
else:
    tun.addr = "10.1.0.1"
    tun.dstaddr = "10.1.0.2"
    UDP_PORT_BASE = config["SERVER_UDP_BASE"]

tun.netmask = "255.255.255.0"
tun.mtu = MTU
tun.up()

# TODO drop root

reads = [tun] # for `select` function
peers = []
for i in xrange(0, config["TUNNELS"]):
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    newSocket.bind(("127.0.0.1", UDP_PORT_BASE + i))
    reads.append(newSocket)
    peers.append(False)

while True:
    readables = select(reads, [], [])[0]
    for each in readables:
        if each == tun:
            buf = each.read(each.mtu)
            # write to socket who have got a peer
            possible = [x for x in xrange(0, len(peers)) if peers[x] != False]
            if len(possible) == 0:
                continue # drop the packet
            i = possible[random.randrange(0, len(possible))]
            workerSocket = reads[i + 1]
            # encrypt and sign buf
            workerSocket.sendto(encrypt(buf), peers[i])
            debug("%s --> [%d]: %s" % (tun.name, i, buf.encode('hex')[:30]))
        else:
            i = reads.index(each) - 1
            buf, sender = each.recvfrom(65536)
#            buf = buf.rstrip()
            if buf.strip() == UDPCONNECTOR_WORD:
                # connection word received, answer
                peers[i] = sender
                each.sendto(UDPCONNECTOR_WORD, sender)
                log("[%d] <==> %s:%d" % (i, sender[0], sender[1]))
            else:
                if peers[i] != sender:
                    continue
                buf = decrypt(buf)
                if buf == False: # if decryption failed
                    print "[%d] --> %s: Bad packet." % (i, tun.name)
                    continue
                tun.write(buf)
                debug("[%d] --> %s: %s" % (i, tun.name, buf.encode('hex')[:30]))
