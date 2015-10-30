# -*- coding: utf-8 -*-

"""
Internal Fyuneru Socket for Proxy Processes

A fyuneru socket basing on UDP socket is defined. It is always a listening UDP
socket on a port in local addr, which does automatic handshake with given
internal magic word, and provides additionally abilities like encryption
underlays, traffic statistics, etc.
"""

import os
import sys
import hashlib
from logging import debug, info, warning, error
from time import time
from struct import pack, unpack
from socket import socket, AF_UNIX, SOCK_DGRAM
from ..util.crypto import Crypto


UDPCONNECTOR_WORD = \
    "Across the Great Wall, we can reach every corner in the world."

##############################################################################

def getUNIXSocketPathByName(socketName, role):
    socketid = hashlib.sha1(role + "|" + socketName).hexdigest()
    socketFile = '.fyuneru-intsck-%s' % socketid
    return os.path.join('/', 'tmp', socketFile) 
    

class InternalSocketServer:

    __sockpath = None
    __sock = None

    peer = None

    sendtiming = 0
    recvtiming = 0

    def __init__(self, name, key):
        self.__crypto = Crypto(key)
        self.__sock = socket(AF_UNIX, SOCK_DGRAM)
        self.__sockpath = getUNIXSocketPathByName(name, "server")
        if os.path.exists(self.__sockpath): os.remove(self.__sockpath)
        self.__sock.bind(self.__sockpath)

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    def close(self):
        # close socket
        debug("Internal socket shutting down...")
        try:
            self.__sock.close()
        except Exception,e:
            error("Error closing socket: %s" % e)
        # remove socket file
        try:
            os.remove(self.__sockpath)
        except Exception,e:
            error("Error removing UNIX socket: %s" % e)

    def receive(self):
        buf, sender = self.__sock.recvfrom(65536)

        if type(sender) != str:
            # We communicate on UNIX sockets, if sender doesn't make its own
            # statement(by using bind) of its socket address, we cannot reply.
            # Therefore we'll discard such packets.
            return None

        if buf.strip() == UDPCONNECTOR_WORD:
            # connection word received, answer
            self.peer = sender
            self.__sock.sendto(UDPCONNECTOR_WORD, sender)
            return None

        if self.peer != sender:
            # Sender has not made a handshake before
            return None

        decryption = self.__crypto.decrypt(buf)
        if not decryption: return None

        if len(decryption) < 8: return None
        header = decryption[:8]
        timestamp = unpack('<d', header)[0]
        buf = decryption[8:]

        self.recvtiming = max(self.recvtiming, timestamp)
        return buf 

    def send(self, buf):
        if None == self.peer:
            return
        self.sendtiming = time()
        header = pack('<d', self.sendtiming)
        encryption = self.__crypto.encrypt(header + buf)
        try:
            # reply using last recorded peer
            self.__sock.sendto(encryption, self.peer)
        except Exception,e:
            error(e) # for debug
            self.peer = None # this peer may not work


class InternalSocketClient:

    __sockpath = None
    __sock = None
    __peer = None
    
    connected = False
    __lastbeat = 0

    def __init__(self, name):
        self.__name = name
        self.__sock = socket(AF_UNIX, SOCK_DGRAM)
        self.__sockpath = getUNIXSocketPathByName(name, "client")
        self.__peer = getUNIXSocketPathByName(name, "server")
        if os.path.exists(self.__sockpath): os.remove(self.__sockpath)
        self.__sock.bind(self.__sockpath)

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    def close(self):
        debug("Internal socket shutting down...")
        try:
            self.__sock.close()
        except Exception,e:
            error("Error closing socket: %s" % e)
        try:
            os.remove(self.__sockpath)
        except Exception,e:
            error("Error removing UNIX socket: %s" % e)

    def heartbeat(self):
        if not os.path.exists(self.__peer):
            self.connected = False
            return
        if not self.connected or time() - self.__lastbeat > 5:
            try:
                self.__lastbeat = time()
                self.__sock.sendto(UDPCONNECTOR_WORD, self.__peer)
            except Exception,e:
                self.connected = False
                print e

    def receive(self):
        buf, sender = self.__sock.recvfrom(65536)
        if sender != self.__peer: return None
        if buf.strip() == UDPCONNECTOR_WORD:
            # connection word received, answer
            debug("CONNECTION: %s(IPCCli)" % self.__name)
            self.connected = True
            return None
        return buf 

    def send(self, buf):
        if not self.connected: return
        try:
            # reply using last recorded peer
            self.__sock.sendto(buf, self.__peer)
        except Exception,e:
            print e # for debug
            self.connected = False # this peer may not work
