"""
XMPP Proxy Process
==================

This proxy utilizes the `xmpppy` library. You have to first install it before
using this. If
    
    sudo pip install xmpppy

doesn't work, you may have to download it from <http://xmpppy.sourceforge.net>
and install manually.

> > > CURRENTLY UNDER DEVELOPEMENT...
"""

import os
import argparse
import signal
from select import select
from logging import info, warning, debug, error, exception

import xmpp

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

MODE_SERVER = 'server'
MODE_CLIENT = 'client'

def start(mode, queuePair, config):
    if MODE_CLIENT == mode:
        peer = config["server"]["jid"]
        jid = config["client"]["jid"]
        password = config["client"]["password"]
    elif MODE_SERVER == mode:
        peer = config["client"]["jid"]
        jid = config["server"]["jid"]
        password = config["server"]["password"]
    else:
        raise Exception("Invalid mode for starting XMPP process.")

    proxy = SocketXMPPProxy(jid, password, peer)
    socket = proxy.xmpp.Connection._sock

    while True:
        try:
            # wait to read some data from xmpp side 
            r = select([socket], [], [], 0.5)[0]
            if len(r) > 0:
                r = r[0]
                proxy.xmpp.Process(1)
                for b in proxy.recvQueue:
                    debug("Received %d bytes, sending to core." % len(b))
                    queuePair.send(b)
                proxy.recvQueue = []
            
            # wait to read some data from core
            try:
                coreSent = queuePair.recv()
                if coreSent:
                    debug(\
                        "Received %d bytes, sending to tunnel." %\
                        len(coreSent)
                    )
                    proxy.send(coreSent)
            except:
                continue

        except KeyboardInterrupt:
            break
        except Exception,e:
            exception(e)
            break
    return
