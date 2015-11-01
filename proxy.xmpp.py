"""
XMPP Proxy Process
==================

This proxy utilizes the `xmpppy` library. You have to first install it before
using this. If
    
    sudo pip install xmpppy

doesn't work, you may have to download it from <http://xmpppy.sourceforge.net>
and install manually.
"""


import argparse
import signal
from select import select
import logging
from logging import info, warning, debug, exception, error

import xmpp

from fyuneru.net.intsck import InternalSocketClient
from fyuneru.util.droproot import dropRoot
from fyuneru.util.debug import configLoggingModule

# ----------- parse arguments

parser = argparse.ArgumentParser()

# if enable debug mode
parser.add_argument("--debug", action="store_true", default=False)

# drop privilege to ...
parser.add_argument("--uidname", metavar="UID_NAME", type=str, required=True)
parser.add_argument("--gidname", metavar="GID_NAME", type=str, required=True)

parser.add_argument("--peer", type=str, required=True)
parser.add_argument("--jid", type=str, required=True)
parser.add_argument("--password", type=str, required=True)

args = parser.parse_args()


# ---------- config log/debug functions

configLoggingModule(args.debug)

# ---------- drop root

dropRoot(args.uidname, args.gidname)

##############################################################################

class SocketXMPPProxyException(Exception): pass

class SocketXMPPProxy:

    def __init__(self, jid, password, peer):
        self.__jid = xmpp.protocol.JID(jid)
        self.__peer = xmpp.protocol.JID(peer)
        self.__peerJIDStripped = self.__peer.getStripped()

        self.xmpp = xmpp.Client(\
            self.__jid.getDomain(),
            debug=["always", "socket", "nodebuilder", "dispatcher"]
        )
        connection = self.xmpp.connect()
        if not connection:
            raise SocketXMPPProxyException("Unable to connect.")

        authentication = self.xmpp.auth(\
            self.__jid.getNode(),
            password
        )
        if not authentication:
            raise SocketXMPPProxyException("Authentication error.")

        self.__registerHandlers()
        self.__sendPresence()

    def __registerHandlers(self):
        self.xmpp.RegisterHandler('message', self.message)

    def __sendPresence(self):
        presence = xmpp.protocol.Presence(priority=999)
        self.xmpp.send(presence)

    recvQueue = []

    def message(self, con, event):
        msgtype = event.getType()
        fromjid = event.getFrom().getStripped()
        if fromjid != self.__peerJIDStripped: return
        if msgtype in ('chat', 'normal', None):
            body = event.getBody()
            self.recvQueue.append(body.decode('base64'))

    def send(self, buf):
        buf = buf.encode('base64')
        message = xmpp.protocol.Message(to=self.__peer, body=buf, typ='chat')
        self.xmpp.send(message)

##############################################################################

proxy = SocketXMPPProxy(args.jid, args.password, args.peer)
local = InternalSocketClient()

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
                    debug("Received %d bytes, sending to core." % len(b))
                    local.send(b)
                proxy.recvQueue = []

            if sockets[each] == 'local':
                recv = local.receive()
                if not recv: continue
                debug("Received %d bytes, sending to tunnel." % len(recv))
                proxy.send(recv)

        if local.broken: doExit(None, None)

    except KeyboardInterrupt:
        doExit(None,None)












