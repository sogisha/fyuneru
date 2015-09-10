#-*- coding: utf-8 -*-

import argparse
from select import select
import socket

from dgram_stream import DatagramToStream, StreamToDatagram



parser = argparse.ArgumentParser()

parser.add_argument('localPort', metavar='LOCAL_UDP_PORT', type=int)
parser.add_argument('destHost', metavar="DESTINATION_HOSTNAME", type=str)
parser.add_argument('destPort', metavar="DESTINATION_PORT", type=int)

args = parser.parse_args()


localSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


