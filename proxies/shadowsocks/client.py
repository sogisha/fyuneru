import argparse
from select import select
import subprocess
import socket

import socksproxy

UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

parser = argparse.ArgumentParser()

# following -? arguments are for process `sslocal`
parser.add_argument("-k", type=str) # key
parser.add_argument("-s", type=str) # server addr
parser.add_argument("-p", type=int) # server port
parser.add_argument("-b", type=str) # local addr
parser.add_argument("-l", type=int) # local port
parser.add_argument("-m", type=str, default="aes-256-cfb") # encryption method
# UDP Ports regarding the core process
parser.add_argument("LOCAL", type=int, help="Local UDP Port")
parser.add_argument(
    "REMOTEADDR",
    type=str, 
    help="Remote UDP address."
)
parser.add_argument("REMOTE", type=int, help="Remote UDP Port")

args = parser.parse_args()

##############################################################################

proxySocket = socksproxy.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
localSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

proxySocket.set_proxy(socksproxy.SOCKS5, args.b, args.l)

proxySocket.bind()
localSocket.bind()

localConnected = False
remoteConnected = False

localPeer = ("127.0.0.1", args.LOCAL)
remotePeer = ("127.0.0.1", args.REMOTE)

while True:
    if not localConnected:
        localSocket.send(UDPCONNECTOR_WORD, localPeer)
    if not remoteConnected:
        proxySocket.send(UDPCONNECTOR_WORD, remotePeer)

    readables = select([localSocket, proxySocket], [], [])[0][0]

    for each in readables:
        buf, sender = each.recvfrom(65536)

