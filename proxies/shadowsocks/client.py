import argparse
from select import select
import subprocess
import socket
import signal
import time

import socksproxy


def log(x):
    print "proxy-shadowsocks-client: %s" % x

UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

parser = argparse.ArgumentParser()

# use the binary executable specified
parser.add_argument("--bin", type=str, default="/usr/local/bin/ss-tunnel")
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


sslocal = subprocess.Popen([
    args.bin,                                       # shadowsocks-libev
    '-U',                                           # UDP relay only
    '-L', "%s:%d" % (args.REMOTEADDR, args.REMOTE), # destinating UDP addr
    '-k', args.k,                                   # key
    '-s', args.s,                                   # server host
    '-p', str(args.p),                              # server port
    '-b', args.b,                                   # local addr
    '-l', str(args.l),                              # local port
    '-m', args.m,                                   # encryption method
])
print "ss-tunnel -U -L %s:%d -k **** -s %s -p %d -b %s -l %d -m %s" % (\
    args.REMOTEADDR,
    args.REMOTE,
    args.s,
    args.p,
    args.b,
    args.l,
    args.m
)

##############################################################################

#proxySocket = socksproxy.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
proxySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
localSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#proxySocket.set_proxy(socksproxy.SOCKS5, args.b, args.l)

#proxySocket.bind()
#localSocket.bind()

localConnected = False
remoteConnected = False

localPeer = ("127.0.0.1", args.LOCAL)
#remotePeer = (args.REMOTEADDR, args.REMOTE)
remotePeer = (args.b, args.l)

##############################################################################

def doExit(signum, frame):
    global localSocket, proxySocket, sslocal 
    try:
        localSocket.close()
    except:
        pass
    try:
        proxySocket.close()
    except:
        pass
    try:
        sslocal.terminate()
    except:
        pass
    log("exit now.")
    exit()
signal.signal(signal.SIGTERM, doExit)

##############################################################################

while True:
    try:
        if not localConnected:
            localSocket.sendto(UDPCONNECTOR_WORD, localPeer)
            log("Trying to connect local socket at: %s:%d" % localPeer)
            time.sleep(0.5)
        if not remoteConnected:
            proxySocket.sendto(UDPCONNECTOR_WORD, remotePeer)
            log("Trying to connect remote socket at %s:%d" % remotePeer)
            time.sleep(0.5)

        selected = select([localSocket, proxySocket], [], [], 1.0)
        if len(selected) < 1:
            continue
        readables = selected[0]

        for each in readables:
            buf, sender = each.recvfrom(65536)
            if buf.strip() == UDPCONNECTOR_WORD:
                if each == localSocket:
                    localConnected = True
                    log("Local socket connected.")
                if each == proxySocket:
                    remoteConnected = True
                    log("Remote socket connected.")
            else:
                if each == localSocket:
                    proxySocket.write(buf)
                if each == proxySocket:
                    localSocket.write(buf)
    except KeyboardInterrupt:
        doExit(None, None)
