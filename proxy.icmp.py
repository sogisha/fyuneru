
"""
ICMP Proxy Process
==================

This is a very simple proxy that puts our encrypted payloads into ICMP packets.
Since encrypted payloads will be recognized using cryptographical means, we
won't do anything on the payload.

ICMP Proxy is currently only one-way: client->server is okay, reverse is not
supported. You have to use other means of proxies to get replied.
"""
# TODO: modify fyuneru.intsck to make server not try to use this tunnel as
# answer.


import argparse
import signal
from select import select

from fyuneru.ipc.client import InternalSocketClient
from fyuneru.droproot import dropRoot

def log(x):
    print "proxy-icmp-client: %s" % x

# ----------- parse arguments

parser = argparse.ArgumentParser()

# drop privilege to ...
parser.add_argument("--uidname", metavar="UID_NAME", type=str, required=True)
parser.add_argument("--gidname", metavar="GID_NAME", type=str, required=True)

parser.add_argument("--client-send-to", type=str, required=False)

args = parser.parse_args()


##############################################################################

if None == args.client_send_to:
    # run as server mode
    sck = socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_ICMP)
    sck.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    dropRoot(args.uidname, args.gidname)
else:
    # run as client mode
    pass

local = InternalSocketClient(args.socket)

##############################################################################

def doExit(signum, frame):
    global local, proxy
    try:
        local.close()
    except:
        pass
    try:
        proxy.xmpp.disconnect()
    except:
        pass
    print "exit now."
    exit()
signal.signal(signal.SIGTERM, doExit)

##############################################################################

sockets = {
    proxy.xmpp.Connection._sock: 'proxy',
    local: 'local',
}

while True:
    try:
        local.heartbeat()
        r, w, _ = select(sockets.keys(), [], [], 1)
        for each in r:
            if sockets[each] == 'proxy':
                proxy.xmpp.Process(1)
                for b in proxy.recvQueue:
                    log("Received %d bytes, sending to core." % len(b))
                    local.send(b)
                proxy.recvQueue = []

            if sockets[each] == 'local':
                recv = local.receive()
                if not recv: continue
                log("Received %d bytes, sending to tunnel." % len(recv))
                proxy.send(recv)


    except KeyboardInterrupt:
        doExit(None,None)












