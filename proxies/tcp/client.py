#-*- coding: utf-8 -*-

import argparse
from select import select
import socket
import sys
import time

from dgram_stream import DatagramToStream, StreamToDatagram

UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."


parser = argparse.ArgumentParser()

parser.add_argument('localPort', metavar='LOCAL_UDP_PORT', type=int)
parser.add_argument('destHost', metavar="DESTINATION_HOSTNAME", type=str)
parser.add_argument('destPort', metavar="DESTINATION_PORT", type=int)

args = parser.parse_args()


localSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sendStream = DatagramToStream()
recvDatagram = StreamToDatagram()

while True:
    print "Sending handshake words to local UDP port %d..." % args.localPort
    localSocket.sendto(UDPCONNECTOR_WORD, ("127.0.0.1", args.localPort))
    readable = select([localSocket], [], [])[0][0]
    data, addr = readable.recvfrom(65536)
    if data.strip() == UDPCONNECTOR_WORD:
        print "Connected to %s:%d" % addr
        break
    time.sleep(0.5)


##############################################################################

def doLoop():
    global localSocket, remoteSocket
    reader = select([localSocket, remoteSocket], [], [])[0]
    for each in reader:
        if each == localSocket:
            pass

        if each == remoteSocket:
            pass

try:
    while True:
        doLoop()
except Exception,e:
    print e
    sys.exit(0)
