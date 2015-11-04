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
import sys
import signal
from select import select
import logging
from logging import info, warning, debug, exception, error

import xmpp

from fyuneru.ipc.client import InternalSocketClient
from fyuneru.util.droproot import dropRoot
from fyuneru.util.debug import configLoggingModule
from fyuneru.ipc.url import IPCServerURL
from fyuneru.ipc.tools import InitConfigWaiter

##############################################################################

# ----------- parse arguments

parser = argparse.ArgumentParser()

parser.add_argument("--debug", action="store_true", default=False)
parser.add_argument("IPC_SERVER_URL", type=str)

args = parser.parse_args()

##############################################################################

configLoggingModule(args.debug)

# use command line to initialize IPC client

ipc = InternalSocketClient(args.IPC_SERVER_URL)

queried = InitConfigWaiter(ipc).wait()
if not queried:
    error("Configuration timed out. Exit.")
    ipc.close()
    sys.exit(1)

##############################################################################

debug("Drop privilege to %s:%s" % queried["user"])
dropRoot(*queried["user"])

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

proxyConfig = queried["config"]
if 's' == queried["mode"]:
    proxy = SocketXMPPProxy(\
        proxyConfig["server"]["jid"],
        proxyConfig["server"]["password"],
        proxyConfig["client"]["jid"]
    )
elif 'c' == queried["mode"]:
    proxy = SocketXMPPProxy(\
        proxyConfig["client"]["jid"],
        proxyConfig["client"]["password"],
        proxyConfig["server"]["jid"]
    )
else:
    sys.exit(127)

##############################################################################

def doExit(signum, frame):
    global ipc, proxy
    try:
        ipc.close()
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
    ipc: 'ipc',
}

while True:
    try:
        ipc.heartbeat()
        r, w, _ = select(sockets.keys(), [], [], 1)
        for each in r:
            if sockets[each] == 'proxy':
                proxy.xmpp.Process(1)
                for b in proxy.recvQueue:
                    debug("Received %d bytes, sending to core." % len(b))
                    ipc.send(b)
                proxy.recvQueue = []

            if sockets[each] == 'ipc':
                recv = ipc.receive()
                if not recv: continue
                debug("Received %d bytes, sending to tunnel." % len(recv))
                proxy.send(recv)

        if ipc.broken: doExit(None, None)

    except KeyboardInterrupt:
        doExit(None,None)
