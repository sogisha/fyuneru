#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from select import select
import signal

from pytun import TunTapDevice

from fyuneru.crypto import randint
from fyuneru.debug import showPacket, colorify
from fyuneru.droproot import dropRoot
from fyuneru.protocol import DataPacket, DataPacketException
from fyuneru.intsck import InternalSocketServer

##############################################################################

parser = argparse.ArgumentParser()
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
    "SOCKET_NAME",
    type=str,
    nargs="+"
)

args = parser.parse_args()


MTU = 1500 
UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."
UNIX_SOCKET_NAMES = args.SOCKET_NAME

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

# ---------- drop root privileges

uidname, gidname = args.uidname, args.gidname
dropRoot(uidname, gidname)

# ---------- open UDP sockets

reads = [tun] # for `select` function
for socketName in UNIX_SOCKET_NAMES:
    newSocket = InternalSocketServer(socketName, args.key)
    reads.append(newSocket)

log("UDP: opening unix socket %s" % ", ".join(UNIX_SOCKET_NAMES))

##############################################################################

def doExit(signum, frame):
    global reads 
    print "Tunnel: exit now."
    for each in reads:
        each.close()
    exit()
signal.signal(signal.SIGTERM, doExit)

while True:
    try:
        readables = select(reads, [], [])[0]
        for each in readables:
            if each == tun:
                # ---------- forward packets came from tun0
                buf = each.read(65536) # each.read(each.mtu)
                # write to socket who have got a peer
                possible = [x for x in xrange(1, len(reads)) if reads[x].peer]
                if len(possible) == 0:
                    continue # drop the packet
                i = possible[randint(0, len(possible) - 1)]
                workerSocket = reads[i]
                # pack buf with timestamp
                packet = DataPacket()
                packet.data = buf
                # encrypt and sign buf
                workerSocket.send(str(packet))
                debug(colorify("[%f] %s --> [%d]\n%s\n" % (\
                    workerSocket.sendtiming,
                    tun.name,
                    i,
                    showPacket(buf)
                ), 'green'))
            else:
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
                debug(colorify("[%f]: --> %s\n%s\n" % (\
                    each.recvtiming,
                    tun.name,
                    showPacket(packet.data)
                ), 'red'))

    except KeyboardInterrupt:
        doExit(None, None)
